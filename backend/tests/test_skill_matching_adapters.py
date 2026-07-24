"""
Skill Matching — Milestone 1 Unit Tests.

Covers adapters.py: translating raw upstream-shaped payloads into internal
models (models.py). Fixtures live in backend/tests/fixtures/skill_matching/.
"""

import json
from pathlib import Path

from modules.skill_matching.adapters import (
    adapt_candidate,
    adapt_job,
    adapt_match_context,
    adapt_trust_signal,
)
from modules.skill_matching.models import (
    Candidate,
    EvidenceSourceType,
    Job,
    MatchContext,
    RequirementLevel,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


# ─── Candidate adapter ───────────────────────────────────────────────────

class TestAdaptCandidate:
    def test_maps_basic_fields(self):
        payload = _load("candidate_fixture.json")
        candidate = adapt_candidate(payload)

        assert isinstance(candidate, Candidate)
        assert candidate.candidate_id == "cand-001"
        assert candidate.name == "Asha Verma"
        assert candidate.completeness_score == 0.82
        assert candidate.profile_status == "Complete"
        assert len(candidate.skills) == 7

    def test_links_skill_to_experience_and_project_evidence(self):
        payload = _load("candidate_fixture.json")
        candidate = adapt_candidate(payload)

        python_skill = next(s for s in candidate.skills if s.raw_text == "Python")
        sources = {e.source_type for e in python_skill.evidence}
        assert EvidenceSourceType.EXPERIENCE in sources
        assert EvidenceSourceType.PROJECT in sources

    def test_links_skill_to_certification_evidence(self):
        payload = _load("candidate_fixture.json")
        candidate = adapt_candidate(payload)

        k8s_skill = next(s for s in candidate.skills if s.raw_text == "Kubernetes")
        sources = {e.source_type for e in k8s_skill.evidence}
        assert EvidenceSourceType.CERTIFICATION in sources

    def test_skill_with_no_cross_referenced_evidence_falls_back_to_profile_summary(self):
        payload = _load("candidate_fixture.json")
        candidate = adapt_candidate(payload)

        ml_skill = next(s for s in candidate.skills if s.raw_text == "Machine Learning")
        assert len(ml_skill.evidence) == 1
        assert ml_skill.evidence[0].source_type == EvidenceSourceType.PROFILE_SUMMARY

    def test_sparse_candidate_still_produces_skill_with_fallback_evidence(self):
        payload = _load("candidate_sparse_fixture.json")
        candidate = adapt_candidate(payload)

        assert len(candidate.skills) == 1
        js_skill = candidate.skills[0]
        assert len(js_skill.evidence) == 1
        assert js_skill.evidence[0].source_type == EvidenceSourceType.PROFILE_SUMMARY

    def test_missing_optional_fields_degrade_gracefully(self):
        candidate = adapt_candidate({"id": "cand-003", "skills": []})
        assert candidate.candidate_id == "cand-003"
        assert candidate.skills == []
        assert candidate.completeness_score is None

    def test_missing_candidate_id_does_not_raise(self):
        candidate = adapt_candidate({"name": "No ID"})
        assert candidate.candidate_id == "unknown"


# ─── Job adapter ─────────────────────────────────────────────────────────

class TestAdaptJob:
    def test_maps_required_and_preferred_skills(self):
        payload = _load("job_fixture.json")
        job = adapt_job(payload)

        assert isinstance(job, Job)
        assert job.job_id == "job-101"
        assert job.title == "Backend Engineer"

        required = [s.raw_text for s in job.skills if s.level == RequirementLevel.REQUIRED]
        preferred = [s.raw_text for s in job.skills if s.level == RequirementLevel.PREFERRED]
        assert required == ["Python", "FastAPI", "Docker", "SQL"]
        assert preferred == ["Kubernetes", "TensorFlow"]

    def test_empty_job_produces_zero_skills_not_an_error(self):
        payload = _load("job_empty_fixture.json")
        job = adapt_job(payload)
        assert job.skills == []

    def test_accepts_dict_shaped_skill_entries(self):
        job = adapt_job({"id": "job-x", "required_skills": [{"name": "Go"}]})
        assert job.skills[0].raw_text == "Go"
        assert job.skills[0].level == RequirementLevel.REQUIRED

    def test_missing_job_id_does_not_raise(self):
        job = adapt_job({"title": "No ID"})
        assert job.job_id == "unknown"


# ─── Talent Check adapter ────────────────────────────────────────────────

class TestAdaptTrustSignal:
    def test_maps_fields_when_present(self):
        payload = _load("talent_check_fixture.json")
        signal = adapt_trust_signal(payload, candidate_id="cand-001")
        assert signal.candidate_id == "cand-001"
        assert signal.overall_trust_score == 0.9
        assert "python" in signal.verified_skill_ids

    def test_returns_none_when_absent(self):
        assert adapt_trust_signal(None, candidate_id="cand-001") is None

    def test_returns_none_when_empty_dict(self):
        assert adapt_trust_signal({}, candidate_id="cand-001") is None


# ─── Full pipeline entry point ───────────────────────────────────────────

class TestAdaptMatchContext:
    def test_builds_complete_context(self):
        job_payload = _load("job_fixture.json")
        candidate_payload = _load("candidate_fixture.json")
        talent_check_payload = _load("talent_check_fixture.json")

        context = adapt_match_context(job_payload, candidate_payload, talent_check_payload)

        assert isinstance(context, MatchContext)
        assert context.candidate.candidate_id == "cand-001"
        assert context.job.job_id == "job-101"
        assert context.trust_signal is not None
        assert context.trust_signal.overall_trust_score == 0.9

    def test_talent_check_is_optional(self):
        job_payload = _load("job_fixture.json")
        candidate_payload = _load("candidate_fixture.json")

        context = adapt_match_context(job_payload, candidate_payload)
        assert context.trust_signal is None
