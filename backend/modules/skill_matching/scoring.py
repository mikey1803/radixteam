"""
Skill Matching — Scoring Engine.

Weighted scoring (algorithm design §4): per-requirement contribution,
required/preferred sub-scores, and the final overall score.

Reuses confidence.py's requirement_confidence as the base per-requirement
signal rather than recomputing match-type/evidence/recency/verification
separately — score and confidence both answer "how well is this
requirement satisfied," just aggregated differently for different
purposes (score: how much does this candidate match overall; confidence:
how much should we trust that number). Recomputing the same signal twice
under two names would be exactly the kind of duplicate implementation the
shared-core rule warns against, just within one module instead of across
modules.

Category weighting (core-technical requirements counting more than
peripheral ones within their required/preferred bucket) reuses the same
CATEGORY_WEIGHT constant confidence.py uses, for the same reason.

Every weight here is a reasoned starting point per the algorithm design's
calibration discipline (see constants.py), not validated against real
outcome data. What IS validated, by this milestone's tests, are the
structural invariants the algorithm design requires: full required
coverage scores higher than partial, verified evidence never scores below
otherwise-identical unverified evidence, and an adjacent match's
contribution stays small relative to an exact match regardless of how
strong its underlying evidence is.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel

from .confidence import requirement_confidence
from .constants import CATEGORY_WEIGHT, REQUIRED_DOMINANCE_WEIGHT, SCORE_CONTRIBUTION_MULTIPLIER
from .matching import SkillMatch
from .models import RequirementLevel, SkillCategory


class ScoreResult(BaseModel):
    """The scoring engine's output for one candidate/job pair."""

    overall_score: float
    required_sub_score: Optional[float] = None
    preferred_sub_score: Optional[float] = None


def _requirement_score_weight(match: SkillMatch) -> float:
    """Within its required/preferred bucket, weight a requirement by category importance."""
    category = match.requirement.category or SkillCategory.UNKNOWN
    return CATEGORY_WEIGHT[category]


def requirement_score_contribution(match: SkillMatch, as_of: date) -> float:
    """
    The score-specific contribution of one requirement: requirement_confidence
    further dampened for adjacent matches (see SCORE_CONTRIBUTION_MULTIPLIER).
    """
    base = requirement_confidence(match, as_of)
    return base * SCORE_CONTRIBUTION_MULTIPLIER[match.match_type]


def _weighted_bucket_score(matches: list[SkillMatch], as_of: date) -> Optional[float]:
    """Weighted average of requirement_score_contribution across one bucket."""
    if not matches:
        return None

    weighted_sum = 0.0
    total_weight = 0.0
    for match in matches:
        weight = _requirement_score_weight(match)
        weighted_sum += weight * requirement_score_contribution(match, as_of)
        total_weight += weight

    if total_weight == 0:
        return None
    return weighted_sum / total_weight


def score_match(matches: list[SkillMatch], as_of: date) -> ScoreResult:
    """
    Score a full set of requirement matches for one job against one candidate.

    A job with only required skills (the common case) yields
    preferred_sub_score=None and overall_score == required_sub_score, and
    vice versa. A job with neither (should already be rejected by
    validators.py before reaching this stage) yields a score of 0 rather
    than raising.
    """
    required = [m for m in matches if m.requirement.level == RequirementLevel.REQUIRED]
    preferred = [m for m in matches if m.requirement.level == RequirementLevel.PREFERRED]

    required_sub_score = _weighted_bucket_score(required, as_of)
    preferred_sub_score = _weighted_bucket_score(preferred, as_of)

    if required_sub_score is not None and preferred_sub_score is not None:
        overall = (
            REQUIRED_DOMINANCE_WEIGHT * required_sub_score
            + (1 - REQUIRED_DOMINANCE_WEIGHT) * preferred_sub_score
        )
    elif required_sub_score is not None:
        overall = required_sub_score
    elif preferred_sub_score is not None:
        overall = preferred_sub_score
    else:
        overall = 0.0

    return ScoreResult(
        overall_score=overall,
        required_sub_score=required_sub_score,
        preferred_sub_score=preferred_sub_score,
    )
