"""FastAPI router for the Resume Parser module."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from shared.exceptions import AppException
from shared.logging import get_logger, get_request_id
from shared.schemas import APIResponse

from backend.modules.resume_parser.schemas import ParseResult
from backend.modules.resume_parser.service import ResumeParserService

logger = get_logger(__name__)

router = APIRouter(prefix="/resume", tags=["Resume Parser"])


# ── Dependency override point ───────────────────────────────────────
_parser_service: ResumeParserService | None = None


def get_parser_service() -> ResumeParserService:
    """Return the ResumeParserService instance."""
    if _parser_service is None:
        raise RuntimeError(
            "ResumeParserService not initialised. Wire via dependencies."
        )
    return _parser_service


def set_parser_service(service: ResumeParserService) -> None:
    """Allow external wiring of the service."""
    global _parser_service  # noqa: PLW0603
    _parser_service = service


# ── Endpoints ───────────────────────────────────────────────────────


@router.post("/parse", response_model=APIResponse[ParseResult], status_code=201)
async def parse_resume(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    ai_model: str | None = Query(
        default=None,
        description="Override AI model for extraction",
    ),
    service: ResumeParserService = Depends(get_parser_service),
) -> APIResponse[ParseResult] | JSONResponse:
    """Upload and parse a resume file.

    Accepts PDF or DOCX files. Extracts text, uses AI to structure the data,
    and returns a structured parse result compatible with the Profile Builder.
    """
    try:
        file_bytes = await file.read()
        result = await service.parse_resume(
            file_bytes=file_bytes,
            filename=file.filename or "resume.pdf",
            ai_model=ai_model,
        )
        return APIResponse(
            success=True,
            message="Resume parsed successfully",
            data=result,
            request_id=get_request_id(),
        )
    except AppException as exc:
        return _error_response(exc)


@router.get("/parse/{parse_id}", response_model=APIResponse[ParseResult])
async def get_parse_result(
    parse_id: str,
    service: ResumeParserService = Depends(get_parser_service),
) -> APIResponse[ParseResult] | JSONResponse:
    """Retrieve a previous parse result by ID."""
    try:
        result = await service.get_parse_result(parse_id)
        return APIResponse(
            success=True,
            message="Parse result retrieved",
            data=result,
            request_id=get_request_id(),
        )
    except AppException as exc:
        return _error_response(exc)


@router.get("/parses", response_model=APIResponse[list[ParseResult]])
async def list_parse_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ResumeParserService = Depends(get_parser_service),
) -> APIResponse[list[ParseResult]] | JSONResponse:
    """List recent parse results."""
    try:
        results = await service.list_parse_history(limit=limit, offset=offset)
        return APIResponse(
            success=True,
            message=f"Found {len(results)} parse results",
            data=results,
            request_id=get_request_id(),
        )
    except AppException as exc:
        return _error_response(exc)


@router.delete("/parse/{parse_id}", response_model=APIResponse[None])
async def delete_parse_result(
    parse_id: str,
    service: ResumeParserService = Depends(get_parser_service),
) -> APIResponse[None] | JSONResponse:
    """Delete a parse result."""
    try:
        await service.delete_parse_result(parse_id)
        return APIResponse(
            success=True,
            message="Parse result deleted",
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
