"""Service layer — business logic for the Profile Builder module."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from shared.exceptions import (
    DatabaseException,
    DuplicateException,
    NotFoundException,
    ValidationException,
)
from shared.logging import get_logger

from backend.modules.profile_builder.completeness import (
    calculate_completeness,
    generate_summary,
)
from backend.modules.profile_builder.merge import (
    deduplicate_certifications,
    deduplicate_projects,
    deduplicate_skills,
    normalize_project_technologies,
    normalize_skills,
)
from backend.modules.profile_builder.models import CandidateProfile
from backend.modules.profile_builder.repository import ProfileRepository
from backend.modules.profile_builder.schemas import (
    CompletenessResult,
    ProfileCreate,
    ProfileResponse,
    ProfileSearchFilters,
    ProfileUpdate,
    ProfileMetadata,
)
from backend.modules.profile_builder.utils import (
    normalize_degree,
    normalize_email,
    normalize_location,
    normalize_phone,
    normalize_url,
)
from backend.modules.profile_builder.validators import (
    validate_profile_create,
    validate_profile_update,
)

logger = get_logger(__name__)


class ProfileService:
    """Orchestrates validation, normalisation, scoring, and persistence."""

    def __init__(self, repository: ProfileRepository) -> None:
        self._repo = repository

    # ── Create ──────────────────────────────────────────────────────

    async def create_profile(self, payload: ProfileCreate) -> ProfileResponse:
        """Validate → normalise → deduplicate → score → persist."""
        # Validate
        validation = validate_profile_create(payload)
        if not validation.is_valid:
            raise ValidationException(
                message="Profile validation failed",
                errors={
                    "required": validation.required_errors,
                    "recommended": validation.recommended_errors,
                },
            )

        # Check for duplicate email
        existing = await self._repo.get_by_email(payload.personal_info.email)
        if existing is not None:
            raise DuplicateException(
                message=f"A profile with email '{payload.personal_info.email}' already exists"
            )

        # Normalise & deduplicate
        normalised = self._normalise_payload(payload)

        # Generate summary if missing
        summary = normalised.summary
        if not summary:
            summary = generate_summary(normalised)

        # Calculate completeness
        completeness = calculate_completeness(normalised)

        # Build model
        now = datetime.now(timezone.utc)
        model = CandidateProfile(
            candidate_id=str(uuid.uuid4()),
            first_name=normalised.personal_info.first_name,
            last_name=normalised.personal_info.last_name,
            email=normalised.personal_info.email,
            phone=normalised.personal_info.phone,
            location=normalised.personal_info.location,
            headline=normalised.personal_info.headline,
            summary=summary,
            education=[e.model_dump() for e in normalised.education],
            experience=[e.model_dump() for e in normalised.experience],
            skills=[s.model_dump() for s in normalised.skills],
            projects=[p.model_dump() for p in normalised.projects],
            certifications=[c.model_dump() for c in normalised.certifications],
            links=[lnk.model_dump() for lnk in normalised.links],
            completeness_score=completeness.score,
            status=completeness.status,
            parser_version=normalised.parser_version,
            resume_version=normalised.resume_version,
            ai_model=normalised.ai_model,
            created_at=now,
            updated_at=now,
        )

        try:
            saved = await self._repo.create(model)
        except Exception as exc:
            logger.error("Database failure during profile creation", error=str(exc))
            raise DatabaseException("Failed to create profile") from exc

        return self._model_to_response(saved, completeness)

    # ── Retrieve ────────────────────────────────────────────────────

    async def get_profile(self, candidate_id: str) -> ProfileResponse:
        """Fetch a profile by ID."""
        model = await self._get_or_raise(candidate_id)
        completeness = self._build_completeness_from_model(model)
        return self._model_to_response(model, completeness)

    # ── Update ──────────────────────────────────────────────────────

    async def update_profile(
        self, candidate_id: str, payload: ProfileUpdate
    ) -> ProfileResponse:
        """Validate → merge → re-score → persist."""
        model = await self._get_or_raise(candidate_id)

        # Validate update payload
        validation = validate_profile_update(payload)
        if not validation.is_valid:
            raise ValidationException(
                message="Profile validation failed",
                errors={"required": validation.required_errors},
            )

        # Merge fields
        if payload.personal_info is not None:
            model.first_name = payload.personal_info.first_name
            model.last_name = payload.personal_info.last_name
            model.email = normalize_email(payload.personal_info.email)
            model.phone = payload.personal_info.phone
            model.location = payload.personal_info.location
            model.headline = payload.personal_info.headline

        if payload.summary is not None:
            model.summary = payload.summary
        if payload.education is not None:
            model.education = [
                e.model_dump() for e in payload.education
            ]
        if payload.experience is not None:
            model.experience = [
                e.model_dump() for e in payload.experience
            ]
        if payload.skills is not None:
            model.skills = [s.model_dump() for s in payload.skills]
        if payload.projects is not None:
            model.projects = [p.model_dump() for p in payload.projects]
        if payload.certifications is not None:
            model.certifications = [
                c.model_dump() for c in payload.certifications
            ]
        if payload.links is not None:
            model.links = [lnk.model_dump() for lnk in payload.links]

        # Re-normalise after merge
        model = self._normalise_model(model)

        # Re-score
        rebuild = self._model_to_create(model)
        completeness = calculate_completeness(rebuild)
        model.completeness_score = completeness.score
        model.status = completeness.status

        # Re-generate summary if now empty
        if not model.summary:
            model.summary = generate_summary(rebuild)

        try:
            saved = await self._repo.update(model)
        except Exception as exc:
            logger.error("Database failure during profile update", error=str(exc))
            raise DatabaseException("Failed to update profile") from exc

        return self._model_to_response(saved, completeness)

    # ── Delete ──────────────────────────────────────────────────────

    async def delete_profile(self, candidate_id: str) -> None:
        """Delete a profile by ID."""
        model = await self._repo.get_by_id(candidate_id)
        if model is None:
            raise NotFoundException("CandidateProfile", candidate_id)

        try:
            await self._repo.delete(candidate_id)
        except Exception as exc:
            logger.error("Database failure during profile deletion", error=str(exc))
            raise DatabaseException("Failed to delete profile") from exc

    # ── Search ──────────────────────────────────────────────────────

    async def search_profiles(
        self, filters: ProfileSearchFilters
    ) -> list[ProfileResponse]:
        """Search profiles with optional filters."""
        try:
            models = await self._repo.search(filters)
        except Exception as exc:
            logger.error("Database failure during search", error=str(exc))
            raise DatabaseException("Search operation failed") from exc

        return [
            self._model_to_response(m, self._build_completeness_from_model(m))
            for m in models
        ]

    # ── Internal helpers ────────────────────────────────────────────

    async def _get_or_raise(self, candidate_id: str) -> CandidateProfile:
        model = await self._repo.get_by_id(candidate_id)
        if model is None:
            raise NotFoundException("CandidateProfile", candidate_id)
        return model

    def _normalise_payload(self, payload: ProfileCreate) -> ProfileCreate:
        """Apply all normalisation and deduplication to a create payload."""
        data = payload.model_dump()

        # Personal info
        data["personal_info"]["email"] = normalize_email(
            payload.personal_info.email
        )
        if payload.personal_info.phone:
            data["personal_info"]["phone"] = normalize_phone(
                payload.personal_info.phone
            )
        if payload.personal_info.location:
            data["personal_info"]["location"] = normalize_location(
                payload.personal_info.location
            )

        # Skills
        raw_skills = payload.skills
        raw_skills = normalize_skills(raw_skills)
        raw_skills = deduplicate_skills(raw_skills)
        data["skills"] = [s.model_dump() for s in raw_skills]

        # Education degrees
        for edu in data["education"]:
            if edu.get("degree"):
                edu["degree"] = normalize_degree(edu["degree"])

        # Projects
        raw_projects = payload.projects
        raw_projects = deduplicate_projects(raw_projects)
        raw_projects = normalize_project_technologies(raw_projects)
        data["projects"] = [p.model_dump() for p in raw_projects]

        # Certifications
        raw_certs = payload.certifications
        raw_certs = deduplicate_certifications(raw_certs)
        data["certifications"] = [c.model_dump() for c in raw_certs]

        # Links
        for lnk in data["links"]:
            lnk["url"] = normalize_url(lnk["url"])

        return ProfileCreate(**data)

    def _normalise_model(self, model: CandidateProfile) -> CandidateProfile:
        """Re-normalise a model after partial update."""
        model.email = normalize_email(model.email)
        if model.phone:
            model.phone = normalize_phone(model.phone)
        if model.location:
            model.location = normalize_location(model.location)
        return model

    def _model_to_create(self, model: CandidateProfile) -> ProfileCreate:
        """Convert an ORM model back into a ProfileCreate for scoring."""
        from backend.modules.profile_builder.schemas import (
            CertificationItem,
            EducationItem,
            ExperienceItem,
            LinkItem,
            PersonalInfo,
            ProjectItem,
            SkillItem,
        )

        return ProfileCreate(
            personal_info=PersonalInfo(
                first_name=model.first_name,
                last_name=model.last_name,
                email=model.email,
                phone=model.phone,
                location=model.location,
                headline=model.headline,
            ),
            summary=model.summary,
            education=[EducationItem(**e) for e in (model.education or [])],
            experience=[ExperienceItem(**e) for e in (model.experience or [])],
            skills=[SkillItem(**s) for s in (model.skills or [])],
            projects=[ProjectItem(**p) for p in (model.projects or [])],
            certifications=[
                CertificationItem(**c) for c in (model.certifications or [])
            ],
            links=[LinkItem(**lnk) for lnk in (model.links or [])],
            parser_version=model.parser_version,
            resume_version=model.resume_version,
            ai_model=model.ai_model,
        )

    def _build_completeness_from_model(
        self, model: CandidateProfile
    ) -> CompletenessResult:
        """Derive a CompletenessResult from an existing stored model."""
        status = model.status
        score = model.completeness_score
        return CompletenessResult(score=score, status=status)

    def _model_to_response(
        self,
        model: CandidateProfile,
        completeness: CompletenessResult,
    ) -> ProfileResponse:
        """Map an ORM model to the API response schema."""
        from backend.modules.profile_builder.schemas import (
            CertificationItem,
            EducationItem,
            ExperienceItem,
            LinkItem,
            PersonalInfo,
            ProjectItem,
            SkillItem,
        )

        return ProfileResponse(
            candidate_id=model.candidate_id,
            personal_info=PersonalInfo(
                first_name=model.first_name,
                last_name=model.last_name,
                email=model.email,
                phone=model.phone,
                location=model.location,
                headline=model.headline,
            ),
            summary=model.summary,
            education=[EducationItem(**e) for e in (model.education or [])],
            experience=[ExperienceItem(**e) for e in (model.experience or [])],
            skills=[SkillItem(**s) for s in (model.skills or [])],
            projects=[ProjectItem(**p) for p in (model.projects or [])],
            certifications=[
                CertificationItem(**c) for c in (model.certifications or [])
            ],
            links=[LinkItem(**lnk) for lnk in (model.links or [])],
            metadata=ProfileMetadata(
                created_at=model.created_at,
                updated_at=model.updated_at,
                parser_version=model.parser_version,
                resume_version=model.resume_version,
                ai_model=model.ai_model,
                completeness_score=model.completeness_score,
            ),
            completeness=completeness,
            status=model.status,
        )
