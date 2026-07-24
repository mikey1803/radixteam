"""
Skill Matching — Evidence Scoring.

Per-evidence-item confidence weighting (algorithm design §5): source type,
depth, recency, and verification status combine into a single [0, 1]
weight for one SkillEvidence. Aggregating multiple items into a per-skill
confidence lives in confidence.py, not here — this file only scores one
item at a time.

`as_of` is a required, explicit parameter rather than a call to
date.today() — the deterministic engine's reproducibility guarantee
depends on every function being a pure function of its actual inputs,
with no hidden wall-clock dependency (algorithm design §5).
"""

from datetime import date

from .constants import (
    DEPTH_MULTIPLIER,
    RECENCY_AGING_WEIGHT,
    RECENCY_AGING_YEARS,
    RECENCY_CURRENT_WEIGHT,
    RECENCY_CURRENT_YEARS,
    RECENCY_NO_DATE_WEIGHT,
    RECENCY_OLD_WEIGHT,
    RECENCY_RECENT_WEIGHT,
    RECENCY_RECENT_YEARS,
    SOURCE_TYPE_WEIGHT,
    UNVERIFIED_PENALTY,
    VERIFIED_BOOST,
)
from .models import SkillEvidence

_DAYS_PER_YEAR = 365.25


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def recency_modifier(evidence: SkillEvidence, as_of: date) -> float:
    """
    Soft recency decay based on the evidence's most recent relevant date.

    Uses end_date if present (a finished experience/project/certification),
    otherwise start_date (still-ongoing evidence, e.g. no end_date given).
    """
    reference_date = evidence.end_date or evidence.start_date
    if reference_date is None:
        return RECENCY_NO_DATE_WEIGHT

    years_ago = (as_of - reference_date).days / _DAYS_PER_YEAR
    if years_ago <= RECENCY_CURRENT_YEARS:
        return RECENCY_CURRENT_WEIGHT
    if years_ago <= RECENCY_RECENT_YEARS:
        return RECENCY_RECENT_WEIGHT
    if years_ago <= RECENCY_AGING_YEARS:
        return RECENCY_AGING_WEIGHT
    return RECENCY_OLD_WEIGHT


def evidence_item_weight(evidence: SkillEvidence, as_of: date) -> float:
    """
    Score a single evidence item to a [0, 1] weight.

    verified=True boosts the weight (capped at 1.0); verified=False (an
    explicit failed-verification signal from Talent Check) penalizes it;
    verified=None (no verification signal available at all) leaves the
    weight unchanged — absence of verification is never treated as
    evidence of dishonesty.
    """
    weight = (
        SOURCE_TYPE_WEIGHT[evidence.source_type]
        * DEPTH_MULTIPLIER[evidence.depth]
        * recency_modifier(evidence, as_of)
    )

    if evidence.verified is True:
        weight *= VERIFIED_BOOST
    elif evidence.verified is False:
        weight *= UNVERIFIED_PENALTY

    return _clamp01(weight)
