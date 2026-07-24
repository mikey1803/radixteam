"""
Skill Matching — Recommendation Engine.

Deterministic tiering (algorithm design §7): synthesizes overall score
(scoring.py), overall confidence (confidence.py), and gap composition
(gap_analysis.py) into one of five recommendation tiers — never AI output.
This is the pipeline's final synthesis step, which is why it depends on
every other deterministic stage rather than the reverse.

The rule this milestone exists to enforce, repeated throughout every
design doc: confidence must GATE the tier, not just modulate it. A high
raw score built on a sparse, low-confidence profile must never read as
Strong Match — that would be presenting false precision, exactly the
"score inflation with no calibration" failure mode flagged from the very
first engineering analysis. A tier is always paired with an explicit
confidence_label so a "Good Match" backed by shaky evidence is
distinguishable at a glance from one backed by strong evidence, per the
algorithm design's own example ("Good Match — Moderate Confidence").

Critical gap count is the primary driver (two rule branches handle it
before anything else is considered); moderate gap count is secondary,
only refining the Good-vs-Potential boundary within the moderate-score
band, per the algorithm design's "primarily critical, secondarily
moderate" framing — it never overrides a critical-gap-driven outcome.

Every threshold here follows the same calibration discipline as every
other constant in this module (see constants.py): a reasoned starting
point, not data validated against real hiring outcomes.
"""

from enum import Enum

from pydantic import BaseModel

from .constants import (
    MEANINGFUL_OVERLAP_SCORE_FLOOR,
    RECOMMENDATION_CONFIDENCE_HIGH,
    RECOMMENDATION_CONFIDENCE_REASONABLE,
    RECOMMENDATION_SCORE_HIGH,
    RECOMMENDATION_SCORE_MODERATE,
    SEVERAL_MODERATE_GAPS_THRESHOLD,
)
from .gap_analysis import Gap, GapSeverity
from .scoring import ScoreResult


class RecommendationTier(str, Enum):
    STRONG_MATCH = "strong_match"
    GOOD_MATCH = "good_match"
    POTENTIAL_MATCH = "potential_match"
    NEEDS_UPSKILLING = "needs_upskilling"
    LOW_MATCH = "low_match"


class ConfidenceLabel(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class Recommendation(BaseModel):
    """The recommendation engine's output for one candidate/job pair."""

    tier: RecommendationTier
    confidence_label: ConfidenceLabel
    overall_score: float
    overall_confidence: float
    critical_gap_count: int
    moderate_gap_count: int


def _confidence_label(confidence: float) -> ConfidenceLabel:
    if confidence >= RECOMMENDATION_CONFIDENCE_HIGH:
        return ConfidenceLabel.HIGH
    if confidence >= RECOMMENDATION_CONFIDENCE_REASONABLE:
        return ConfidenceLabel.MODERATE
    return ConfidenceLabel.LOW


def _determine_tier(
    score: float, confidence: float, critical_gaps: int, moderate_gaps: int
) -> RecommendationTier:
    # Critical gap count is the primary driver -- decided first, and
    # nothing below can override a critical-gap-driven outcome.
    if critical_gaps >= 2:
        return RecommendationTier.LOW_MATCH
    if critical_gaps == 1:
        if score >= MEANINGFUL_OVERLAP_SCORE_FLOOR:
            return RecommendationTier.NEEDS_UPSKILLING
        return RecommendationTier.LOW_MATCH

    # critical_gaps == 0 from here on.
    if score < MEANINGFUL_OVERLAP_SCORE_FLOOR:
        return RecommendationTier.LOW_MATCH

    if score >= RECOMMENDATION_SCORE_HIGH:
        # Confidence gates Strong Match specifically -- a high score alone
        # is not enough; see module docstring.
        if confidence >= RECOMMENDATION_CONFIDENCE_HIGH:
            return RecommendationTier.STRONG_MATCH
        return RecommendationTier.POTENTIAL_MATCH

    if score >= RECOMMENDATION_SCORE_MODERATE:
        # Moderate gap count is the secondary driver, refining this one
        # boundary only.
        if (
            confidence >= RECOMMENDATION_CONFIDENCE_REASONABLE
            and moderate_gaps < SEVERAL_MODERATE_GAPS_THRESHOLD
        ):
            return RecommendationTier.GOOD_MATCH
        return RecommendationTier.POTENTIAL_MATCH

    return RecommendationTier.POTENTIAL_MATCH


def recommend(score_result: ScoreResult, overall_confidence: float, gaps: list[Gap]) -> Recommendation:
    """Synthesize a score, a confidence value, and a gap list into one Recommendation."""
    critical_gap_count = sum(1 for gap in gaps if gap.severity == GapSeverity.CRITICAL)
    moderate_gap_count = sum(1 for gap in gaps if gap.severity == GapSeverity.MODERATE)

    tier = _determine_tier(
        score_result.overall_score, overall_confidence, critical_gap_count, moderate_gap_count
    )

    return Recommendation(
        tier=tier,
        confidence_label=_confidence_label(overall_confidence),
        overall_score=score_result.overall_score,
        overall_confidence=overall_confidence,
        critical_gap_count=critical_gap_count,
        moderate_gap_count=moderate_gap_count,
    )
