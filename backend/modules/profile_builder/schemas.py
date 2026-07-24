"""Pydantic schemas for the Profile Builder module."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, HttpUrl


# ── Personal Information ────────────────────────────────────────────


class PersonalInfo(BaseModel):
    """Candidate personal details."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = None
    location: str | None = None
    headline: str | None = None


# ── Education ───────────────────────────────────────────────────────


class EducationItem(BaseModel):
    """Single education entry."""

    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa: float | None = None


# ── Experience ──────────────────────────────────────────────────────


class ExperienceItem(BaseModel):
    """Single work-experience entry."""

    company: str
    title: str
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    highlights: list[str] = Field(default_factory=list)


# ── Skills ──────────────────────────────────────────────────────────


class SkillItem(BaseModel):
    """Single skill entry."""

    name: str
    category: str | None = None
    proficiency: str | None = None


# ── Projects ────────────────────────────────────────────────────────


class ProjectItem(BaseModel):
    """Single project entry."""

    name: str
    description: str | None = None
    url: str | None = None
    technologies: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)


# ── Certifications ─────────────────────────────────────────────────


class CertificationItem(BaseModel):
    """Single certification entry."""

    name: str
    issuer: str | None = None
    date_obtained: str | None = None
    expiry_date: str | None = None
    url: str | None = None


# ── Links ───────────────────────────────────────────────────────────


class LinkItem(BaseModel):
    """External link (LinkedIn, GitHub, portfolio, etc.)."""

    label: str
    url: str


# ── Metadata ────────────────────────────────────────────────────────


class ProfileMetadata(BaseModel):
    """Metadata attached to every profile."""

    created_at: datetime | None = None
    updated_at: datetime | None = None
    parser_version: str | None = None
    resume_version: str | None = None
    ai_model: str | None = None
    completeness_score: float = 0.0


# ── Completeness ────────────────────────────────────────────────────


class CompletenessResult(BaseModel):
    """Output of the completeness calculator."""

    score: float = Field(ge=0, le=100)
    status: str
    section_scores: dict[str, float] = Field(default_factory=dict)


# ── Validation ──────────────────────────────────────────────────────


class ValidationResult(BaseModel):
    """Structured result of profile validation."""

    is_valid: bool
    required_errors: list[str] = Field(default_factory=list)
    recommended_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ── Create / Update / Response ─────────────────────────────────────


class ProfileCreate(BaseModel):
    """Payload for POST /profile."""

    personal_info: PersonalInfo
    summary: str | None = None
    education: list[EducationItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    skills: list[SkillItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
    links: list[LinkItem] = Field(default_factory=list)
    parser_version: str | None = None
    resume_version: str | None = None
    ai_model: str | None = None


class ProfileUpdate(BaseModel):
    """Payload for PUT /profile/{candidate_id} — all fields optional."""

    personal_info: PersonalInfo | None = None
    summary: str | None = None
    education: list[EducationItem] | None = None
    experience: list[ExperienceItem] | None = None
    skills: list[SkillItem] | None = None
    projects: list[ProjectItem] | None = None
    certifications: list[CertificationItem] | None = None
    links: list[LinkItem] | None = None


class ProfileResponse(BaseModel):
    """Full canonical Candidate Profile returned by the API."""

    candidate_id: str
    personal_info: PersonalInfo
    summary: str | None = None
    education: list[EducationItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    skills: list[SkillItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
    links: list[LinkItem] = Field(default_factory=list)
    metadata: ProfileMetadata = Field(default_factory=ProfileMetadata)
    completeness: CompletenessResult = Field(default_factory=CompletenessResult)
    status: str = "incomplete"


# ── Search ──────────────────────────────────────────────────────────


class ProfileSearchFilters(BaseModel):
    """Query parameters for GET /profile/search."""

    skill: str | None = None
    min_experience_years: int | None = Field(default=None, ge=0)
    education_level: str | None = None
    location: str | None = None
    status: str | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
