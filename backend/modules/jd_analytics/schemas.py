"""Request/response schemas specific to the JD Analytics API surface."""
from __future__ import annotations

from pydantic import BaseModel

from app.shared.schemas.skill import ExtractedSkillList


class JobRecord(BaseModel):
    id: str
    filename: str
    company: str | None = None
    role: str | None = None
    extracted: ExtractedSkillList


class JobUploadResponse(BaseModel):
    success: bool = True
    data: JobRecord
