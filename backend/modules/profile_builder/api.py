"""
Profile Builder — FastAPI Router (API Layer).

Defines all REST endpoints for the Profile Builder module.
Handles HTTP concerns only — all business logic is in the service layer.

Endpoints:
    POST   /profile                  — Create profile from resume JSON
    GET    /profile/search           — Search profiles with filters
    GET    /profile/{candidate_id}   — Get single profile
    PUT    /profile/{candidate_id}   — Update profile
    DELETE /profile/{candidate_id}   — Delete profile

Note: /profile/search is registered BEFORE /profile/{candidate_id}
      to avoid FastAPI treating "search" as a candidate_id.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.shared.schemas import APIResponse
from app.core.logging import get_logger, set_request_id
from modules.profile_builder import service
from modules.profile_builder.schemas import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    ProfileSearchParams,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/profile", tags=["Profile Builder"])


# ─── POST /profile ──────────────────────────────────────────────────────

@router.post("", response_model=APIResponse, status_code=201)
def create_profile(
    request: ProfileCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Create a new candidate profile from parsed resume JSON.

    Consumes output from the Resume Parser module.
    Validates, deduplicates, normalizes, scores completeness,
    and persists the profile.
    """
    request_id = set_request_id()
    logger.info(f"POST /profile | request_id={request_id}")

    profile = service.create_profile(db, request)
    return APIResponse(
        success=True,
        message="Profile created successfully",
        data=profile.model_dump(),
    )


# ─── GET /profile/search ────────────────────────────────────────────────
# IMPORTANT: This must be registered BEFORE /{candidate_id}

@router.get("/search", response_model=APIResponse)
def search_profiles(
    skill: str | None = Query(None, description="Filter by skill"),
    min_experience: int | None = Query(None, description="Minimum experience entries"),
    location: str | None = Query(None, description="Filter by location"),
    education: str | None = Query(None, description="Filter by education"),
    db: Session = Depends(get_db),
):
    """
    Search candidate profiles with filters.

    Supports filtering by skill, experience count, location, and education.
    Future enhancement: Semantic search using embeddings.
    """
    request_id = set_request_id()
    logger.info(
        f"GET /profile/search | request_id={request_id} | "
        f"skill={skill} location={location} education={education}"
    )

    params = ProfileSearchParams(
        skill=skill,
        min_experience=min_experience,
        location=location,
        education=education,
    )
    profiles = service.search_profiles(db, params)
    return APIResponse(
        success=True,
        message=f"Found {len(profiles)} profile(s)",
        data=[p.model_dump() for p in profiles],
    )


# ─── GET /profile/{candidate_id} ────────────────────────────────────────

@router.get("/{candidate_id}", response_model=APIResponse)
def get_profile(
    candidate_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve a single candidate profile by ID.
    """
    request_id = set_request_id()
    logger.info(
        f"GET /profile/{candidate_id} | request_id={request_id}"
    )

    profile = service.get_profile(db, candidate_id)
    return APIResponse(
        success=True,
        message="Profile retrieved successfully",
        data=profile.model_dump(),
    )


# ─── PUT /profile/{candidate_id} ────────────────────────────────────────

@router.put("/{candidate_id}", response_model=APIResponse)
def update_profile(
    candidate_id: str,
    request: ProfileUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Update an existing candidate profile.

    Supports partial updates — only provided fields are modified.
    Recalculates completeness score after update.
    """
    request_id = set_request_id()
    logger.info(
        f"PUT /profile/{candidate_id} | request_id={request_id}"
    )

    profile = service.update_profile(db, candidate_id, request)
    return APIResponse(
        success=True,
        message="Profile updated successfully",
        data=profile.model_dump(),
    )


# ─── DELETE /profile/{candidate_id} ─────────────────────────────────────

@router.delete("/{candidate_id}", response_model=APIResponse)
def delete_profile(
    candidate_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete a candidate profile.

    Returns success if the profile was found and deleted.
    """
    request_id = set_request_id()
    logger.info(
        f"DELETE /profile/{candidate_id} | request_id={request_id}"
    )

    service.delete_profile(db, candidate_id)
    return APIResponse(
        success=True,
        message="Profile deleted successfully",
    )
