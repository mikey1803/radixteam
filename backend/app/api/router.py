"""Main API router — aggregates all module routers."""

from __future__ import annotations

from fastapi import APIRouter

from backend.modules.profile_builder.api import router as profile_router
from backend.modules.resume_parser.api import router as resume_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(profile_router)
api_router.include_router(resume_router)
