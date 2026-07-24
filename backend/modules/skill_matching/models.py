"""
Skill Matching — Internal Domain Models.

Internal representations used between pipeline stages (normalization,
matching, scoring, gap analysis, reasoning). These are decoupled from both
the upstream modules' payload shapes and this module's own public API
contract (schemas.py) — upstream schema drift and public-contract changes
should never require changing these types.

Scope note: this file only models pipeline *input* (candidate, job, trust
signal). Output-side types (match results, scores, gaps, recommendations)
are introduced by the milestones that compute them, not defined ahead of
schedule here.
"""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ─── Enums ───────────────────────────────────────────────────────────────

class SkillCategory(str, Enum):
    """Primary category a canonical skill is tagged with (assigned during normalization)."""

    CORE_TECHNICAL = "core_technical"
    FRAMEWORK = "framework"
    TOOL_PLATFORM = "tool_platform"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    SOFT_SKILL = "soft_skill"
    CERTIFICATION_COMPLIANCE = "certification_compliance"
    UNKNOWN = "unknown"


class EvidenceSourceType(str, Enum):
    """Where a skill mention was found in the candidate's data."""

    EXPERIENCE = "experience"
    PROJECT = "project"
    CERTIFICATION = "certification"
    EDUCATION = "education"
    HACKATHON = "hackathon"
    RESUME_TEXT = "resume_text"
    PROFILE_SUMMARY = "profile_summary"


class EvidenceDepth(str, Enum):
    """
    Coarse depth signal for one evidence item.

    Deliberately a 3-tier heuristic rather than fine-grained NLP depth
    understanding, per the algorithm design's documented hackathon-scope
    simplification.
    """

    MENTIONED = "mentioned"  # bare skill-list mention, no supporting context
    DESCRIBED = "described"  # appears within a description/technologies list
    CENTRAL = "central"      # clearly a central/primary skill of the source


class RequirementLevel(str, Enum):
    """Whether a job-side skill is required or preferred."""

    REQUIRED = "required"
    PREFERRED = "preferred"


# ─── Evidence ────────────────────────────────────────────────────────────

class SkillEvidence(BaseModel):
    """One piece of evidence supporting that a candidate has a given skill."""

    source_type: EvidenceSourceType
    source_reference: str = Field(
        description=(
            "Human-readable pointer to where this evidence came from, e.g. "
            "'Backend Engineer at Acme Analytics'."
        )
    )
    depth: EvidenceDepth = EvidenceDepth.MENTIONED
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    verified: Optional[bool] = Field(
        default=None,
        description=(
            "True/False if Talent Check has a verdict on this specific claim; "
            "None if no verification signal is available for it."
        ),
    )


# ─── Candidate-side models ───────────────────────────────────────────────

class CandidateSkill(BaseModel):
    """
    A single skill as understood for one candidate.

    canonical_skill_id and category start unset — normalization (Milestone 3)
    populates them, not the adapters.
    """

    raw_text: str
    canonical_skill_id: Optional[str] = None
    category: Optional[SkillCategory] = None
    evidence: list[SkillEvidence] = Field(default_factory=list)


class Candidate(BaseModel):
    """Internal representation of a candidate, decoupled from Profile Builder's wire schema."""

    candidate_id: str
    name: Optional[str] = None
    skills: list[CandidateSkill] = Field(default_factory=list)
    completeness_score: Optional[float] = Field(
        default=None,
        description=(
            "Passed through from Profile Builder as-is; consumed later as a "
            "confidence ceiling, never recomputed by this module."
        ),
    )
    profile_status: Optional[str] = None


# ─── Job-side models ──────────────────────────────────────────────────────

class JobSkillRequirement(BaseModel):
    """
    A single skill requirement as understood for one job.

    canonical_skill_id and category start unset for the same reason as
    CandidateSkill — normalization populates them.
    """

    raw_text: str
    canonical_skill_id: Optional[str] = None
    category: Optional[SkillCategory] = None
    level: RequirementLevel = RequirementLevel.REQUIRED


class Job(BaseModel):
    """Internal representation of a job's skill requirements."""

    job_id: str
    title: Optional[str] = None
    seniority: Optional[str] = None
    skills: list[JobSkillRequirement] = Field(default_factory=list)


# ─── Talent Check signal ──────────────────────────────────────────────────

class TrustSignal(BaseModel):
    """
    Verification signal from Talent Check.

    Supports either per-skill verification (verified_skill_ids) or a coarse
    overall trust score — real upstream granularity is unverified, so both
    are optional and independent of each other.
    """

    candidate_id: str
    overall_trust_score: Optional[float] = None
    verified_skill_ids: list[str] = Field(default_factory=list)


# ─── Pipeline entry point ─────────────────────────────────────────────────

class MatchContext(BaseModel):
    """
    The complete, adapted input to the matching pipeline.

    This is what adapters.py produces and what normalization.py (Milestone 3)
    onward consumes — the anti-corruption boundary between upstream payload
    shapes and this module's internal pipeline.
    """

    candidate: Candidate
    job: Job
    trust_signal: Optional[TrustSignal] = None
