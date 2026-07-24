"""
Central API router — aggregates all route modules.
"""

from fastapi import APIRouter

from app.api.routes import talent_check

api_router = APIRouter(prefix="/api/v1")

# ── Register sub-routers ─────────────────────────────────────────────────────
api_router.include_router(
    talent_check.router, prefix="/talent-check", tags=["Talent Check"]
)


@api_router.get("/health", tags=["Health"])
async def health_check():
    """Simple health-check endpoint."""
    return {"status": "ok"}
