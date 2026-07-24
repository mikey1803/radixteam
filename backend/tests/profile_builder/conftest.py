"""Shared fixtures for Profile Builder tests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.modules.profile_builder.models import Base, CandidateProfile
from backend.modules.profile_builder.repository import ProfileRepository
from backend.modules.profile_builder.schemas import (
    CertificationItem,
    EducationItem,
    ExperienceItem,
    LinkItem,
    PersonalInfo,
    ProjectItem,
    ProfileCreate,
    SkillItem,
)
from backend.modules.profile_builder.service import ProfileService


# ── Sample Data ─────────────────────────────────────────────────────


@pytest.fixture
def sample_personal_info() -> PersonalInfo:
    return PersonalInfo(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        phone="+1-555-123-4567",
        location="San Francisco, CA",
        headline="Senior Software Engineer",
    )


@pytest.fixture
def sample_skills() -> list[SkillItem]:
    return [
        SkillItem(name="Python", category="Programming", proficiency="Expert"),
        SkillItem(name="FastAPI", category="Framework", proficiency="Advanced"),
        SkillItem(name="PostgreSQL", category="Database", proficiency="Advanced"),
    ]


@pytest.fixture
def sample_education() -> list[EducationItem]:
    return [
        EducationItem(
            institution="MIT",
            degree="BS",
            field_of_study="Computer Science",
            start_date="2015-09",
            end_date="2019-06",
            gpa=3.8,
        )
    ]


@pytest.fixture
def sample_experience() -> list[ExperienceItem]:
    return [
        ExperienceItem(
            company="Acme Corp",
            title="Senior Engineer",
            location="San Francisco, CA",
            start_date="2021-01",
            end_date=None,
            description="Leading backend development.",
            highlights=["Built microservices platform", "Reduced latency 40%"],
        ),
        ExperienceItem(
            company="StartupXYZ",
            title="Software Engineer",
            location="Remote",
            start_date="2019-07",
            end_date="2020-12",
            description="Full-stack development.",
            highlights=["Shipped v1.0"],
        ),
    ]


@pytest.fixture
def sample_projects() -> list[ProjectItem]:
    return [
        ProjectItem(
            name="OpenAnalytics",
            description="Open-source analytics dashboard",
            url="https://github.com/janedoe/openanalytics",
            technologies=["Python", "React", "PostgreSQL"],
            highlights=["500+ GitHub stars"],
        )
    ]


@pytest.fixture
def sample_certifications() -> list[CertificationItem]:
    return [
        CertificationItem(
            name="AWS Solutions Architect",
            issuer="Amazon Web Services",
            date_obtained="2023-03",
            url="https://aws.amazon.com/certification",
        )
    ]


@pytest.fixture
def sample_links() -> list[LinkItem]:
    return [
        LinkItem(label="LinkedIn", url="https://linkedin.com/in/janedoe"),
        LinkItem(label="GitHub", url="https://github.com/janedoe"),
        LinkItem(label="Portfolio", url="https://janedoe.dev"),
    ]


@pytest.fixture
def sample_profile_create(
    sample_personal_info,
    sample_skills,
    sample_education,
    sample_experience,
    sample_projects,
    sample_certifications,
    sample_links,
) -> ProfileCreate:
    return ProfileCreate(
        personal_info=sample_personal_info,
        summary="Experienced software engineer specialising in Python backends.",
        education=sample_education,
        experience=sample_experience,
        skills=sample_skills,
        projects=sample_projects,
        certifications=sample_certifications,
        links=sample_links,
        parser_version="1.0.0",
        resume_version="2024-01",
        ai_model="gpt-4",
    )


@pytest.fixture
def sample_profile_model() -> CandidateProfile:
    now = datetime.now(timezone.utc)
    return CandidateProfile(
        candidate_id="test-uuid-001",
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        phone="+15551234567",
        location="San Francisco, CA",
        headline="Senior Software Engineer",
        summary="Experienced software engineer.",
        education=[
            {"institution": "MIT", "degree": "Bachelor of Science", "field_of_study": "Computer Science"}
        ],
        experience=[
            {"company": "Acme Corp", "title": "Senior Engineer"}
        ],
        skills=[
            {"name": "Python", "category": "Programming"}
        ],
        projects=[
            {"name": "OpenAnalytics", "technologies": ["python", "react"]}
        ],
        certifications=[
            {"name": "AWS Solutions Architect", "issuer": "Amazon Web Services"}
        ],
        links=[
            {"label": "LinkedIn", "url": "https://linkedin.com/in/janedoe"},
            {"label": "GitHub", "url": "https://github.com/janedoe"},
        ],
        completeness_score=82.5,
        status="good",
        parser_version="1.0.0",
        created_at=now,
        updated_at=now,
    )


# ── Mock Repository ─────────────────────────────────────────────────


@pytest.fixture
def mock_repository() -> MagicMock:
    repo = MagicMock(spec=ProfileRepository)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.search = AsyncMock()
    return repo


@pytest.fixture
def profile_service(mock_repository: MagicMock) -> ProfileService:
    return ProfileService(repository=mock_repository)
