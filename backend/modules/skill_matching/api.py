"""Skill Matching API — STUB. Matches a candidate's skills against one JD."""
from fastapi import APIRouter
from pydantic import BaseModel

from app.shared.schemas.skill import Skill, ExtractedSkillList
from .service import SkillMatchingService

router = APIRouter()
service = SkillMatchingService()


class SkillMatchRequest(BaseModel):
    candidate_skills: list[Skill]
    jd_skill_list: ExtractedSkillList


@router.post("/run")
async def run_skill_match(payload: SkillMatchRequest):
    result = service.match(
        [s.model_dump() for s in payload.candidate_skills],
        payload.jd_skill_list.model_dump(),
    )
    return {"success": True, "data": result}
