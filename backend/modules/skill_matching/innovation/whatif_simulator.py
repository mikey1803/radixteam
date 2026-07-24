"""
Skill Matching — What-if Simulator.

Answers a candidate's most concrete, actionable question: "how much
would learning X actually change my match?" Reuses the entire
deterministic pipeline already built in Milestones 3-8 (normalization,
matching, scoring, confidence, gap analysis, recommendation) against a
hypothetical candidate with one additional skill — no new AI, no new
scoring logic, just the same trusted engine run twice and diffed. This
is exactly the kind of feature the intelligence design prioritizes: high
value, reuses what's already proven, cheap to build and to trust.

The hypothetical skill is added with the most conservative possible
evidence (a bare, unverified mention) by default — a skill a candidate
doesn't have yet has no proven depth, and simulating otherwise would
overstate the projected improvement. Callers may pass a stronger
hypothetical_depth to model a more concrete plan (e.g. "if I complete a
production project using X").
"""

from datetime import date

from pydantic import BaseModel

from ..confidence import overall_confidence
from ..gap_analysis import analyze_gaps
from ..matching import match_job
from ..models import (
    Candidate,
    CandidateSkill,
    EvidenceDepth,
    EvidenceSourceType,
    Job,
    SkillEvidence,
)
from ..normalization import normalize_candidate
from ..recommendation import recommend
from ..scoring import score_match


class WhatIfSnapshot(BaseModel):
    """The deterministic engine's output at one point — baseline or projected."""

    overall_score: float
    overall_confidence: float
    recommendation_tier: str
    critical_gap_count: int
    moderate_gap_count: int


class WhatIfResult(BaseModel):
    """The comparison between a candidate's current state and a hypothetical addition."""

    hypothetical_skill: str
    hypothetical_skill_recognized: bool
    baseline: WhatIfSnapshot
    projected: WhatIfSnapshot
    score_delta: float
    confidence_delta: float
    critical_gaps_resolved: int


def _snapshot(candidate: Candidate, job: Job, as_of: date) -> WhatIfSnapshot:
    matches = match_job(job, candidate)
    score = score_match(matches, as_of)
    confidence = overall_confidence(matches, candidate, as_of)
    gaps = analyze_gaps(matches, as_of)
    recommendation = recommend(score, confidence, gaps)

    return WhatIfSnapshot(
        overall_score=score.overall_score,
        overall_confidence=confidence,
        recommendation_tier=recommendation.tier.value,
        critical_gap_count=recommendation.critical_gap_count,
        moderate_gap_count=recommendation.moderate_gap_count,
    )


def _add_hypothetical_skill(
    candidate: Candidate, hypothetical_skill: str, hypothetical_depth: EvidenceDepth
) -> Candidate:
    hypothetical_evidence = SkillEvidence(
        source_type=EvidenceSourceType.PROFILE_SUMMARY,
        source_reference="hypothetical -- not yet demonstrated",
        depth=hypothetical_depth,
    )
    new_skill = CandidateSkill(raw_text=hypothetical_skill, evidence=[hypothetical_evidence])
    return candidate.model_copy(update={"skills": [*candidate.skills, new_skill]})


def simulate_added_skill(
    candidate: Candidate,
    job: Job,
    hypothetical_skill: str,
    as_of: date,
    hypothetical_depth: EvidenceDepth = EvidenceDepth.MENTIONED,
) -> WhatIfResult:
    """
    Compare a candidate's current match against the same job if they had
    one additional skill. `candidate` and `job` must already be normalized
    (Milestone 3) — this function normalizes only the newly-added
    hypothetical skill, consistent with every other pipeline stage's scope.

    If the hypothetical skill isn't recognized by the taxonomy, the
    simulation still runs (never raises) but score/confidence deltas will
    be near zero, since matching.py can't use an unmapped skill for
    lookups — `hypothetical_skill_recognized` flags this explicitly so a
    caller never mistakes "we can't simulate this" for "this skill
    genuinely wouldn't help."
    """
    baseline = _snapshot(candidate, job, as_of)

    projected_candidate = normalize_candidate(
        _add_hypothetical_skill(candidate, hypothetical_skill, hypothetical_depth)
    )
    projected = _snapshot(projected_candidate, job, as_of)

    added_skill = projected_candidate.skills[-1]
    recognized = added_skill.canonical_skill_id is not None

    return WhatIfResult(
        hypothetical_skill=hypothetical_skill,
        hypothetical_skill_recognized=recognized,
        baseline=baseline,
        projected=projected,
        score_delta=projected.overall_score - baseline.overall_score,
        confidence_delta=projected.overall_confidence - baseline.overall_confidence,
        critical_gaps_resolved=baseline.critical_gap_count - projected.critical_gap_count,
    )
