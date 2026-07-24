"""
Candidate model — stores candidate profiles with parsed resume data.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    skills = Column(JSON, default=list)  # ["Python", "FastAPI", ...]
    experience_years = Column(Float, default=0.0)
    education = Column(JSON, default=list)  # [{"degree": "...", "institution": "..."}]
    resume_text = Column(Text, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationship to talent check results
    talent_check_results = relationship(
        "TalentCheckResult", back_populates="candidate", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Candidate(id={self.id}, name={self.name}, email={self.email})>"
