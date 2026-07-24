"""
Repository layer — CRUD operations for Talent Check entities.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.talent_check_result import TalentCheckResult


class TalentCheckRepository:
    """Pure DB operations, no business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Candidates ───────────────────────────────────────────────────────
    def create_candidate(self, **kwargs) -> Candidate:
        candidate = Candidate(**kwargs)
        self.db.add(candidate)
        self.db.flush()
        return candidate

    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        return self.db.query(Candidate).filter(Candidate.id == candidate_id).first()

    def get_candidate_by_email(self, email: str) -> Optional[Candidate]:
        return self.db.query(Candidate).filter(Candidate.email == email).first()

    def list_candidates(self, skip: int = 0, limit: int = 50) -> List[Candidate]:
        return self.db.query(Candidate).offset(skip).limit(limit).all()

    # ── Job Descriptions ─────────────────────────────────────────────────
    def create_job_description(self, **kwargs) -> JobDescription:
        jd = JobDescription(**kwargs)
        self.db.add(jd)
        self.db.flush()
        return jd

    def get_job_description(self, jd_id: str) -> Optional[JobDescription]:
        return (
            self.db.query(JobDescription)
            .filter(JobDescription.id == jd_id)
            .first()
        )

    def list_job_descriptions(
        self, skip: int = 0, limit: int = 50
    ) -> List[JobDescription]:
        return self.db.query(JobDescription).offset(skip).limit(limit).all()

    # ── Results ──────────────────────────────────────────────────────────
    def create_result(self, **kwargs) -> TalentCheckResult:
        result = TalentCheckResult(**kwargs)
        self.db.add(result)
        self.db.flush()
        return result

    def get_result(self, result_id: str) -> Optional[TalentCheckResult]:
        return (
            self.db.query(TalentCheckResult)
            .filter(TalentCheckResult.id == result_id)
            .first()
        )

    def get_results_by_candidate(
        self, candidate_id: str
    ) -> List[TalentCheckResult]:
        return (
            self.db.query(TalentCheckResult)
            .filter(TalentCheckResult.candidate_id == candidate_id)
            .order_by(TalentCheckResult.created_at.desc())
            .all()
        )
