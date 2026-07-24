"""
Skill Matching — Milestone 3 Unit Tests.

Covers normalization.py: text normalization, compact-key alias resolution,
and canonical/category assignment applied to the internal models produced
in Milestone 1.
"""

import json
from pathlib import Path

from modules.skill_matching.adapters import adapt_candidate, adapt_job
from modules.skill_matching.models import RequirementLevel, SkillCategory
from modules.skill_matching.normalization import (
    compact_key,
    normalize_candidate,
    normalize_job,
    normalize_text,
    resolve_canonical_skill,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


# ─── Text normalization primitives ───────────────────────────────────────

class TestNormalizeText:
    def test_lowercases_and_trims(self):
        assert normalize_text("  Python  ") == "python"

    def test_collapses_internal_whitespace(self):
        assert normalize_text("Machine   Learning") == "machine learning"


class TestCompactKey:
    def test_strips_dots_spaces_hyphens_underscores(self):
        assert compact_key("React.js") == compact_key("ReactJS") == compact_key("React JS")

    def test_preserves_plus_and_hash(self):
        assert compact_key("C++") == "c++"
        assert compact_key("C#") == "c#"
        assert compact_key("C++") != compact_key("C#")


# ─── Canonical resolution ─────────────────────────────────────────────────

class TestResolveCanonicalSkill:
    def test_exact_canonical_form(self):
        canonical_id, category = resolve_canonical_skill("Python")
        assert canonical_id == "python"
        assert category == SkillCategory.CORE_TECHNICAL

    def test_case_insensitive(self):
        canonical_id, _ = resolve_canonical_skill("PYTHON")
        assert canonical_id == "python"

    def test_react_alias_variants_all_resolve_identically(self):
        for variant in ["React", "ReactJS", "React.js", "React JS"]:
            canonical_id, category = resolve_canonical_skill(variant)
            assert canonical_id == "react", f"{variant!r} should resolve to react"
            assert category == SkillCategory.FRAMEWORK

    def test_nodejs_alias_variants_all_resolve_identically(self):
        for variant in ["Node.js", "NodeJS", "Node JS", "node"]:
            canonical_id, _ = resolve_canonical_skill(variant)
            assert canonical_id == "nodejs", f"{variant!r} should resolve to nodejs"

    def test_multi_word_alias(self):
        canonical_id, category = resolve_canonical_skill("Machine Learning")
        assert canonical_id == "machine_learning"
        assert category == SkillCategory.DOMAIN_KNOWLEDGE

    def test_unknown_skill_returns_none_and_unknown_category(self):
        canonical_id, category = resolve_canonical_skill("Quantum Basket Weaving")
        assert canonical_id is None
        assert category == SkillCategory.UNKNOWN


# ─── Candidate / Job normalization (integration with Milestone 1) ────────

class TestNormalizeCandidate:
    def test_all_fixture_skills_resolve(self):
        candidate = adapt_candidate(_load("candidate_fixture.json"))
        normalized = normalize_candidate(candidate)

        by_text = {s.raw_text: s for s in normalized.skills}
        assert by_text["Python"].canonical_skill_id == "python"
        assert by_text["FastAPI"].canonical_skill_id == "fastapi"
        assert by_text["Docker"].canonical_skill_id == "docker"
        assert by_text["PyTorch"].canonical_skill_id == "pytorch"
        assert by_text["SQL"].canonical_skill_id == "sql"
        assert by_text["Kubernetes"].canonical_skill_id == "kubernetes"
        assert by_text["Machine Learning"].canonical_skill_id == "machine_learning"

    def test_unmapped_skill_stays_unmapped_not_dropped(self):
        candidate = adapt_candidate({"id": "cand-x", "skills": ["Quantum Basket Weaving"]})
        normalized = normalize_candidate(candidate)

        assert len(normalized.skills) == 1
        assert normalized.skills[0].canonical_skill_id is None
        assert normalized.skills[0].category == SkillCategory.UNKNOWN

    def test_does_not_mutate_original_candidate(self):
        candidate = adapt_candidate(_load("candidate_fixture.json"))
        normalize_candidate(candidate)
        assert all(s.canonical_skill_id is None for s in candidate.skills)

    def test_evidence_is_preserved_through_normalization(self):
        candidate = adapt_candidate(_load("candidate_fixture.json"))
        normalized = normalize_candidate(candidate)

        python_skill = next(s for s in normalized.skills if s.raw_text == "Python")
        assert len(python_skill.evidence) >= 1


class TestNormalizeJob:
    def test_required_and_preferred_skills_resolve(self):
        job = adapt_job(_load("job_fixture.json"))
        normalized = normalize_job(job)

        by_text = {s.raw_text: s for s in normalized.skills}
        assert by_text["Python"].canonical_skill_id == "python"
        assert by_text["FastAPI"].canonical_skill_id == "fastapi"
        assert by_text["Docker"].canonical_skill_id == "docker"
        assert by_text["SQL"].canonical_skill_id == "sql"
        assert by_text["Kubernetes"].canonical_skill_id == "kubernetes"
        assert by_text["TensorFlow"].canonical_skill_id == "tensorflow"

    def test_empty_job_normalizes_to_empty_skills(self):
        job = adapt_job(_load("job_empty_fixture.json"))
        normalized = normalize_job(job)
        assert normalized.skills == []

    def test_does_not_mutate_original_job(self):
        job = adapt_job(_load("job_fixture.json"))
        normalize_job(job)
        assert all(s.canonical_skill_id is None for s in job.skills)


class TestRequirementLevelConflictResolution:
    """
    Milestone 13 hardening: adapt_job never deduped a skill listed under
    both required_skills and preferred_skills -- it produced two separate
    JobSkillRequirement entries, silently contradicting the algorithm
    design's documented "required wins" rule. True dedup can only happen
    after canonical resolution (two different spellings of the same skill
    only provably collapse once normalized), so the fix lives in
    normalize_job, not adapters.py.
    """

    def test_skill_in_both_required_and_preferred_collapses_to_required(self):
        job = adapt_job({"id": "j1", "required_skills": ["Python", "SQL"], "preferred_skills": ["Python", "Docker"]})
        normalized = normalize_job(job)

        python_entries = [s for s in normalized.skills if s.raw_text == "Python"]
        assert len(python_entries) == 1
        assert python_entries[0].level == RequirementLevel.REQUIRED

    def test_non_conflicting_skills_are_unaffected(self):
        job = adapt_job({"id": "j1", "required_skills": ["Python"], "preferred_skills": ["Docker"]})
        normalized = normalize_job(job)
        assert len(normalized.skills) == 2

    def test_conflict_resolution_works_across_alias_spellings(self):
        # "ReactJS" (required) and "React.js" (preferred) are the same
        # canonical skill under different spellings -- must still dedupe.
        job = adapt_job({"id": "j1", "required_skills": ["ReactJS"], "preferred_skills": ["React.js"]})
        normalized = normalize_job(job)

        assert len(normalized.skills) == 1
        assert normalized.skills[0].level == RequirementLevel.REQUIRED

    def test_unmapped_duplicate_skills_also_dedupe_by_raw_text(self):
        job = adapt_job(
            {"id": "j1", "required_skills": ["Some Obscure Tool"], "preferred_skills": ["some obscure tool"]}
        )
        normalized = normalize_job(job)
        assert len(normalized.skills) == 1
        assert normalized.skills[0].level == RequirementLevel.REQUIRED

    def test_preserves_original_relative_order(self):
        job = adapt_job(
            {"id": "j1", "required_skills": ["Python", "SQL"], "preferred_skills": ["Docker", "Python"]}
        )
        normalized = normalize_job(job)
        assert [s.raw_text for s in normalized.skills] == ["Python", "SQL", "Docker"]
