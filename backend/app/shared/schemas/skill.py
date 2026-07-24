"""
THE SHARED DATA CONTRACT.

This is the one true shape for skill data passed between all five modules.
Every module (jd_analytics, resume_parser, profile_builder, talent_check,
skill_matching) imports Skill / ExtractedSkillList from here. Do not redefine
these shapes locally in a module — that's exactly the duplication Chapter 2.6
tells us not to do.

Matches "The Shared Data Contract" section of the hackathon brief exactly,
field-for-field, so JSON produced by any module can be consumed by any other
without translation.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

from app.shared.constants import CATEGORY_CODES, CONFIDENCE_LEVELS

CategoryCode = Literal[
    "DSA", "COD", "OOD", "APTI", "COMM", "AI", "CLOUD",
    "SQL", "SWE", "SYSD", "NETW", "OS", "OTHER",
]
Confidence = Literal["high", "medium", "low"]


class Skill(BaseModel):
    """A single extracted or entered skill."""
    skill_name: str
    category_code: CategoryCode
    evidence: str = Field(default="", description="Short quote or reason")
    confidence: Confidence = "medium"


class ExtractedSkillList(BaseModel):
    """Output of JD Analytics or Resume Parsing."""
    source_type: Literal["jd", "resume"]
    source_file: str
    company: Optional[str] = None
    role: Optional[str] = None
    skills: list[Skill] = Field(default_factory=list)

    # Extra structured fields JD Analytics / Resume Parser can populate.
    title: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    responsibilities: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    industry: Optional[str] = None


class CandidateProfile(BaseModel):
    """Output of Profile Builder."""
    id: Optional[str] = None
    name: str
    email: str
    education: Optional[str] = None
    skills: list[Skill] = Field(default_factory=list)
    hackathons: list[str] = Field(default_factory=list)
    internships: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    preferred_roles: list[str] = Field(default_factory=list)
    cv_file: Optional[str] = None


class SkillsetGapItem(BaseModel):
    category_code: CategoryCode
    required_level: int = Field(ge=1, le=10)
    candidate_level: int = Field(ge=1, le=10)
    gap: bool


class TalentCheckResult(BaseModel):
    """Output of Talent Check."""
    company: str
    skillset_gap: list[SkillsetGapItem]
    readiness_score: int = Field(ge=0, le=100)


class SkillMatchResult(BaseModel):
    """Output of Skill Matching."""
    jd_source_file: str
    match_score: int = Field(ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)


class StandardResponse(BaseModel):
    """Every endpoint in every module returns this shape on success."""
    success: bool = True
    data: dict = Field(default_factory=dict)
