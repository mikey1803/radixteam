"""
Main API Router.

Aggregates every module's router under one prefix, so main.py includes
this single router rather than importing each module's router
individually. Registering a new module here should always be a minimal,
additive one-line change — never a restructure of what's already here.
"""

from fastapi import APIRouter

from modules.profile_builder.api import router as profile_builder_router
from modules.skill_matching.api import router as skill_matching_router

router = APIRouter(prefix="/api/v1")
router.include_router(profile_builder_router)
router.include_router(skill_matching_router)
