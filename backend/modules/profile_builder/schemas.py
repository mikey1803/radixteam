"""
Profile Builder — Pydantic Schemas.

Request/response models for the Profile Builder API.
These are the data contracts consumed and produced by this module.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─── Section Item Schemas ───────────────────────────────────────────────

class EducationItem(BaseModel):
    """A single education entry."""
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None


class ExperienceItem(BaseModel):
    """A single work experience entry."""
    company: str
    title: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    technologies: list[str] = []


class ProjectItem(BaseModel):
    """A single project entry."""
    name: str
    description: Optional[str] = None
    technologies: list[str] = []
    url: Optional[str] = None


class CertificationItem(BaseModel):
    """A single certification entry."""
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None


class LinksInfo(BaseModel):
    """Links associated with a candidate profile."""
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


class ProfileMetadata(BaseModel):
    """Audit metadata for traceability."""
    resume_version: Optional[str] = None
    parser_version: Optional[str] = None
    ai_model: Optional[str] = None


# ─── Request Schemas ────────────────────────────────────────────────────

class ProfileCreateRequest(BaseModel):
    """
    Input schema for creating a candidate profile.

    This is the contract consumed from the Resume Parser module.
    Mandatory fields: name, email, at least one skill.
    """
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: list[str] = []
    education: list[EducationItem] = []
    experience: list[ExperienceItem] = []
    projects: list[ProjectItem] = []
    certifications: list[CertificationItem] = []
    links: Optional[LinksInfo] = None
    metadata: Optional[ProfileMetadata] = None


class ProfileUpdateRequest(BaseModel):
    """
    Input schema for updating a candidate profile.

    All fields are optional — only provided fields are updated.
    """
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[list[str]] = None
    education: Optional[list[EducationItem]] = None
    experience: Optional[list[ExperienceItem]] = None
    projects: Optional[list[ProjectItem]] = None
    certifications: Optional[list[CertificationItem]] = None
    links: Optional[LinksInfo] = None
    metadata: Optional[ProfileMetadata] = None


# ─── Response Schemas ───────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    """Full candidate profile response."""
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: list[str] = []
    education: list[dict] = []
    experience: list[dict] = []
    projects: list[dict] = []
    certifications: list[dict] = []
    links: dict = {}
    completeness_score: float = 0.0
    profile_status: str = "Incomplete"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    resume_version: Optional[str] = None
    parser_version: Optional[str] = None
    ai_model: Optional[str] = None


class ProfileSearchParams(BaseModel):
    """Query parameters for profile search."""
    skill: Optional[str] = None
    min_experience: Optional[int] = None
    location: Optional[str] = None
    education: Optional[str] = None
