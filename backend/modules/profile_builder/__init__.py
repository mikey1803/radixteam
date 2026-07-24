"""Profile Builder module — converts Resume Parser output into validated Candidate Profiles."""

from backend.modules.profile_builder.api import router as profile_router
from backend.modules.profile_builder.service import ProfileService

__all__ = ["profile_router", "ProfileService"]
