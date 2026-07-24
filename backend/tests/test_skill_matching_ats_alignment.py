"""
Skill Matching — Milestone 11 Unit Tests (ats_alignment.py).

Covers compute_ats_alignment: literal keyword presence, in deliberate
contrast to this module's smarter canonical/transferable matching.
"""

import json
from pathlib import Path

from modules.skill_matching.adapters import adapt_candidate, adapt_job
from modules.skill_matching.innovation.ats_alignment import compute_ats_alignment
from modules.skill_matching.matching import MatchType, match_job
from modules.skill_matching.models import Job
from modules.skill_matching.normalization import normalize_candidate, normalize_job

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class TestComputeATSAlignment:
    def test_literally_present_skill_is_matched(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))

        alignment = compute_ats_alignment(candidate, job)
        assert "Python" in alignment.matched_keywords

    def test_literally_absent_skill_is_missing_even_with_a_real_transferable_match(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))

        # Sanity check the contrast: this module's real matching resolves
        # TensorFlow via PyTorch as TRANSFERABLE...
        matches = match_job(job, candidate)
        tensorflow_match = next(m for m in matches if m.requirement.raw_text == "TensorFlow")
        assert tensorflow_match.match_type == MatchType.TRANSFERABLE

        # ...but a naive keyword scan never sees it, because the literal
        # string "TensorFlow" never appears in the candidate's skill list.
        # This is the exact contrast the feature exists to demonstrate.
        alignment = compute_ats_alignment(candidate, job)
        assert "TensorFlow" in alignment.missing_keywords
        assert "TensorFlow" not in alignment.matched_keywords

    def test_keyword_match_rate_calculation(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))

        alignment = compute_ats_alignment(candidate, job)
        # 5 of 6 job skills literally present: Python, FastAPI, Docker, SQL, Kubernetes
        # (TensorFlow is the one literal miss, per the test above)
        assert alignment.keyword_match_rate == 5 / 6

    def test_empty_job_skills_returns_zero_rate_not_error(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_fixture.json")))
        empty_job = Job(job_id="job-empty", skills=[])

        alignment = compute_ats_alignment(candidate, empty_job)
        assert alignment.keyword_match_rate == 0.0
        assert alignment.matched_keywords == []
        assert alignment.missing_keywords == []

    def test_sparse_candidate_matches_nothing(self):
        candidate = normalize_candidate(adapt_candidate(_load("candidate_sparse_fixture.json")))
        job = normalize_job(adapt_job(_load("job_fixture.json")))

        alignment = compute_ats_alignment(candidate, job)
        assert alignment.matched_keywords == []
        assert alignment.keyword_match_rate == 0.0
