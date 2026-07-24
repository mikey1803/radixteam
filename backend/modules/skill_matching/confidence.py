"""
Skill Matching — Confidence Engine.

The four-tier confidence calculation from algorithm design §5: Evidence
(evidence.py), Skill, Requirement, and Overall confidence.

Skill Confidence combines multiple evidence items with a diminishing-
returns (noisy-OR) accumulation rather than an average: a second strong
corroborating source should raise confidence meaningfully, a fifth should
barely move it, and confidence should never exceed 1.0 no matter how many
items pile up. This is deliberately NOT a simple average, which would
wrongly dilute one strong source down toward weaker ones.

If evidence for the same skill disagrees on verification status (one
source verified, another explicitly not), that is treated as a detectable
conflict and penalized rather than left to the noisy-OR combination to
optimistically boost. This is the one conflict signal the current
SkillEvidence schema actually supports — broader narrative conflicts
(e.g. contradictory claimed years of experience) aren't representable in
the schema yet and are an explicit, known limitation, not something this
milestone attempts to solve.

Requirement Confidence applies a match-type ceiling on top of Skill
Confidence — even excellent evidence for a transferable match should not
be treated as certain as an exact match. For TRANSFERABLE/ADJACENT
matches specifically, the pair's own relationship_confidence (the
specific prior from the relationship graph — e.g. 0.7 for PyTorch <->
TensorFlow vs. 0.6 for Docker <-> Kubernetes, see relationships.py) is
also factored in, so two different transferable pairs with identical
underlying evidence don't collapse to the same confidence just because
they share a match type. The match-type ceiling is applied as a cap
(min), not a second multiplier: "capped below the exact-match ceiling
regardless of how strong evidence gets" (algorithm design §3) reads most
naturally as an upper bound, not compounded dampening on top of the pair
prior.

Overall Confidence blends a criticality-weighted mean with the weighted
minimum confidence, biased toward the minimum, so one severely
under-evidenced *critical* requirement drags overall confidence down
sharply while several well-evidenced minor requirements cannot fully
compensate for it — the "weakest link" behavior described in the
algorithm design. A true power-mean with a negative exponent would
express this more elegantly but is undefined at exactly zero confidence,
which happens routinely (any unmatched requirement has confidence 0);
this min/mean blend achieves the same behavioral goal and stays
well-defined everywhere. Overall Confidence is finally capped by Profile
Builder's completeness_score, never recomputed — a sparse profile cannot
produce high confidence no matter how internally consistent its few data
points are.
"""

from datetime import date

from .constants import (
    CATEGORY_WEIGHT,
    CONFLICT_PENALTY,
    MATCH_TYPE_CEILING,
    OVERALL_CONFIDENCE_MIN_BIAS,
    REQUIREMENT_LEVEL_WEIGHT,
)
from .evidence import evidence_item_weight
from .matching import MatchType, SkillMatch
from .models import Candidate, CandidateSkill, JobSkillRequirement, SkillCategory, SkillEvidence


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _combine_diminishing_returns(weights: list[float]) -> float:
    """Noisy-OR combination: 1 - product(1 - w_i). Bounded in [0, 1], monotonic."""
    remaining_gap = 1.0
    for weight in weights:
        remaining_gap *= 1.0 - _clamp01(weight)
    return 1.0 - remaining_gap


def _has_verification_conflict(evidence_items: list[SkillEvidence]) -> bool:
    """True if evidence for the same skill disagrees on verification status."""
    verdicts = {e.verified for e in evidence_items if e.verified is not None}
    return True in verdicts and False in verdicts


def skill_confidence(candidate_skills: list[CandidateSkill], as_of: date) -> float:
    """
    Combine every evidence item across one or more CandidateSkill entries
    (multiple entries occur when the same canonical skill was mentioned
    more than once — see matching.py's grouping) into one confidence value.
    """
    evidence_items = [evidence for skill in candidate_skills for evidence in skill.evidence]
    if not evidence_items:
        return 0.0

    weights = [evidence_item_weight(evidence, as_of) for evidence in evidence_items]
    combined = _combine_diminishing_returns(weights)

    if _has_verification_conflict(evidence_items):
        combined *= CONFLICT_PENALTY

    return _clamp01(combined)


def requirement_confidence(match: SkillMatch, as_of: date) -> float:
    """
    Skill Confidence, capped by the match type's ceiling; 0 for an
    unresolved requirement.

    EXACT matches have no relationship prior (they didn't go through the
    relationship graph) and use Skill Confidence directly, capped at 1.0.
    TRANSFERABLE/ADJACENT matches are additionally scaled by the specific
    pair's relationship_confidence before the ceiling is applied as a cap.
    """
    if match.match_type == MatchType.NONE:
        return 0.0

    base = skill_confidence(match.matched_candidate_skills, as_of)
    ceiling = MATCH_TYPE_CEILING[match.match_type]

    if match.match_type == MatchType.EXACT:
        return base * ceiling

    pair_prior = match.relationship_confidence if match.relationship_confidence is not None else 1.0
    return min(ceiling, base * pair_prior)


def _requirement_weight(requirement: JobSkillRequirement) -> float:
    level_weight = REQUIREMENT_LEVEL_WEIGHT[requirement.level]
    category_weight = CATEGORY_WEIGHT[requirement.category or SkillCategory.UNKNOWN]
    return level_weight * category_weight


def overall_confidence(matches: list[SkillMatch], candidate: Candidate, as_of: date) -> float:
    """
    Criticality-weighted, weakest-link-dampened aggregation across every
    requirement's confidence, capped by the candidate's completeness_score.
    """
    if not matches:
        return 0.0

    weighted: list[tuple[float, float]] = [
        (_requirement_weight(match.requirement), requirement_confidence(match, as_of))
        for match in matches
    ]

    total_weight = sum(weight for weight, _ in weighted)
    if total_weight == 0:
        return 0.0

    weighted_mean = sum(weight * confidence for weight, confidence in weighted) / total_weight
    weakest = min(confidence for weight, confidence in weighted if weight > 0)

    raw_overall = (
        OVERALL_CONFIDENCE_MIN_BIAS * weakest + (1 - OVERALL_CONFIDENCE_MIN_BIAS) * weighted_mean
    )

    if candidate.completeness_score is not None:
        raw_overall = min(raw_overall, candidate.completeness_score)

    return _clamp01(raw_overall)
