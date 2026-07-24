"""
Talent Check Result model — stores AI evaluation results.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class TalentCheckResult(Base):
    __tablename__ = "talent_check_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(
        String(36), ForeignKey("candidates.id"), nullable=False, index=True
    )
    job_description_id = Column(
        String(36), ForeignKey("job_descriptions.id"), nullable=False, index=True
    )

    # ── Scores ───────────────────────────────────────────────────────────
    overall_score = Column(Float, default=0.0)  # 0–100
    skill_match_score = Column(Float, default=0.0)  # 0–100
    experience_score = Column(Float, default=0.0)  # 0–100

    # ── Recommendation ───────────────────────────────────────────────────
    recommendation = Column(String(20), default="REVIEW")  # PASS | FAIL | REVIEW
    reasoning = Column(Text, nullable=True)  # AI-generated explanation

    # ── Analysis ─────────────────────────────────────────────────────────
    skill_gaps = Column(JSON, default=list)  # ["Docker", "Kubernetes", ...]
    matched_skills = Column(JSON, default=list)  # ["Python", "SQL", ...]
    interview_questions = Column(JSON, default=list)  # [{"question": "...", "focus_area": "..."}]

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────
    candidate = relationship("Candidate", back_populates="talent_check_results")
    job_description = relationship(
        "JobDescription", back_populates="talent_check_results"
    )

    def __repr__(self) -> str:
        return (
            f"<TalentCheckResult(id={self.id}, score={self.overall_score}, "
            f"recommendation={self.recommendation})>"
        )
