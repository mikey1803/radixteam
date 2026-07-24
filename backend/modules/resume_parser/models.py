"""SQLAlchemy ORM models for the Resume Parser module."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for resume_parser models."""

    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ParsedResumeRecord(Base):
    """Stores the result of a resume parse operation."""

    __tablename__ = "parsed_resumes"

    parse_id: str = Column(String(36), primary_key=True)
    filename: str = Column(String(255), nullable=False)
    file_type: str = Column(String(10), nullable=False)
    file_size_bytes: int = Column(Integer, nullable=False)

    # Raw extracted text (for re-processing or auditing)
    raw_text: str | None = Column(Text, nullable=True)

    # Structured extraction result
    parsed_data: dict = Column(JSONB, nullable=False, default=dict)

    # Metadata
    status: str = Column(String(20), nullable=False, default="completed")
    ai_model: str | None = Column(String(100), nullable=True)
    parser_version: str = Column(String(50), nullable=False, default="1.0.0")
    parse_duration_ms: float = Column(Float, nullable=False, default=0.0)
    errors: list = Column(JSONB, nullable=False, default=list)

    created_at: datetime = Column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    def __repr__(self) -> str:
        return f"<ParsedResumeRecord {self.parse_id} ({self.filename})>"
