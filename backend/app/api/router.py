"""
Aggregates every module's router into one API surface.
Each module owns its own routes/prefix; this file just wires them together.
"""
from fastapi import APIRouter

from modules.jd_analytics.api import router as jd_analytics_router
from modules.resume_parser.api import router as resume_parser_router
from modules.profile_builder.api import router as profile_builder_router
from modules.talent_check.api import router as talent_check_router
from modules.skill_matching.api import router as skill_matching_router

api_router = APIRouter()

api_router.include_router(jd_analytics_router, prefix="/jobs", tags=["JD Analytics"])
api_router.include_router(resume_parser_router, prefix="/resumes", tags=["Resume Parser"])
api_router.include_router(profile_builder_router, prefix="/profiles", tags=["Profile Builder"])
api_router.include_router(talent_check_router, prefix="/talent-check", tags=["Talent Check"])
api_router.include_router(skill_matching_router, prefix="/skill-match", tags=["Skill Matching"])
