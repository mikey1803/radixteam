"""
Main API Router.

Aggregates every module's router under one prefix, so main.py includes
this single router rather than importing each module's router
individually. Registering a new module here should always be a minimal,
additive one-line change — never a restructure of what's already here.

Modules that declare their own internal prefix (profile_builder,
skill_matching, resume_parser) are included as-is; modules whose router
has no prefix of its own get one assigned here at the aggregation point.

resume_parser is imported via its own `backend.modules.*` absolute path
(rather than the `modules.*` convention every other module uses) because
its internal files import each other that way — importing it any other
way would load it as a second, distinct module object. `backend/` is
added to sys.path in main.py to make this resolve.
"""

from fastapi import APIRouter

from modules.jd_analytics.api import router as jd_analytics_router
from modules.profile_builder.api import router as profile_builder_router
from modules.talent_check.api import router as talent_check_router
from modules.skill_matching.api import router as skill_matching_router
from backend.modules.resume_parser.api import router as resume_parser_router

router = APIRouter(prefix="/api/v1")
router.include_router(jd_analytics_router, prefix="/jobs", tags=["JD Analytics"])
router.include_router(resume_parser_router)
router.include_router(profile_builder_router)
router.include_router(talent_check_router, prefix="/talent-check", tags=["Talent Check"])
router.include_router(skill_matching_router)
