"""
Main API Router.

Aggregates every module's router under one prefix, so main.py includes
this single router rather than importing each module's router
individually. Registering a new module here should always be a minimal,
additive one-line change — never a restructure of what's already here.

Modules that declare their own internal prefix (profile_builder,
skill_matching) are included as-is; modules whose router has no prefix
of its own get one assigned here at the aggregation point.
"""

from fastapi import APIRouter

from modules.jd_analytics.api import router as jd_analytics_router
from modules.resume_parser.api import router as resume_parser_router
from modules.profile_builder.api import router as profile_builder_router
from modules.talent_check.api import router as talent_check_router
from modules.skill_matching.api import router as skill_matching_router

router = APIRouter(prefix="/api/v1")
router.include_router(jd_analytics_router, prefix="/jobs", tags=["JD Analytics"])
router.include_router(resume_parser_router, prefix="/resumes", tags=["Resume Parser"])
router.include_router(profile_builder_router)
router.include_router(talent_check_router, prefix="/talent-check", tags=["Talent Check"])
router.include_router(skill_matching_router)
