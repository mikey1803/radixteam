"""
Pydantic schemas for the Talent Check module.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# ── Candidate ────────────────────────────────────────────────────────────────
class CandidateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., max_length=255)
    phone: Optional[str] = None
    skills: List[str] = []
    experience_years: float = 0.0
    education: List[Dict[str, Any]] = []
    resume_text: Optional[str] = None


class CandidateResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    skills: List[str]
    experience_years: float
    education: List[Dict[str, Any]]
    resume_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Job Description ──────────────────────────────────────────────────────────
class JobDescriptionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    company: Optional[str] = None
    description: str = Field(..., min_length=10)
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    min_experience: float = 0.0


class JobDescriptionResponse(BaseModel):
    id: str
    title: str
    company: Optional[str]
    description: str
    required_skills: List[str]
    preferred_skills: List[str]
    min_experience: float
    created_at: datetime

    class Config:
        from_attributes = True


# ── Talent Check ─────────────────────────────────────────────────────────────
class TalentCheckRequest(BaseModel):
    candidate_id: str
    job_description_id: str


class InterviewQuestion(BaseModel):
    question: str
    focus_area: str


class TalentCheckResponse(BaseModel):
    id: str
    candidate_id: str
    job_description_id: str
    overall_score: float
    skill_match_score: float
    experience_score: float
    recommendation: str
    reasoning: Optional[str]
    skill_gaps: List[str]
    matched_skills: List[str]
    interview_questions: List[Dict[str, str]]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Resume Parse ─────────────────────────────────────────────────────────────
class ResumeParseRequest(BaseModel):
    resume_text: str = Field(..., min_length=20)


class ResumeParseResponse(BaseModel):
    name: str
    email: Optional[str]
    phone: Optional[str]
    skills: List[str]
    experience_years: float
    education: List[Dict[str, Any]]
