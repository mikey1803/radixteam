"""SQLAlchemy ORM models for the Profile Builder module."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for profile_builder models."""

    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid4())


class CandidateProfile(Base):
    """Relational model for a candidate profile stored in Supabase PostgreSQL."""

    __tablename__ = "candidate_profiles"

    candidate_id: str = Column(String(36), primary_key=True, default=_uuid)

    # Personal info (kept as top-level columns for search)
    first_name: str = Column(String(100), nullable=False)
    last_name: str = Column(String(100), nullable=False)
    email: str = Column(String(255), nullable=False, unique=True, index=True)
    phone: str | None = Column(String(30), nullable=True)
    location: str | None = Column(String(255), nullable=True, index=True)
    headline: str | None = Column(String(300), nullable=True)

    # Summary
    summary: str | None = Column(Text, nullable=True)

    # JSONB sections for flexible nested data
    education: list[dict] = Column(JSONB, nullable=False, default=list)
    experience: list[dict] = Column(JSONB, nullable=False, default=list)
    skills: list[dict] = Column(JSONB, nullable=False, default=list)
    projects: list[dict] = Column(JSONB, nullable=False, default=list)
    certifications: list[dict] = Column(JSONB, nullable=False, default=list)
    links: list[dict] = Column(JSONB, nullable=False, default=list)

    # Scoring / status
    completeness_score: float = Column(Float, nullable=False, default=0.0)
    status: str = Column(String(20), nullable=False, default="incomplete")

    # Metadata
    parser_version: str | None = Column(String(50), nullable=True)
    resume_version: str | None = Column(String(50), nullable=True)
    ai_model: str | None = Column(String(100), nullable=True)
    created_at: datetime = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: datetime = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    def __repr__(self) -> str:
        return f"<CandidateProfile {self.candidate_id} ({self.email})>"
