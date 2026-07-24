"""
Skill Matching — Normalization Engine.

Canonical mapping, alias resolution, and category assignment (algorithm
design §2). Every raw skill string on both the candidate and job side runs
through the identical pipeline here — that's what guarantees the same
real-world skill lands on the same canonical_skill_id on both sides, the
precondition for a well-defined exact match in Milestone 4.

Unmapped skills are never silently dropped or guessed at full confidence:
they come out with canonical_skill_id=None and category=UNKNOWN, an
explicit, checkable "unmapped" signal that downstream stages must treat
as insufficient taxonomy confidence, per the documented handling for
unknown and emerging technologies.

normalize_job also resolves the documented required/preferred conflict
rule (algorithm design §9): if a skill is listed under both
required_skills and preferred_skills, adapters.py has no reliable way to
detect that (it only ever sees raw text, and two different spellings of
the same skill only provably collapse to one skill once canonical
resolution has run) — so the dedup has to happen here, after
canonicalization, not in adapters.py. The stricter classification
(required) always wins.
"""

import re

from .models import Candidate, CandidateSkill, Job, JobSkillRequirement, RequirementLevel, SkillCategory
from .taxonomy import TAXONOMY

_WHITESPACE_RE = re.compile(r"\s+")
_COMPACT_STRIP_RE = re.compile(r"[\s.\-_/]+")

# canonical_skill_id -> category, and compact surface form -> canonical_skill_id,
# both derived once from TAXONOMY so the data declaration stays the single
# source of truth.
_CANONICAL_CATEGORY: dict[str, SkillCategory] = {}
_SURFACE_FORM_INDEX: dict[str, str] = {}


def normalize_text(text: str) -> str:
    """Lowercase, trim, and collapse internal whitespace — the 'loose' normal form."""
    return _WHITESPACE_RE.sub(" ", text.strip().lower())


def compact_key(text: str) -> str:
    """
    Strip spacing/punctuation noise on top of normalize_text, tolerant of the
    common surface-form variation seen in real skill text (Node.js / NodeJS /
    Node JS all reduce to the same key). Deliberately leaves '+' and '#'
    untouched so C++ and C# stay distinct from C and from each other.
    """
    return _COMPACT_STRIP_RE.sub("", normalize_text(text))


def _build_index() -> None:
    for canonical_id, (category, surface_forms) in TAXONOMY.items():
        _CANONICAL_CATEGORY[canonical_id] = category
        for form in surface_forms:
            _SURFACE_FORM_INDEX[compact_key(form)] = canonical_id


_build_index()


def resolve_canonical_skill(raw_text: str) -> tuple[str | None, SkillCategory]:
    """
    Resolve one raw skill string to (canonical_skill_id, category).

    Returns (None, SkillCategory.UNKNOWN) for anything not in the curated
    taxonomy — an explicit "unmapped" result, never a guess.
    """
    canonical_id = _SURFACE_FORM_INDEX.get(compact_key(raw_text))
    if canonical_id is None:
        return None, SkillCategory.UNKNOWN
    return canonical_id, _CANONICAL_CATEGORY[canonical_id]


def _normalize_candidate_skill(skill: CandidateSkill) -> CandidateSkill:
    canonical_id, category = resolve_canonical_skill(skill.raw_text)
    return skill.model_copy(update={"canonical_skill_id": canonical_id, "category": category})


def _normalize_job_skill(skill: JobSkillRequirement) -> JobSkillRequirement:
    canonical_id, category = resolve_canonical_skill(skill.raw_text)
    return skill.model_copy(update={"canonical_skill_id": canonical_id, "category": category})


def normalize_candidate(candidate: Candidate) -> Candidate:
    """Return a copy of candidate with every skill's canonical_skill_id/category populated."""
    return candidate.model_copy(
        update={"skills": [_normalize_candidate_skill(s) for s in candidate.skills]}
    )


def _resolve_requirement_level_conflicts(
    skills: list[JobSkillRequirement],
) -> list[JobSkillRequirement]:
    """
    Collapse a skill listed at both REQUIRED and PREFERRED level to a
    single REQUIRED entry. Matched by canonical_skill_id when known, else
    by normalized raw text (so two unmapped duplicate mentions still
    dedupe). Order-preserving: keeps the position of the first occurrence.
    """
    best_by_key: dict[str, JobSkillRequirement] = {}
    order: list[str] = []

    for skill in skills:
        key = skill.canonical_skill_id or normalize_text(skill.raw_text)
        if key not in best_by_key:
            best_by_key[key] = skill
            order.append(key)
        elif skill.level == RequirementLevel.REQUIRED and best_by_key[key].level != RequirementLevel.REQUIRED:
            best_by_key[key] = skill

    return [best_by_key[key] for key in order]


def normalize_job(job: Job) -> Job:
    """
    Return a copy of job with every skill's canonical_skill_id/category
    populated, and any required/preferred duplicate collapsed per
    _resolve_requirement_level_conflicts (module docstring).
    """
    normalized_skills = [_normalize_job_skill(s) for s in job.skills]
    deduped_skills = _resolve_requirement_level_conflicts(normalized_skills)
    return job.model_copy(update={"skills": deduped_skills})
