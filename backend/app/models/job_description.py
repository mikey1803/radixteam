"""
Job Description model — stores JDs for talent evaluation.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list)  # ["Python", "SQL", ...]
    preferred_skills = Column(JSON, default=list)  # ["Docker", "AWS", ...]
    min_experience = Column(Float, default=0.0)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationship to talent check results
    talent_check_results = relationship(
        "TalentCheckResult",
        back_populates="job_description",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<JobDescription(id={self.id}, title={self.title})>"
