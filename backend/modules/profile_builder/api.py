"""Profile Builder API — STUB. Real form-driven CRUD against CandidateProfile."""
from fastapi import APIRouter

from app.shared.exceptions import NotFoundErrorApp
from app.shared.schemas.skill import CandidateProfile
from .service import ProfileBuilderService

router = APIRouter()
service = ProfileBuilderService()


@router.post("")
async def create_profile(profile: CandidateProfile):
    record = service.create_profile(profile)
    return {"success": True, "data": record}


@router.put("/{profile_id}")
async def update_profile(profile_id: str, profile: CandidateProfile):
    record = service.update_profile(profile_id, profile)
    if not record:
        raise NotFoundErrorApp(f"Profile '{profile_id}' not found.")
    return {"success": True, "data": record}


@router.get("")
async def list_profiles():
    return {"success": True, "data": service.list_profiles()}


@router.get("/{profile_id}")
async def get_profile(profile_id: str):
    record = service.get_profile(profile_id)
    if not record:
        raise NotFoundErrorApp(f"Profile '{profile_id}' not found.")
    return {"success": True, "data": record}
