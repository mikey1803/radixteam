"""
Talent Check API routes.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.talent_check import (
    CandidateCreate,
    CandidateResponse,
    JobDescriptionCreate,
    JobDescriptionResponse,
    ResumeParseRequest,
    ResumeParseResponse,
    TalentCheckRequest,
    TalentCheckResponse,
)
from app.services.talent_check_service import TalentCheckService

router = APIRouter()


def _get_service(db: Session = Depends(get_db)) -> TalentCheckService:
    return TalentCheckService(db)


# ── Candidates ───────────────────────────────────────────────────────────────
@router.post("/candidates", response_model=CandidateResponse, status_code=201)
def create_candidate(
    data: CandidateCreate,
    service: TalentCheckService = Depends(_get_service),
):
    """Create a new candidate profile."""
    return service.create_candidate(**data.model_dump())


@router.get("/candidates", response_model=List[CandidateResponse])
def list_candidates(
    skip: int = 0,
    limit: int = 50,
    service: TalentCheckService = Depends(_get_service),
):
    """List all candidates."""
    return service.list_candidates(skip, limit)


@router.get("/candidates/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    candidate_id: str,
    service: TalentCheckService = Depends(_get_service),
):
    """Get a candidate by ID."""
    try:
        return service.get_candidate(candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/candidates/parse-resume", response_model=ResumeParseResponse)
async def parse_resume(
    data: ResumeParseRequest,
    service: TalentCheckService = Depends(_get_service),
):
    """Parse raw resume text into structured data using AI."""
    try:
        result = await service.parse_resume(data.resume_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume parsing failed: {str(e)}")


# ── Job Descriptions ─────────────────────────────────────────────────────────
@router.post("/job-descriptions", response_model=JobDescriptionResponse, status_code=201)
def create_job_description(
    data: JobDescriptionCreate,
    service: TalentCheckService = Depends(_get_service),
):
    """Create a new job description."""
    return service.create_job_description(**data.model_dump())


@router.get("/job-descriptions", response_model=List[JobDescriptionResponse])
def list_job_descriptions(
    skip: int = 0,
    limit: int = 50,
    service: TalentCheckService = Depends(_get_service),
):
    """List all job descriptions."""
    return service.list_job_descriptions(skip, limit)


@router.get("/job-descriptions/{jd_id}", response_model=JobDescriptionResponse)
def get_job_description(
    jd_id: str,
    service: TalentCheckService = Depends(_get_service),
):
    """Get a job description by ID."""
    try:
        return service.get_job_description(jd_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Talent Check ─────────────────────────────────────────────────────────────
@router.post("/check", response_model=TalentCheckResponse, status_code=201)
async def run_talent_check(
    data: TalentCheckRequest,
    service: TalentCheckService = Depends(_get_service),
):
    """Run a full talent check — scores, gaps, questions, recommendation."""
    try:
        result = await service.run_talent_check(data.candidate_id, data.job_description_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Talent check failed: {str(e)}")


@router.get("/results/{result_id}", response_model=TalentCheckResponse)
def get_result(
    result_id: str,
    service: TalentCheckService = Depends(_get_service),
):
    """Get a specific talent check result."""
    try:
        return service.get_result(result_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/results/candidate/{candidate_id}", response_model=List[TalentCheckResponse])
def get_results_by_candidate(
    candidate_id: str,
    service: TalentCheckService = Depends(_get_service),
):
    """Get all talent check results for a candidate."""
    return service.get_results_by_candidate(candidate_id)
