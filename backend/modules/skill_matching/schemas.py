"""
Skill Matching — Public API Contract.

Request/response models exposed via this module's API (wired in
Milestone 12). This is the stable, backward-compatible external contract —
internal pipeline stages (models.py, normalization.py, matching.py, ...)
never use these types directly; only api.py and aggregator.py should.

Response fields below `candidate_id`/`job_id` are intentionally optional
at this stage: the shape is established now so other teams can align
early, and fields are filled in progressively as later milestones land
(score/gaps in Milestones 6-7, recommendation in Milestone 8, explanation
in Milestone 9, innovation-layer output in Milestones 10-11). New fields
must always be additive from here on — this is the schema the brief
requires to stay backward compatible.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0.0"


# ─── Request ───────────────────────────────────────────────────────────

class SkillMatchRequest(BaseModel):
    """
    Input to a skill match request.

    `job` and `candidate` are accepted as raw payloads rather than
    strongly-typed upstream schemas, because JD Analytics' and Resume
    Parser's real output schemas are not yet committed anywhere upstream.
    adapters.py is the sole place that interprets these payloads, so this
    request schema doesn't have to change when those upstream shapes are
    confirmed — only the adapter does.
    """

    job: dict[str, Any] = Field(description="Raw JD Analytics output.")
    candidate: dict[str, Any] = Field(description="Raw Resume Parser / Profile Builder output.")
    talent_check: Optional[dict[str, Any]] = Field(
        default=None, description="Raw Talent Check output, if available."
    )


# ─── Response building blocks (populated by later milestones) ──────────

class SkillEvidenceOut(BaseModel):
    """Public projection of one evidence item behind a matched skill."""

    source_type: str
    source_reference: str
    depth: str
    verified: Optional[bool] = None


class MatchedSkillOut(BaseModel):
    """Public projection of one resolved requirement (Milestone 4/5)."""

    skill: str
    match_type: str
    confidence: float
    evidence: list[SkillEvidenceOut] = Field(default_factory=list)


class GapOut(BaseModel):
    """Public projection of one unresolved requirement (Milestone 7)."""

    skill: str
    severity: str
    reason: Optional[str] = None


class RecommendationOut(BaseModel):
    """Public projection of the deterministic recommendation tier (Milestone 8)."""

    tier: str
    confidence_label: str


# ─── Innovation-layer response building blocks (Milestones 10-11) ──────

class InterviewQuestionOut(BaseModel):
    question: str
    purpose: str
    difficulty: str
    related_skill: str


class MatchInsightsOut(BaseModel):
    """
    Optional, additive innovation-layer content. Every field here is
    computed by reusing already-computed pipeline output (Milestones
    10-11) — nothing here is a new source of truth, only a different
    presentation of what `matched_skills`/`gaps`/`recommendation` above
    already established.
    """

    weakest_matched_skill: Optional[str] = None
    candidate_bonus_skills: list[str] = Field(default_factory=list)
    interview_questions: list[InterviewQuestionOut] = Field(default_factory=list)
    ats_keyword_match_rate: Optional[float] = None


# ─── Response ────────────────────────────────────────────────────────────

class SkillMatchResponse(BaseModel):
    """
    The module's public response contract.

    Every field from `overall_score` onward stays None until the milestone
    that computes it lands — this lets the contract exist and be
    integrated against immediately without a breaking change later.
    """

    schema_version: str = SCHEMA_VERSION
    candidate_id: str
    job_id: str

    overall_score: Optional[float] = None
    overall_confidence: Optional[float] = None

    matched_skills: Optional[list[MatchedSkillOut]] = None
    gaps: Optional[list[GapOut]] = None
    recommendation: Optional[RecommendationOut] = None

    explanation: Optional[str] = None
    explanation_source: Optional[str] = Field(
        default=None, description="'ai' or 'template' — which path produced `explanation`."
    )

    insights: Optional[MatchInsightsOut] = Field(
        default=None,
        description=(
            "Optional innovation-layer output (candidate insights, confidence "
            "meter, interview questions, ATS alignment). Additive only — never "
            "required for the response to be valid. Was a loose dict[str, Any] "
            "placeholder before Milestone 11 defined what actually goes in it; "
            "no external client existed yet, so tightening the type here is a "
            "safe, honest improvement rather than a breaking change."
        ),
    )


# ─── What-if Simulator (separate endpoint — different request shape) ───

class WhatIfRequest(BaseModel):
    """
    Input to a what-if simulation: the same job/candidate payloads as
    SkillMatchRequest, plus the one hypothetical skill to simulate adding.
    A separate request type from SkillMatchRequest because this genuinely
    needs different input, not because the underlying engine differs.
    """

    job: dict[str, Any] = Field(description="Raw JD Analytics output.")
    candidate: dict[str, Any] = Field(description="Raw Resume Parser / Profile Builder output.")
    hypothetical_skill: str = Field(description="The skill to simulate the candidate having.")


class WhatIfResponseOut(BaseModel):
    """The public projection of a WhatIfResult (innovation/whatif_simulator.py)."""

    hypothetical_skill: str
    hypothetical_skill_recognized: bool
    baseline_score: float
    projected_score: float
    score_delta: float
    baseline_confidence: float
    projected_confidence: float
    confidence_delta: float
    critical_gaps_resolved: int
