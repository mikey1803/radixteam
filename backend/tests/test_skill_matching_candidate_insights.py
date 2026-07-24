"""
Skill Matching — Milestone 11 Unit Tests (candidate_insights.py).

Covers compute_candidate_insights: skills the candidate has beyond what
the job asked for, deduped and grouped by category.
"""

import json
from pathlib import Path

from modules.skill_matching.adapters import adapt_candidate, adapt_job
from modules.skill_matching.innovation.candidate_insights import compute_candidate_insights
from modules.skill_matching.matching import match_job
from modules.skill_matching.models import SkillCategory
from modules.skill_matching.normalization import normalize_candidate, normalize_job

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class TestComputeCandidateInsights:
    def test_skill_not_in_job_requirements_is_a_bonus_skill(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)

        insights = compute_candidate_insights(candidate, matches)

        # Machine Learning is not required or preferred by job_fixture
        assert "Machine Learning" in [b.skill for b in insights.bonus_skills]

    def test_skill_matching_a_requirement_is_excluded_from_bonus(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)

        insights = compute_candidate_insights(candidate, matches)

        bonus_names = {b.skill for b in insights.bonus_skills}
        assert "Python" not in bonus_names  # required, exactly matched
        assert "Kubernetes" not in bonus_names  # preferred, exactly matched

    def test_no_bonus_skills_returns_empty_list_not_error(self):
        # candidate_sparse_fixture has "JavaScript", which job_fixture
        # doesn't require -- that's a real bonus skill, not an empty case.
        # A candidate with literally no skills is the genuine "no bonus" case.
        candidate = normalize_candidate(adapt_candidate({"id": "cand-empty", "skills": []}))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)

        insights = compute_candidate_insights(candidate, matches)
        assert insights.bonus_skills == []
        assert insights.bonus_skill_count == 0

    def test_unmapped_candidate_skill_is_still_included_as_bonus(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)

        # JavaScript isn't in the taxonomy-matched job requirements and
        # resolves to canonical_skill_id="javascript" via normalization,
        # so this exercises the "unmapped-but-still-shown" path only when
        # the skill genuinely fails normalization -- use a raw skill name
        # not in the taxonomy at all to exercise that specific branch.
        from modules.skill_matching.adapters import adapt_candidate as _adapt
        from modules.skill_matching.normalization import normalize_candidate as _normalize

        unmapped_candidate = _normalize(_adapt({"id": "x", "skills": ["Some Obscure Tool"]}))
        insights = compute_candidate_insights(unmapped_candidate, [])

        assert len(insights.bonus_skills) == 1
        assert insights.bonus_skills[0].skill == "Some Obscure Tool"
        assert insights.bonus_skills[0].category == SkillCategory.UNKNOWN

    def test_duplicate_bonus_skill_mentions_are_deduped(self):
        from modules.skill_matching.adapters import adapt_candidate as _adapt
        from modules.skill_matching.normalization import normalize_candidate as _normalize

        candidate = _normalize(_adapt({"id": "x", "skills": ["Machine Learning", "machine learning"]}))
        insights = compute_candidate_insights(candidate, [])

        assert insights.bonus_skill_count == 1

    def test_categories_represented_reflects_bonus_skill_categories(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))
        matches = match_job(job, candidate)

        insights = compute_candidate_insights(candidate, matches)
        assert SkillCategory.DOMAIN_KNOWLEDGE in insights.categories_represented
