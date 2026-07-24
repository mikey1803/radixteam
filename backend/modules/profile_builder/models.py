"""
Profile Builder — SQLAlchemy ORM Models.

Defines the CandidateProfile table storing all candidate data,
completeness scores, and audit metadata.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Float, DateTime, JSON
from app.db.base import Base


class CandidateProfile(Base):
    """
    ORM model for the candidate_profiles table.

    Stores structured profile data built from parsed resume JSON,
    along with completeness scoring and audit metadata.
    """

    __tablename__ = "candidate_profiles"

    # Primary key — UUID4
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Personal information
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True, index=True)

    # Professional summary (auto-generated if missing)
    summary = Column(Text, nullable=True)

    # Structured sections (stored as JSON for flexibility)
    skills = Column(JSON, nullable=False, default=list)
    education = Column(JSON, nullable=False, default=list)
    experience = Column(JSON, nullable=False, default=list)
    projects = Column(JSON, nullable=False, default=list)
    certifications = Column(JSON, nullable=False, default=list)
    links = Column(JSON, nullable=False, default=dict)

    # Completeness scoring
    completeness_score = Column(Float, nullable=False, default=0.0)
    profile_status = Column(String(20), nullable=False, default="Incomplete")

    # Audit metadata
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    resume_version = Column(String(50), nullable=True)
    parser_version = Column(String(50), nullable=True)
    ai_model = Column(String(50), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CandidateProfile(id={self.id}, name={self.name}, "
            f"email={self.email}, status={self.profile_status})>"
        )

    def to_dict(self) -> dict:
        """Convert the ORM model to a plain dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "summary": self.summary,
            "skills": self.skills or [],
            "education": self.education or [],
            "experience": self.experience or [],
            "projects": self.projects or [],
            "certifications": self.certifications or [],
            "links": self.links or {},
            "completeness_score": self.completeness_score,
            "profile_status": self.profile_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resume_version": self.resume_version,
            "parser_version": self.parser_version,
            "ai_model": self.ai_model,
        }
