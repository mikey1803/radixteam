"""Talent Check API — STUB. One button: compare profile vs company bar."""
from fastapi import APIRouter
from pydantic import BaseModel

from app.shared.schemas.skill import CandidateProfile
from .service import TalentCheckService

router = APIRouter()
service = TalentCheckService()


class TalentCheckRequest(BaseModel):
    profile: CandidateProfile
    company: str


@router.post("/run")
async def run_talent_check(payload: TalentCheckRequest):
    result = service.run_talent_check(payload.profile.model_dump(), payload.company)
    return {"success": True, "data": result}
