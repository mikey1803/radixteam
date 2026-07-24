"""
Profile Builder Service — STUB for Role 3.

Per the brief: "mostly good old coding — a form, basic validation, and a
save/load mechanism." LangChain isn't needed here. This stub gives a real
save/load loop against the shared CandidateProfile contract so Roles 4 and
5 aren't blocked waiting on the real form UI.
"""
from __future__ import annotations

from app.shared.schemas.skill import CandidateProfile
from .repository import ProfileRepository


class ProfileBuilderService:
    def __init__(self, repository: ProfileRepository | None = None):
        self.repository = repository or ProfileRepository()

    def create_profile(self, profile: CandidateProfile) -> dict:
        return self.repository.insert(profile.model_dump(exclude={"id"}))

    def update_profile(self, profile_id: str, profile: CandidateProfile) -> dict | None:
        return self.repository.update(profile_id, profile.model_dump(exclude={"id"}))

    def get_profile(self, profile_id: str) -> dict | None:
        return self.repository.get(profile_id)

    def list_profiles(self) -> list[dict]:
        return self.repository.list()
