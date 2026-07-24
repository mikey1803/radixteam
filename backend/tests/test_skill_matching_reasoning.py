"""
Skill Matching — Milestone 9 Unit Tests (reasoning.py).

Covers explanation generation (grounding, fallback-to-template) and Tier 2
semantic-assist relationship discovery, using simple fake AIProvider test
doubles -- no real network access or SDK required anywhere in this file.
"""

import json
from datetime import date
from pathlib import Path

from app.core.ai_provider import AICallError
from modules.skill_matching.adapters import adapt_candidate, adapt_job
from modules.skill_matching.confidence import overall_confidence
from modules.skill_matching.gap_analysis import Gap, GapSeverity, analyze_gaps
from modules.skill_matching.matching import MatchType, SkillMatch, match_job
from modules.skill_matching.models import JobSkillRequirement, RequirementLevel, SkillCategory
from modules.skill_matching.normalization import normalize_candidate, normalize_job
from modules.skill_matching.reasoning import (
    AIExplanationResponse,
    ExplanationPoint,
    SemanticRelationshipResponse,
    discover_relationship,
    generate_explanation,
)
from modules.skill_matching.recommendation import recommend
from modules.skill_matching.relationships import RelationshipType
from modules.skill_matching.scoring import ScoreResult, score_match

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"
AS_OF = date(2024, 12, 1)


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class _FakeProvider:
    """A minimal AIProvider test double -- structurally matches the Protocol, no inheritance needed."""

    def __init__(self, response=None, raises: Exception | None = None):
        self._response = response
        self._raises = raises
        self.calls = 0

    def complete_structured(self, system_prompt, user_prompt, response_model, *, temperature=0.2, timeout_seconds=10.0):
        self.calls += 1
        if self._raises is not None:
            raise self._raises
        return self._response


def _score(overall: float) -> ScoreResult:
    return ScoreResult(overall_score=overall)


def _gap(raw_text: str, severity: GapSeverity) -> Gap:
    requirement = JobSkillRequirement(
        raw_text=raw_text, canonical_skill_id=raw_text.lower(),
        level=RequirementLevel.REQUIRED, category=SkillCategory.CORE_TECHNICAL,
    )
    return Gap(requirement=requirement, match_type=MatchType.NONE, severity=severity, mitigating_confidence=0.0)


def _exact_match(raw_text: str) -> SkillMatch:
    requirement = JobSkillRequirement(raw_text=raw_text, canonical_skill_id=raw_text.lower())
    return SkillMatch(requirement=requirement, match_type=MatchType.EXACT)


# ─── generate_explanation: fallback behavior ──────────────────────────────

class TestGenerateExplanationFallback:
    def test_no_provider_uses_template(self):
        score = _score(0.8)
        gaps = [_gap("Docker", GapSeverity.CRITICAL)]
        rec = recommend(score, 0.8, gaps)

        result = generate_explanation(None, [], score, gaps, rec, AS_OF)
        assert result.source == "template"
        assert "Docker" in result.text

    def test_failing_provider_falls_back_to_template(self):
        score = _score(0.8)
        rec = recommend(score, 0.8, [])
        provider = _FakeProvider(raises=AICallError("network down"))

        result = generate_explanation(provider, [], score, [], rec, AS_OF)
        assert result.source == "template"
        assert result.text  # never empty

    def test_template_is_never_empty_even_with_no_matches_or_gaps(self):
        score = _score(0.0)
        rec = recommend(score, 0.0, [])
        result = generate_explanation(None, [], score, [], rec, AS_OF)
        assert result.text.strip() != ""


# ─── generate_explanation: grounding check ────────────────────────────────

class TestGenerateExplanationGrounding:
    def test_valid_grounded_response_is_used_as_is(self):
        matches = [_exact_match("Python")]
        score = _score(0.9)
        rec = recommend(score, 0.9, [])

        ai_response = AIExplanationResponse(
            overall_summary="This candidate shows strong alignment with the role.",
            points=[
                ExplanationPoint(statement="Python is directly matched.", cites_skill="Python", confidence_hedge="high")
            ],
        )
        provider = _FakeProvider(response=ai_response)

        result = generate_explanation(provider, matches, score, [], rec, AS_OF)
        assert result.source == "ai"
        assert "Python is directly matched" in result.text
        assert provider.calls == 1

    def test_ungrounded_points_are_stripped_but_response_still_used(self):
        matches = [_exact_match("Python")]
        score = _score(0.9)
        rec = recommend(score, 0.9, [])

        ai_response = AIExplanationResponse(
            overall_summary="Generic framing sentence.",
            points=[
                ExplanationPoint(statement="Python is directly matched.", cites_skill="Python"),
                # "Photoshop" was never in the facts -- fabricated, must be dropped
                ExplanationPoint(statement="Candidate also knows Photoshop.", cites_skill="Photoshop"),
            ],
        )
        provider = _FakeProvider(response=ai_response)

        result = generate_explanation(provider, matches, score, [], rec, AS_OF)
        assert result.source == "ai"
        assert "Python is directly matched" in result.text
        assert "Photoshop" not in result.text

    def test_all_points_ungrounded_falls_back_to_template(self):
        matches = [_exact_match("Python")]
        score = _score(0.9)
        gaps = [_gap("SQL", GapSeverity.CRITICAL)]
        rec = recommend(score, 0.9, gaps)

        ai_response = AIExplanationResponse(
            overall_summary="Generic framing sentence.",
            points=[
                ExplanationPoint(statement="Candidate knows Photoshop.", cites_skill="Photoshop"),
                ExplanationPoint(statement="Candidate knows Figma.", cites_skill="Figma"),
            ],
        )
        provider = _FakeProvider(response=ai_response)

        result = generate_explanation(provider, matches, score, gaps, rec, AS_OF)
        assert result.source == "template"
        assert "SQL" in result.text

    def test_points_with_no_cited_skill_are_always_kept(self):
        score = _score(0.5)
        rec = recommend(score, 0.5, [])

        ai_response = AIExplanationResponse(
            overall_summary="Overall framing.",
            points=[ExplanationPoint(statement="A general remark not tied to one skill.", cites_skill=None)],
        )
        provider = _FakeProvider(response=ai_response)

        result = generate_explanation(provider, [], score, [], rec, AS_OF)
        assert result.source == "ai"
        assert "A general remark not tied to one skill." in result.text


# ─── discover_relationship (Tier 2 semantic assist) ───────────────────────

class TestDiscoverRelationship:
    def test_no_provider_returns_none(self):
        result = discover_relationship(
            None, "Vue", SkillCategory.FRAMEWORK, "React", SkillCategory.FRAMEWORK
        )
        assert result is None

    def test_failing_provider_returns_none(self):
        provider = _FakeProvider(raises=AICallError("timeout"))
        result = discover_relationship(
            provider, "Vue", SkillCategory.FRAMEWORK, "React", SkillCategory.FRAMEWORK
        )
        assert result is None

    def test_not_related_returns_none(self):
        provider = _FakeProvider(response=SemanticRelationshipResponse(related=False))
        result = discover_relationship(
            provider, "Vue", SkillCategory.FRAMEWORK, "COBOL", SkillCategory.CORE_TECHNICAL
        )
        assert result is None

    def test_valid_transferable_response_returns_type_and_confidence(self):
        provider = _FakeProvider(
            response=SemanticRelationshipResponse(
                related=True, relationship_type="transferable", confidence=0.65
            )
        )
        result = discover_relationship(
            provider, "Vue", SkillCategory.FRAMEWORK, "React", SkillCategory.FRAMEWORK
        )
        assert result == (RelationshipType.TRANSFERABLE, 0.65)

    def test_valid_adjacent_response(self):
        provider = _FakeProvider(
            response=SemanticRelationshipResponse(
                related=True, relationship_type="adjacent", confidence=0.4
            )
        )
        result = discover_relationship(
            provider, "Vue", SkillCategory.FRAMEWORK, "Svelte", SkillCategory.FRAMEWORK
        )
        assert result == (RelationshipType.ADJACENT, 0.4)

    def test_implausible_category_pair_is_rejected_even_if_ai_claims_related(self):
        # Tier 3 cross-check: soft skill <-> core technical is not a
        # plausible transferable-skill pair, regardless of what the AI says.
        provider = _FakeProvider(
            response=SemanticRelationshipResponse(
                related=True, relationship_type="transferable", confidence=0.9
            )
        )
        result = discover_relationship(
            provider, "Leadership", SkillCategory.SOFT_SKILL, "Python", SkillCategory.CORE_TECHNICAL
        )
        assert result is None

    def test_confidence_is_clamped_to_0_1(self):
        provider = _FakeProvider(
            response=SemanticRelationshipResponse(
                related=True, relationship_type="transferable", confidence=1.7
            )
        )
        result = discover_relationship(
            provider, "Vue", SkillCategory.FRAMEWORK, "React", SkillCategory.FRAMEWORK
        )
        assert result[1] == 1.0


# ─── Full pipeline integration (Milestones 1, 3-9 together) ──────────────

class TestFullPipelineExplanation:
    def test_strong_candidate_explanation_with_ai_provider(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)
        score = score_match(matches, AS_OF)
        confidence = overall_confidence(matches, candidate, AS_OF)
        gaps = analyze_gaps(matches, AS_OF)
        rec = recommend(score, confidence, gaps)

        ai_response = AIExplanationResponse(
            overall_summary="This candidate covers every required skill directly.",
            points=[
                ExplanationPoint(statement="Python is directly matched.", cites_skill="Python", confidence_hedge="high"),
                ExplanationPoint(
                    statement="TensorFlow is covered through related PyTorch experience.",
                    cites_skill="TensorFlow", confidence_hedge="moderate",
                ),
            ],
        )
        provider = _FakeProvider(response=ai_response)

        result = generate_explanation(provider, matches, score, gaps, rec, AS_OF)
        assert result.source == "ai"
        assert "Python is directly matched" in result.text
        assert "TensorFlow" in result.text

    def test_strong_candidate_explanation_without_provider_still_produces_real_text(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)
        score = score_match(matches, AS_OF)
        confidence = overall_confidence(matches, candidate, AS_OF)
        gaps = analyze_gaps(matches, AS_OF)
        rec = recommend(score, confidence, gaps)

        result = generate_explanation(None, matches, score, gaps, rec, AS_OF)
        assert result.source == "template"
        assert "Python" in result.text
        assert "TensorFlow" in result.text  # the one gap in this fixture
