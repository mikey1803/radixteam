"""Pydantic schemas for the Resume Parser module."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class FileType(str, Enum):
    """Supported resume file types."""

    PDF = "pdf"
    DOCX = "docx"


class ParseStatus(str, Enum):
    """Status of a parse operation."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ParsedResume(BaseModel):
    """Structured resume data extracted by the parser.

    Maps directly to profile_builder.schemas.ProfileCreate for downstream use.
    """

    personal_info: dict = Field(default_factory=dict)
    summary: str | None = None
    education: list[dict] = Field(default_factory=list)
    experience: list[dict] = Field(default_factory=list)
    skills: list[dict] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)
    certifications: list[dict] = Field(default_factory=list)
    links: list[dict] = Field(default_factory=list)


class ParseMetadata(BaseModel):
    """Metadata about a parse operation."""

    parse_id: str | None = None
    filename: str
    file_type: FileType
    file_size_bytes: int
    raw_text_length: int = 0
    ai_model: str | None = None
    parser_version: str = "1.0.0"
    parse_duration_ms: float = 0.0
    created_at: datetime | None = None


class ParseResult(BaseModel):
    """Complete result of parsing a resume file."""

    parsed_data: ParsedResume
    metadata: ParseMetadata
    status: ParseStatus = ParseStatus.COMPLETED
    errors: list[str] = Field(default_factory=list)


class ParseErrorResponse(BaseModel):
    """Error details when parsing fails."""

    message: str
    filename: str
    errors: list[str] = Field(default_factory=list)


class ParseHistoryItem(BaseModel):
    """Summary of a previous parse operation."""

    parse_id: str
    filename: str
    file_type: FileType
    status: ParseStatus
    created_at: datetime | None = None
