"""
Skill Matching — Report Assembly.

Merges every pipeline stage's ALREADY-COMPUTED output (matches, score,
confidence, gaps, recommendation, explanation) into one internal
MatchReport — the last internal representation before service.py / api.py
(Milestone 12) map it onto the public SkillMatchResponse contract.

This file never runs the pipeline itself and never calls AI directly —
per the architecture, sequencing every stage (adapters -> normalization
-> matching -> scoring -> confidence -> gap_analysis -> reasoning ->
here) is service.py's job (Milestone 12). This file only assembles what
other stages already produced, which is what keeps it trivially testable
and keeps the orchestration decision (sync vs. async, error handling
policy) in exactly one place rather than duplicated here.

`match_confidences` is parallel to `matches` (same order, same length) —
computed once by service.py via confidence.py's requirement_confidence,
using the single `as_of` resolved for this request. api.py needs a
per-match confidence value to build its response and must never recompute
one itself with a possibly-different `as_of`, which is exactly the
determinism hazard this field exists to avoid.

Innovation-layer output (Milestones 10-11: interview questions,
candidate insights, confidence meter, ATS alignment) is computed by
service.py (Milestone 12) and passed in here as a plain dict — this file
still doesn't compute any of it, only carries it through, exactly as
documented when the `insights` field was first added. What-if Simulator
is exposed as its own endpoint with its own response shape (see
schemas.py's WhatIfResponseOut) rather than folded in here, since it
needs different request input, not just different output.
"""

from typing import Any, Optional

from pydantic import BaseModel

from .gap_analysis import Gap
from .matching import SkillMatch
from .reasoning import ExplanationResult
from .recommendation import Recommendation
from .scoring import ScoreResult


class MatchReport(BaseModel):
    """The complete internal result of matching one candidate against one job."""

    candidate_id: str
    job_id: str
    matches: list[SkillMatch]
    match_confidences: list[float]  # parallel to `matches`, same order -- see module docstring
    score: ScoreResult
    overall_confidence: float
    gaps: list[Gap]
    recommendation: Recommendation
    explanation: str
    explanation_source: str  # "ai" | "template"
    insights: Optional[dict[str, Any]] = None  # populated by Milestones 10-11


def assemble_match_report(
    candidate_id: str,
    job_id: str,
    matches: list[SkillMatch],
    match_confidences: list[float],
    score: ScoreResult,
    confidence: float,
    gaps: list[Gap],
    recommendation: Recommendation,
    explanation: ExplanationResult,
    insights: Optional[dict[str, Any]] = None,
) -> MatchReport:
    """Merge already-computed pipeline output into one MatchReport."""
    return MatchReport(
        candidate_id=candidate_id,
        job_id=job_id,
        matches=matches,
        match_confidences=match_confidences,
        score=score,
        overall_confidence=confidence,
        gaps=gaps,
        recommendation=recommendation,
        explanation=explanation.text,
        explanation_source=explanation.source,
        insights=insights,
    )
