"""
Skill Matching — Milestone 2 Unit Tests.

Covers validators.py: domain-level validation raising the shared
ValidationError for genuinely invalid input, applied on top of the
internal models produced in Milestone 1.
"""

import json
from pathlib import Path

import pytest

from app.shared.exceptions import ValidationError
from modules.skill_matching.adapters import adapt_job, adapt_match_context
from modules.skill_matching.models import Job, JobSkillRequirement, RequirementLevel
from modules.skill_matching.validators import validate_job, validate_match_context

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class TestValidateJob:
    def test_valid_job_passes(self):
        job = adapt_job(_load("job_fixture.json"))
        validate_job(job)  # should not raise

    def test_empty_job_raises_validation_error(self):
        job = adapt_job(_load("job_empty_fixture.json"))
        with pytest.raises(ValidationError) as exc_info:
            validate_job(job)
        assert "job-102" in exc_info.value.errors[0]

    def test_job_with_only_preferred_skills_passes(self):
        job = Job(
            job_id="job-x",
            skills=[JobSkillRequirement(raw_text="Go", level=RequirementLevel.PREFERRED)],
        )
        validate_job(job)  # preferred-only is still non-empty, should not raise

    def test_job_with_only_required_skills_passes(self):
        job = Job(
            job_id="job-y",
            skills=[JobSkillRequirement(raw_text="Python", level=RequirementLevel.REQUIRED)],
        )
        validate_job(job)


class TestValidateMatchContext:
    def test_valid_context_passes(self):
        context = adapt_match_context(_load("job_fixture.json"), _load("candidate_fixture.json"))
        validate_match_context(context)  # should not raise

    def test_empty_job_in_context_raises(self):
        context = adapt_match_context(
            _load("job_empty_fixture.json"), _load("candidate_fixture.json")
        )
        with pytest.raises(ValidationError):
            validate_match_context(context)

    def test_sparse_candidate_does_not_raise(self):
        # Sparse/empty candidate data is valid input -- only the job side
        # has a hard-invalid state at this layer.
        context = adapt_match_context(
            _load("job_fixture.json"), _load("candidate_sparse_fixture.json")
        )
        validate_match_context(context)  # should not raise

    def test_candidate_with_zero_skills_does_not_raise(self):
        context = adapt_match_context(_load("job_fixture.json"), {"id": "cand-x", "skills": []})
        validate_match_context(context)  # should not raise
