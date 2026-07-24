"""Tests for Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.modules.profile_builder.schemas import (
    CompletenessResult,
    CertificationItem,
    EducationItem,
    ExperienceItem,
    LinkItem,
    PersonalInfo,
    ProfileCreate,
    ProfileResponse,
    ProfileSearchFilters,
    ProfileUpdate,
    ProjectItem,
    SkillItem,
)


class TestPersonalInfo:
    def test_valid_personal_info(self):
        info = PersonalInfo(
            first_name="John",
            last_name="Smith",
            email="john@example.com",
        )
        assert info.first_name == "John"
        assert info.email == "john@example.com"

    def test_empty_first_name_rejected(self):
        with pytest.raises(ValidationError):
            PersonalInfo(
                first_name="",
                last_name="Smith",
                email="john@example.com",
            )

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            PersonalInfo(
                first_name="John",
                last_name="Smith",
                email="not-an-email",
            )

    def test_optional_fields_default_none(self):
        info = PersonalInfo(
            first_name="John",
            last_name="Smith",
            email="john@example.com",
        )
        assert info.phone is None
        assert info.location is None
        assert info.headline is None


class TestSkillItem:
    def test_minimal_skill(self):
        skill = SkillItem(name="Python")
        assert skill.name == "Python"
        assert skill.category is None

    def test_full_skill(self):
        skill = SkillItem(
            name="FastAPI",
            category="Framework",
            proficiency="Advanced",
        )
        assert skill.proficiency == "Advanced"


class TestProfileCreate:
    def test_valid_profile_create(self, sample_profile_create):
        assert sample_profile_create.personal_info.first_name == "Jane"
        assert len(sample_profile_create.skills) == 3
        assert len(sample_profile_create.experience) == 2

    def test_empty_skills_allowed_at_schema_level(self):
        """Empty skills are allowed in schema; business validation happens in validators."""
        profile = ProfileCreate(
            personal_info=PersonalInfo(
                first_name="A",
                last_name="B",
                email="a@b.com",
            ),
            skills=[],
        )
        assert profile.skills == []


class TestProfileUpdate:
    def test_all_fields_optional(self):
        update = ProfileUpdate()
        assert update.personal_info is None
        assert update.skills is None

    def test_partial_update(self):
        update = ProfileUpdate(
            summary="Updated summary",
            skills=[SkillItem(name="Rust")],
        )
        assert update.summary == "Updated summary"
        assert update.personal_info is None


class TestCompletenessResult:
    def test_score_bounds(self):
        result = CompletenessResult(score=50.0, status="average")
        assert result.score == 50.0

    def test_score_out_of_range(self):
        with pytest.raises(ValidationError):
            CompletenessResult(score=150.0, status="bad")


class TestProfileSearchFilters:
    def test_defaults(self):
        filters = ProfileSearchFilters()
        assert filters.limit == 20
        assert filters.offset == 0
        assert filters.skill is None

    def test_invalid_limit(self):
        with pytest.raises(ValidationError):
            ProfileSearchFilters(limit=0)

    def test_invalid_offset(self):
        with pytest.raises(ValidationError):
            ProfileSearchFilters(offset=-1)
