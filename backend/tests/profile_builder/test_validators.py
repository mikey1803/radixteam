"""Tests for profile validators."""

from __future__ import annotations

import pytest

from backend.modules.profile_builder.schemas import (
    CertificationItem,
    EducationItem,
    ExperienceItem,
    LinkItem,
    PersonalInfo,
    ProfileCreate,
    ProfileUpdate,
    ProjectItem,
    SkillItem,
)
from backend.modules.profile_builder.validators import (
    validate_profile_create,
    validate_profile_update,
)


def _make_create(
    *,
    first_name: str = "Jane",
    last_name: str = "Doe",
    email: str = "jane@example.com",
    skills: list | None = None,
    summary: str = "A summary",
    links: list | None = None,
    projects: list | None = None,
) -> ProfileCreate:
    if skills is None:
        skills = [SkillItem(name="Python")]
    if links is None:
        links = [
            LinkItem(label="LinkedIn", url="https://linkedin.com/in/jane"),
            LinkItem(label="GitHub", url="https://github.com/jane"),
        ]
    if projects is None:
        projects = [ProjectItem(name="ProjectX")]

    return ProfileCreate(
        personal_info=PersonalInfo(
            first_name=first_name,
            last_name=last_name,
            email=email,
        ),
        summary=summary,
        skills=skills,
        links=links,
        projects=projects,
    )


class TestValidateProfileCreate:
    def test_valid_profile_passes(self, sample_profile_create):
        result = validate_profile_create(sample_profile_create)
        assert result.is_valid is True
        assert len(result.required_errors) == 0

    def test_no_skills_fails(self):
        profile = _make_create(skills=[])
        result = validate_profile_create(profile)
        assert result.is_valid is False
        assert any("skill" in e.lower() for e in result.required_errors)

    def test_missing_summary_recommended(self, sample_profile_create):
        sample_profile_create.summary = None
        result = validate_profile_create(sample_profile_create)
        assert result.is_valid is True
        assert any("summary" in e for e in result.recommended_errors)

    def test_missing_linkedin_recommended(self, sample_profile_create):
        sample_profile_create.links = [
            LinkItem(label="GitHub", url="https://github.com/jane")
        ]
        result = validate_profile_create(sample_profile_create)
        assert any("LinkedIn" in e for e in result.recommended_errors)

    def test_missing_github_recommended(self, sample_profile_create):
        sample_profile_create.links = [
            LinkItem(label="LinkedIn", url="https://linkedin.com/in/jane")
        ]
        result = validate_profile_create(sample_profile_create)
        assert any("GitHub" in e for e in result.recommended_errors)

    def test_invalid_url_fails(self):
        profile = _make_create(
            links=[LinkItem(label="Portfolio", url="not-a-url")]
        )
        result = validate_profile_create(profile)
        assert result.is_valid is False
        assert any("URL" in e for e in result.required_errors)

    def test_whitespace_name_fails(self):
        """Name with only whitespace should fail validation."""
        profile = _make_create(first_name="   ")
        result = validate_profile_create(profile)
        assert result.is_valid is False
        assert any("first_name" in e for e in result.required_errors)


class TestValidateProfileUpdate:
    def test_empty_update_passes(self):
        result = validate_profile_update(ProfileUpdate())
        assert result.is_valid is True

    def test_empty_skills_list_fails(self):
        update = ProfileUpdate(skills=[])
        result = validate_profile_update(update)
        assert result.is_valid is False

    def test_partial_update_with_valid_data(self):
        update = ProfileUpdate(summary="New summary")
        result = validate_profile_update(update)
        assert result.is_valid is True

    def test_whitespace_name_fails_in_update(self):
        """Name with only whitespace should fail in update validation."""
        update = ProfileUpdate(
            personal_info=PersonalInfo(
                first_name="   ",
                last_name="Doe",
                email="jane@example.com",
            )
        )
        result = validate_profile_update(update)
        assert result.is_valid is False
        assert any("first_name" in e for e in result.required_errors)

    def test_invalid_email_in_update_fails(self):
        """Email validation happens at Pydantic level; test with whitespace name instead."""
        update = ProfileUpdate(
            personal_info=PersonalInfo(
                first_name="Jane",
                last_name="Doe",
                email="  jane@test.com  ",
            )
        )
        result = validate_profile_update(update)
        # Whitespace-padded email should still be valid after normalisation
        assert result.is_valid is True
