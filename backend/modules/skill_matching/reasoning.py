"""
Skill Matching — AI Reasoning Layer.

Two AI-backed capabilities, per the intelligence design:

1. generate_explanation() — turns an already-computed deterministic
   result into evidence-cited, natural-language prose (algorithm design
   §6, §8). The AI narrates decisions already made; it never makes new
   ones. Falls back to a deterministic template on any failure so the
   `explanation` field is never empty, regardless of AI availability.

2. discover_relationship() — Tier 2 semantic-assist discovery
   (intelligence doc §2): for a skill pair NOT in the curated relationship
   graph (relationships.py's Tier 1), asks the AI for a constrained
   classification. Built and tested here as a standalone capability; NOT
   wired into matching.py's synchronous pipeline in this milestone —
   matching.py stays purely deterministic (as every downstream milestone
   already depends on and tests), and deciding how a live request invokes
   this (sync inline, async pre-pass, etc.) is an orchestration decision
   that belongs to service.py (Milestone 12), not something to bolt onto
   the already-complete, already-tested deterministic core now.

Grounding design (how hallucination is actually prevented, mechanically,
not just by asking nicely): the AI's explanation output is structured
into discrete `points`, each optionally citing one specific skill name.
Every citation is checked against the exact set of skill names that
actually appear in the deterministic result; any point citing a skill
outside that set is dropped, not trusted. The free-text `overall_summary`
field is deliberately constrained by prompt instruction to stay generic
(no specific skill names) precisely because free text can't be
mechanically fact-checked the way a structured citation can — this is an
honest, implementable grounding boundary, not a claim that hallucination
in free text is fully solved.
"""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.core.ai_provider import AICallError, AIProvider
from app.shared.prompts import TALENCIA_REASONING_SYSTEM_PROMPT

from .constants import (
    AI_EXPLANATION_TEMPERATURE,
    AI_EXPLANATION_TIMEOUT_SECONDS,
    AI_RELATIONSHIP_TEMPERATURE,
    AI_RELATIONSHIP_TIMEOUT_SECONDS,
)
from .gap_analysis import Gap, GapSeverity
from .matching import MatchType, SkillMatch
from .models import SkillCategory
from .recommendation import Recommendation
from .relationships import RelationshipType
from .scoring import ScoreResult

# ─── Explanation: structured AI output ────────────────────────────────────


class ExplanationPoint(BaseModel):
    """
    One grounded observation. cites_skill must be an exact skill raw_text
    from the facts provided, or None for a point that doesn't reference a
    specific skill (e.g. a general recommendation-tier remark).
    """

    statement: str
    cites_skill: Optional[str] = None
    confidence_hedge: Literal["high", "moderate", "low", "uncertain"] = "moderate"


class AIExplanationResponse(BaseModel):
    """
    The AI's structured explanation output. `overall_summary` must stay
    generic (no specific skill names) — only `points[].cites_skill` is
    mechanically grounding-checked, so every skill-specific claim must go
    through a point, never the summary (see module docstring).
    """

    overall_summary: str
    points: list[ExplanationPoint] = Field(default_factory=list)


class ExplanationFacts(BaseModel):
    """The complete, closed vocabulary the AI is allowed to reference."""

    overall_score: float
    overall_confidence: float
    recommendation_tier: str
    confidence_label: str
    exact_match_skills: list[str]
    transferable_match_skills: list[str]
    critical_gap_skills: list[str]
    moderate_gap_skills: list[str]
    known_skill_names: set[str]


class ExplanationResult(BaseModel):
    """The final explanation text plus which path produced it."""

    text: str
    source: Literal["ai", "template"]


def _build_explanation_facts(
    matches: list[SkillMatch], score: ScoreResult, gaps: list[Gap], recommendation: Recommendation
) -> ExplanationFacts:
    exact = [m.requirement.raw_text for m in matches if m.match_type == MatchType.EXACT]
    transferable = [m.requirement.raw_text for m in matches if m.match_type == MatchType.TRANSFERABLE]
    critical = [g.requirement.raw_text for g in gaps if g.severity == GapSeverity.CRITICAL]
    moderate = [g.requirement.raw_text for g in gaps if g.severity == GapSeverity.MODERATE]

    known = set(exact) | set(transferable) | {g.requirement.raw_text for g in gaps}
    for match in matches:
        known.update(skill.raw_text for skill in match.matched_candidate_skills)

    return ExplanationFacts(
        overall_score=score.overall_score,
        overall_confidence=recommendation.overall_confidence,
        recommendation_tier=recommendation.tier.value,
        confidence_label=recommendation.confidence_label.value,
        exact_match_skills=exact,
        transferable_match_skills=transferable,
        critical_gap_skills=critical,
        moderate_gap_skills=moderate,
        known_skill_names=known,
    )


def _build_explanation_prompt(facts: ExplanationFacts) -> str:
    return "\n".join(
        [
            "Here are the facts of one candidate-to-job skill match, already computed "
            "by a deterministic scoring engine. Do not recompute or second-guess these "
            "numbers -- your job is only to explain them.",
            "",
            f"Overall score: {facts.overall_score:.2f} (0-1 scale)",
            f"Overall confidence: {facts.overall_confidence:.2f} (0-1 scale)",
            f"Recommendation tier: {facts.recommendation_tier}",
            f"Confidence label: {facts.confidence_label}",
            f"Exactly matched skills: {', '.join(facts.exact_match_skills) or 'none'}",
            "Skills covered via related/transferable evidence (candidate doesn't have "
            f"the exact skill, but has a related one): {', '.join(facts.transferable_match_skills) or 'none'}",
            f"Critical gaps (required, no mitigating evidence): {', '.join(facts.critical_gap_skills) or 'none'}",
            f"Moderate gaps (required, some mitigating evidence): {', '.join(facts.moderate_gap_skills) or 'none'}",
            "",
            "Respond with a JSON object with exactly two fields:",
            '- "overall_summary": one or two generic sentences framing the overall '
            "result. Do not name any specific skill in this field.",
            '- "points": a list of objects, each with "statement" (one sentence), '
            '"cites_skill" (the exact skill name from the facts above that this point '
            'is about, or null if it does not reference one specific skill), and '
            '"confidence_hedge" (one of "high", "moderate", "low", "uncertain").',
            "Only reference skills listed above. Do not mention any skill not listed.",
        ]
    )


def _apply_grounding_check(response: AIExplanationResponse, facts: ExplanationFacts) -> Optional[AIExplanationResponse]:
    """
    Drop any point citing a skill outside the known vocabulary. If every
    point was ungrounded (and there was at least one to begin with), the
    whole response is untrustworthy -- return None so the caller falls
    back to the template.
    """
    grounded_points = [
        point
        for point in response.points
        if point.cites_skill is None or point.cites_skill in facts.known_skill_names
    ]

    if response.points and not grounded_points:
        return None

    return AIExplanationResponse(overall_summary=response.overall_summary, points=grounded_points)


def _render_explanation(response: AIExplanationResponse) -> str:
    lines = [response.overall_summary]
    for point in response.points:
        hedge = f" ({point.confidence_hedge} confidence)" if point.confidence_hedge != "moderate" else ""
        lines.append(f"{point.statement}{hedge}")
    return " ".join(lines)


def _template_explanation(facts: ExplanationFacts) -> str:
    """Deterministic, rule-based fallback -- no AI, never empty, never fails."""
    lines = [
        f"Overall match: {facts.recommendation_tier.replace('_', ' ')} "
        f"({facts.confidence_label} confidence), score {facts.overall_score:.0%}."
    ]
    if facts.critical_gap_skills:
        lines.append("Critical gaps: " + ", ".join(facts.critical_gap_skills) + ".")
    if facts.moderate_gap_skills:
        lines.append(
            "Moderate gaps, partially mitigated by related evidence: "
            + ", ".join(facts.moderate_gap_skills)
            + "."
        )
    if facts.exact_match_skills:
        lines.append("Directly matched: " + ", ".join(facts.exact_match_skills) + ".")
    if facts.transferable_match_skills:
        lines.append(
            "Covered via related evidence: " + ", ".join(facts.transferable_match_skills) + "."
        )
    return " ".join(lines)


def generate_explanation(
    provider: Optional[AIProvider],
    matches: list[SkillMatch],
    score: ScoreResult,
    gaps: list[Gap],
    recommendation: Recommendation,
    as_of: date,
) -> ExplanationResult:
    """
    Produce an explanation for one match result. `as_of` is accepted for
    interface consistency with the rest of the deterministic pipeline but
    isn't itself used here -- explanation generation doesn't depend on the
    current date, only on the already-computed facts.
    """
    facts = _build_explanation_facts(matches, score, gaps, recommendation)

    if provider is None:
        return ExplanationResult(text=_template_explanation(facts), source="template")

    try:
        ai_response = provider.complete_structured(
            system_prompt=TALENCIA_REASONING_SYSTEM_PROMPT,
            user_prompt=_build_explanation_prompt(facts),
            response_model=AIExplanationResponse,
            temperature=AI_EXPLANATION_TEMPERATURE,
            timeout_seconds=AI_EXPLANATION_TIMEOUT_SECONDS,
        )
    except AICallError:
        return ExplanationResult(text=_template_explanation(facts), source="template")

    grounded = _apply_grounding_check(ai_response, facts)
    if grounded is None:
        return ExplanationResult(text=_template_explanation(facts), source="template")

    return ExplanationResult(text=_render_explanation(grounded), source="ai")


# ─── Semantic assist: Tier 2 relationship discovery ───────────────────────


class SemanticRelationshipResponse(BaseModel):
    related: bool
    relationship_type: Optional[Literal["transferable", "adjacent"]] = None
    confidence: float = 0.0
    justification: Optional[str] = None


_TECHNICAL_CATEGORIES = frozenset(
    {
        SkillCategory.CORE_TECHNICAL,
        SkillCategory.FRAMEWORK,
        SkillCategory.TOOL_PLATFORM,
        SkillCategory.DOMAIN_KNOWLEDGE,
    }
)


def _categories_plausibly_related(category_a: SkillCategory, category_b: SkillCategory) -> bool:
    """
    Tier 3 cross-check (intelligence doc §2): reject a claimed relationship
    between categories that don't plausibly relate (e.g. a soft skill and
    a framework), regardless of the AI's self-reported confidence. Same
    category is always plausible; otherwise both must be "technical"
    categories.
    """
    if category_a == category_b:
        return True
    return category_a in _TECHNICAL_CATEGORIES and category_b in _TECHNICAL_CATEGORIES


def _build_relationship_prompt(
    skill_a: str, category_a: SkillCategory, skill_b: str, category_b: SkillCategory
) -> str:
    return "\n".join(
        [
            "Are these two skills related in a way relevant to job matching?",
            f"Skill A: {skill_a} (category: {category_a.value})",
            f"Skill B: {skill_b} (category: {category_b.value})",
            "",
            'Respond with a JSON object: {"related": true or false, '
            '"relationship_type": "transferable" or "adjacent" or null, '
            '"confidence": a number from 0 to 1, "justification": a short reason}.',
            '"transferable" means strong conceptual overlap -- experience with one '
            'covers most of what the other tests for. "adjacent" means same '
            "ecosystem/domain but real ramp-up is still expected. If they are not "
            "meaningfully related, set related to false.",
        ]
    )


def discover_relationship(
    provider: Optional[AIProvider],
    skill_a: str,
    category_a: SkillCategory,
    skill_b: str,
    category_b: SkillCategory,
) -> Optional[tuple[RelationshipType, float]]:
    """
    Ask the AI whether two canonical skills not in the curated relationship
    graph are related. Returns None on any failure, missing provider, an
    implausible AI-claimed relationship (Tier 3 cross-check), or a
    not-related verdict -- never raises. Callers already treat "no
    relationship found" as a normal outcome (see matching.py), so a silent
    None here is a safe, honest degradation, not a hidden failure.
    """
    if provider is None:
        return None

    try:
        response = provider.complete_structured(
            system_prompt=TALENCIA_REASONING_SYSTEM_PROMPT,
            user_prompt=_build_relationship_prompt(skill_a, category_a, skill_b, category_b),
            response_model=SemanticRelationshipResponse,
            temperature=AI_RELATIONSHIP_TEMPERATURE,
            timeout_seconds=AI_RELATIONSHIP_TIMEOUT_SECONDS,
        )
    except AICallError:
        return None

    if not response.related or response.relationship_type is None:
        return None

    if not _categories_plausibly_related(category_a, category_b):
        return None

    confidence = max(0.0, min(1.0, response.confidence))
    relationship_type = (
        RelationshipType.TRANSFERABLE
        if response.relationship_type == "transferable"
        else RelationshipType.ADJACENT
    )
    return relationship_type, confidence
