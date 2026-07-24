"""
Talent Check service — business logic + AI integration.
"""

import json
import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.ai_provider import get_ai_provider
from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.talent_check_result import TalentCheckResult
from app.repositories.talent_check_repo import TalentCheckRepository
from modules.talent_check.prompts import (
    INTERVIEW_QUESTIONS_PROMPT,
    RESUME_PARSE_PROMPT,
    TALENT_CHECK_PROMPT,
)

logger = logging.getLogger(__name__)


class TalentCheckService:
    """Orchestrates talent evaluation pipeline."""

    def __init__(self, db: Session) -> None:
        self.repo = TalentCheckRepository(db)
        self.ai = get_ai_provider()

    # ── Resume Parsing ───────────────────────────────────────────────────
    async def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """Use AI to extract structured data from raw resume text."""
        prompt = RESUME_PARSE_PROMPT.format(resume_text=resume_text)
        result = await self.ai.generate_structured(prompt)
        return result

    # ── Candidate CRUD ───────────────────────────────────────────────────
    def create_candidate(self, **kwargs) -> Candidate:
        return self.repo.create_candidate(**kwargs)

    def get_candidate(self, candidate_id: str) -> Candidate:
        candidate = self.repo.get_candidate(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate not found: {candidate_id}")
        return candidate

    def list_candidates(self, skip: int = 0, limit: int = 50) -> List[Candidate]:
        return self.repo.list_candidates(skip, limit)

    # ── JD CRUD ──────────────────────────────────────────────────────────
    def create_job_description(self, **kwargs) -> JobDescription:
        return self.repo.create_job_description(**kwargs)

    def get_job_description(self, jd_id: str) -> JobDescription:
        jd = self.repo.get_job_description(jd_id)
        if not jd:
            raise ValueError(f"Job Description not found: {jd_id}")
        return jd

    def list_job_descriptions(self, skip: int = 0, limit: int = 50) -> List[JobDescription]:
        return self.repo.list_job_descriptions(skip, limit)

    # ── Core Talent Check Pipeline ───────────────────────────────────────
    async def run_talent_check(
        self, candidate_id: str, job_description_id: str
    ) -> TalentCheckResult:
        """Full evaluation pipeline: score → gap analysis → questions → recommendation."""
        # 1. Fetch entities
        candidate = self.get_candidate(candidate_id)
        jd = self.get_job_description(job_description_id)

        # 2. AI-powered scoring
        scores = await self._score_candidate(candidate, jd)

        # 3. Generate interview questions
        questions = await self._generate_interview_questions(
            candidate, jd, scores.get("skill_gaps", []), scores.get("matched_skills", [])
        )

        # 4. Calculate recommendation
        overall_score = scores.get("overall_score", 0)
        recommendation = self._calculate_recommendation(overall_score)

        # 5. Save result
        result = self.repo.create_result(
            candidate_id=candidate_id,
            job_description_id=job_description_id,
            overall_score=overall_score,
            skill_match_score=scores.get("skill_match_score", 0),
            experience_score=scores.get("experience_score", 0),
            recommendation=recommendation,
            reasoning=scores.get("reasoning", ""),
            skill_gaps=scores.get("skill_gaps", []),
            matched_skills=scores.get("matched_skills", []),
            interview_questions=questions,
        )

        logger.info(
            f"Talent check complete: candidate={candidate_id}, "
            f"score={overall_score}, recommendation={recommendation}"
        )
        return result

    async def _score_candidate(
        self, candidate: Candidate, jd: JobDescription
    ) -> Dict[str, Any]:
        """Use AI to score candidate against JD."""
        prompt = TALENT_CHECK_PROMPT.format(
            candidate_name=candidate.name,
            candidate_skills=", ".join(candidate.skills or []),
            experience_years=candidate.experience_years,
            education=json.dumps(candidate.education or []),
            resume_text=(candidate.resume_text or "Not provided")[:2000],
            jd_title=jd.title,
            jd_company=jd.company or "Not specified",
            jd_description=jd.description[:2000],
            required_skills=", ".join(jd.required_skills or []),
            preferred_skills=", ".join(jd.preferred_skills or []),
            min_experience=jd.min_experience,
        )
        return await self.ai.generate_structured(prompt)

    async def _generate_interview_questions(
        self,
        candidate: Candidate,
        jd: JobDescription,
        skill_gaps: List[str],
        matched_skills: List[str],
    ) -> List[Dict[str, str]]:
        """Use AI to generate targeted interview questions."""
        prompt = INTERVIEW_QUESTIONS_PROMPT.format(
            jd_title=jd.title,
            jd_description=jd.description[:1500],
            candidate_skills=", ".join(candidate.skills or []),
            skill_gaps=", ".join(skill_gaps) if skill_gaps else "None identified",
            matched_skills=", ".join(matched_skills) if matched_skills else "None identified",
        )
        result = await self.ai.generate_structured(prompt)
        # Result could be a list or dict with a key
        if isinstance(result, list):
            return result
        return result.get("questions", [])

    @staticmethod
    def _calculate_recommendation(overall_score: float) -> str:
        """Score-based recommendation: ≥70 PASS, 50-69 REVIEW, <50 FAIL."""
        if overall_score >= 70:
            return "PASS"
        elif overall_score >= 50:
            return "REVIEW"
        return "FAIL"

    # ── Result queries ───────────────────────────────────────────────────
    def get_result(self, result_id: str) -> TalentCheckResult:
        result = self.repo.get_result(result_id)
        if not result:
            raise ValueError(f"Result not found: {result_id}")
        return result

    def get_results_by_candidate(self, candidate_id: str) -> List[TalentCheckResult]:
        return self.repo.get_results_by_candidate(candidate_id)
