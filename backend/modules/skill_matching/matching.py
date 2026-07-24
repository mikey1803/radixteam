"""
Skill Matching — Matching Engine (deterministic).

Classifies every job-side requirement against a candidate's normalized
skill set, per algorithm design §3. Exact and alias matches are already
unified into canonical-ID equality by normalization.py (Milestone 3) — by
the time this file runs, there is no separate "alias match" branch, only
canonical-ID equality. Requires both `job` and `candidate` to already be
normalized (canonical_skill_id populated, or explicitly None for unmapped
skills) before this stage runs.

Candidate skills are grouped by canonical_skill_id once per job so that
every raw mention of the same skill (e.g. duplicate entries from the
candidate's data) is preserved as corroborating evidence for Milestone 5,
rather than only the first one found — and so lookups are O(1) per
requirement instead of a nested scan.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .models import Candidate, CandidateSkill, Job, JobSkillRequirement
from .relationships import RelationshipType, get_relationship


class MatchType(str, Enum):
    """
    How (or whether) a job requirement resolved against a candidate.

    EXACT covers both true exact matches and alias matches — normalization
    already collapsed that distinction into canonical-ID equality, so it
    doesn't reappear here as a separate case.
    """

    EXACT = "exact"
    TRANSFERABLE = "transferable"
    ADJACENT = "adjacent"
    NONE = "none"


class SkillMatch(BaseModel):
    """The outcome of matching one job requirement against a candidate."""

    requirement: JobSkillRequirement
    match_type: MatchType
    matched_candidate_skills: list[CandidateSkill] = Field(default_factory=list)
    relationship_confidence: Optional[float] = Field(
        default=None,
        description="Base transferability/adjacency prior from the relationship graph; "
        "unset for EXACT and NONE.",
    )


def _group_candidate_skills_by_canonical(candidate: Candidate) -> dict[str, list[CandidateSkill]]:
    """
    Group a candidate's skills by canonical_skill_id.

    Skills that failed to resolve during normalization (canonical_skill_id
    is None) are excluded — they can't participate in canonical-ID lookups,
    though they still exist on the candidate for display elsewhere.
    """
    grouped: dict[str, list[CandidateSkill]] = {}
    for skill in candidate.skills:
        if skill.canonical_skill_id is None:
            continue
        grouped.setdefault(skill.canonical_skill_id, []).append(skill)
    return grouped


def _relationship_rank(match_type: MatchType, confidence: float) -> tuple[int, float]:
    """Prefer TRANSFERABLE over ADJACENT, then higher relationship confidence."""
    type_rank = 1 if match_type == MatchType.TRANSFERABLE else 0
    return (type_rank, confidence)


def match_requirement(
    requirement: JobSkillRequirement,
    candidate_by_canonical: dict[str, list[CandidateSkill]],
) -> SkillMatch:
    """
    Classify one job requirement against an already-grouped candidate skill set.

    An unmapped requirement (canonical_skill_id is None — an unknown or
    emerging technology per algorithm doc §9) still produces a real
    SkillMatch with match_type=NONE rather than being skipped: dropping it
    silently would understate what the job actually needs.
    """
    if requirement.canonical_skill_id is None:
        return SkillMatch(requirement=requirement, match_type=MatchType.NONE)

    exact = candidate_by_canonical.get(requirement.canonical_skill_id)
    if exact:
        return SkillMatch(
            requirement=requirement, match_type=MatchType.EXACT, matched_candidate_skills=exact
        )

    best: Optional[SkillMatch] = None
    for candidate_canonical_id, skills in candidate_by_canonical.items():
        relationship = get_relationship(requirement.canonical_skill_id, candidate_canonical_id)
        if relationship is None:
            continue

        rel_type, confidence = relationship
        match_type = (
            MatchType.TRANSFERABLE if rel_type == RelationshipType.TRANSFERABLE else MatchType.ADJACENT
        )
        candidate_match = SkillMatch(
            requirement=requirement,
            match_type=match_type,
            matched_candidate_skills=skills,
            relationship_confidence=confidence,
        )
        if best is None or _relationship_rank(match_type, confidence) > _relationship_rank(
            best.match_type, best.relationship_confidence or 0.0
        ):
            best = candidate_match

    return best or SkillMatch(requirement=requirement, match_type=MatchType.NONE)


def match_job(job: Job, candidate: Candidate) -> list[SkillMatch]:
    """Classify every requirement on a (normalized) job against a (normalized) candidate."""
    candidate_by_canonical = _group_candidate_skills_by_canonical(candidate)
    return [match_requirement(requirement, candidate_by_canonical) for requirement in job.skills]
