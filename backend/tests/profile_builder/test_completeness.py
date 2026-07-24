"""Tests for completeness scoring and summary generation."""

from __future__ import annotations

import pytest

from backend.modules.profile_builder.completeness import (
    calculate_completeness,
    generate_summary,
    recalculate_from_update,
)
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


def _minimal_profile() -> ProfileCreate:
    return ProfileCreate(
        personal_info=PersonalInfo(
            first_name="A",
            last_name="B",
            email="a@b.com",
        ),
        skills=[SkillItem(name="Python")],
    )


def _full_profile() -> ProfileCreate:
    return ProfileCreate(
        personal_info=PersonalInfo(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="+15551234567",
            location="San Francisco, CA",
            headline="Senior Engineer",
        ),
        summary="Experienced engineer.",
        education=[
            EducationItem(
                institution="MIT",
                degree="BS",
                field_of_study="CS",
                gpa=3.9,
            )
        ],
        experience=[
            ExperienceItem(company="A", title="Engineer"),
            ExperienceItem(company="B", title="Lead"),
            ExperienceItem(company="C", title="Director"),
            ExperienceItem(company="D", title="VP"),
        ],
        skills=[
            SkillItem(name="Python"),
            SkillItem(name="Rust"),
            SkillItem(name="Go"),
            SkillItem(name="TypeScript"),
            SkillItem(name="SQL"),
        ],
        projects=[
            ProjectItem(name="P1"),
            ProjectItem(name="P2"),
            ProjectItem(name="P3"),
        ],
        certifications=[
            CertificationItem(name="AWS"),
            CertificationItem(name="GCP"),
        ],
        links=[
            LinkItem(label="LinkedIn", url="https://linkedin.com/in/jane"),
            LinkItem(label="GitHub", url="https://github.com/jane"),
            LinkItem(label="Portfolio", url="https://jane.dev"),
        ],
    )


class TestCalculateCompleteness:
    def test_minimal_profile_low_score(self):
        result = calculate_completeness(_minimal_profile())
        assert result.score < 40
        assert result.status == "incomplete"

    def test_full_profile_high_score(self):
        result = calculate_completeness(_full_profile())
        assert result.score >= 90
        assert result.status == "excellent"

    def test_score_bounds(self):
        result = calculate_completeness(_full_profile())
        assert 0 <= result.score <= 100

    def test_section_scores_present(self):
        result = calculate_completeness(_full_profile())
        expected_sections = {
            "personal_information",
            "skills",
            "education",
            "experience",
            "projects",
            "certifications",
            "links",
        }
        assert set(result.section_scores.keys()) == expected_sections

    def test_average_profile(self):
        profile = ProfileCreate(
            personal_info=PersonalInfo(
                first_name="A",
                last_name="B",
                email="a@b.com",
            ),
            summary="Some summary",
            skills=[SkillItem(name="Python"), SkillItem(name="Java")],
            experience=[ExperienceItem(company="X", title="Dev")],
            projects=[ProjectItem(name="P1")],
            links=[
                LinkItem(label="LinkedIn", url="https://linkedin.com/in/x"),
            ],
        )
        result = calculate_completeness(profile)
        assert 41 <= result.score <= 70
        assert result.status == "average"

    def test_good_profile(self):
        profile = ProfileCreate(
            personal_info=PersonalInfo(
                first_name="A",
                last_name="B",
                email="a@b.com",
                phone="+15551234567",
                location="NYC",
                headline="Engineer",
            ),
            summary="Summary",
            education=[EducationItem(institution="MIT", degree="BS", gpa=3.5)],
            experience=[
                ExperienceItem(company="A", title="Dev"),
                ExperienceItem(company="B", title="Lead"),
            ],
            skills=[
                SkillItem(name="Python"),
                SkillItem(name="Java"),
                SkillItem(name="Go"),
            ],
            projects=[ProjectItem(name="P1"), ProjectItem(name="P2")],
            links=[
                LinkItem(label="LinkedIn", url="https://linkedin.com/in/x"),
                LinkItem(label="GitHub", url="https://github.com/x"),
            ],
        )
        result = calculate_completeness(profile)
        assert 71 <= result.score <= 90
        assert result.status == "good"


class TestGenerateSummary:
    def test_generates_from_skills_and_experience(self):
        profile = _full_profile()
        summary = generate_summary(profile)
        assert "Jane Doe" in summary
        assert "Python" in summary
        assert len(summary.split()) <= 150

    def test_minimal_summary(self):
        profile = _minimal_profile()
        summary = generate_summary(profile)
        assert "A B" in summary
        assert len(summary) > 0

    def test_summary_respects_word_limit(self):
        profile = _full_profile()
        summary = generate_summary(profile)
        assert len(summary.split()) <= 150


class TestRecalculateFromUpdate:
    def test_update_adds_skills(self):
        existing = _minimal_profile()
        update = ProfileUpdate(
            skills=[
                SkillItem(name="Python"),
                SkillItem(name="Rust"),
                SkillItem(name="Go"),
            ]
        )
        result = recalculate_from_update(existing, update)
        assert result.score > calculate_completeness(existing).score
