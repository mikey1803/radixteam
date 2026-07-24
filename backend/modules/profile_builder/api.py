"""FastAPI router for the Profile Builder module."""

from __future__ import annotations

from fastapi import APIRouter, Depends, FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from shared.exceptions import AppException
from shared.logging import get_logger, get_request_id
from shared.schemas import APIResponse

from backend.modules.profile_builder.schemas import (
    ProfileCreate,
    ProfileResponse,
    ProfileSearchFilters,
    ProfileUpdate,
)
from backend.modules.profile_builder.service import ProfileService

logger = get_logger(__name__)

router = APIRouter(prefix="/profile", tags=["Profile Builder"])


# ── Dependency override point ───────────────────────────────────────
# In production this is wired via backend/app/api/dependencies.py.
# Module-internal fallback for standalone usage:
_profile_service: ProfileService | None = None


def get_profile_service() -> ProfileService:
    """Return the ProfileService instance (DI placeholder)."""
    if _profile_service is None:
        raise RuntimeError(
            "ProfileService not initialised. Wire via dependencies."
        )
    return _profile_service


def set_profile_service(service: ProfileService) -> None:
    """Allow external wiring of the service (used in tests & startup)."""
    global _profile_service  # noqa: PLW0603
    _profile_service = service


# ── Endpoints ───────────────────────────────────────────────────────


@router.post("", response_model=APIResponse[ProfileResponse], status_code=201)
async def create_profile(
    payload: ProfileCreate,
    service: ProfileService = Depends(get_profile_service),
) -> APIResponse[ProfileResponse] | JSONResponse:
    """Create a new Candidate Profile from Resume Parser output."""
    try:
        result = await service.create_profile(payload)
        return APIResponse(
            success=True,
            message="Profile created successfully",
            data=result,
            request_id=get_request_id(),
        )
    except AppException as exc:
        return _error_response(exc)


@router.get("/search", response_model=APIResponse[list[ProfileResponse]])
async def search_profiles(
    skill: str | None = Query(default=None, description="Filter by skill name"),
    min_experience_years: int | None = Query(default=None, ge=0),
    education_level: str | None = Query(default=None, description="Filter by degree"),
    location: str | None = Query(default=None, description="Filter by location"),
    status: str | None = Query(default=None, description="Filter by profile status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ProfileService = Depends(get_profile_service),
) -> APIResponse[list[ProfileResponse]] | JSONResponse:
    """Search candidate profiles with optional filters."""
    try:
        filters = ProfileSearchFilters(
            skill=skill,
            min_experience_years=min_experience_years,
            education_level=education_level,
            location=location,
            status=status,
            limit=limit,
            offset=offset,
        )
        results = await service.search_profiles(filters)
        return APIResponse(
            success=True,
            message=f"Found {len(results)} profiles",
            data=results,
            request_id=get_request_id(),
        )
    except AppException as exc:
        return _error_response(exc)


@router.get("/{candidate_id}", response_model=APIResponse[ProfileResponse])
async def get_profile(
    candidate_id: str,
    service: ProfileService = Depends(get_profile_service),
) -> APIResponse[ProfileResponse] | JSONResponse:
    """Retrieve a Candidate Profile by ID."""
    try:
        result = await service.get_profile(candidate_id)
        return APIResponse(
            success=True,
            message="Profile retrieved successfully",
            data=result,
            request_id=get_request_id(),
        )
    except AppException as exc:
        return _error_response(exc)


@router.put("/{candidate_id}", response_model=APIResponse[ProfileResponse])
async def update_profile(
    candidate_id: str,
    payload: ProfileUpdate,
    service: ProfileService = Depends(get_profile_service),
) -> APIResponse[ProfileResponse] | JSONResponse:
    """Update an existing Candidate Profile."""
    try:
        result = await service.update_profile(candidate_id, payload)
        return APIResponse(
            success=True,
            message="Profile updated successfully",
            data=result,
            request_id=get_request_id(),
        )
    except AppException as exc:
        return _error_response(exc)


@router.delete("/{candidate_id}", response_model=APIResponse[None])
async def delete_profile(
    candidate_id: str,
    service: ProfileService = Depends(get_profile_service),
) -> APIResponse[None] | JSONResponse:
    """Delete a Candidate Profile."""
    try:
        await service.delete_profile(candidate_id)
        return APIResponse(
            success=True,
            message="Profile deleted successfully",
            data=None,
            request_id=get_request_id(),
        )
    except AppException as exc:
        return _error_response(exc)


# ── Helpers ─────────────────────────────────────────────────────────


class _ErrorBody(BaseModel):
    success: bool = False
    message: str
    errors: object = None
    request_id: str | None = None


def _error_response(exc: AppException) -> JSONResponse:
    """Build a JSONResponse from an AppException."""
    return JSONResponse(
        status_code=exc.status_code,
        content=_ErrorBody(
            message=exc.message,
            errors=exc.details,
            request_id=get_request_id(),
        ).model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register profile-specific exception handlers on the FastAPI app.

    Call this once at startup:
        from backend.modules.profile_builder.api import register_exception_handlers
        register_exception_handlers(app)
    """
    app.add_exception_handler(AppException, _error_response)  # type: ignore[arg-type]
