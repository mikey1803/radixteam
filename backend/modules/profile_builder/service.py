"""
Profile Builder — Service Layer.

Business logic orchestrator. Contains ALL business rules.
No SQL. No HTTP. No UI.

Responsibilities:
    - Validate input data
    - Check for duplicate profiles
    - Merge & deduplicate sections
    - Normalize locations & degrees
    - Generate professional summary if missing
    - Calculate completeness score
    - Persist via repository
    - Structured logging with candidate_id and timestamps
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from modules.profile_builder import repository
from modules.profile_builder.models import CandidateProfile
from modules.profile_builder.schemas import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    ProfileResponse,
    ProfileSearchParams,
)
from modules.profile_builder.validators import (
    validate_profile_data,
    validate_candidate_id,
    validate_urls,
    sanitize_string,
)
from modules.profile_builder.merge import merge_profile_sections
from modules.profile_builder.completeness import (
    calculate_completeness,
    get_profile_status,
)
from modules.profile_builder.utils import generate_summary, generate_uuid
from app.shared.exceptions import (
    ValidationError,
    NotFoundError,
    DuplicateError,
    DatabaseError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def _profile_to_response(profile: CandidateProfile) -> ProfileResponse:
    """Convert a CandidateProfile ORM instance to a ProfileResponse."""
    return ProfileResponse(
        id=profile.id,
        name=profile.name,
        email=profile.email,
        phone=profile.phone,
        location=profile.location,
        summary=profile.summary,
        skills=profile.skills or [],
        education=profile.education or [],
        experience=profile.experience or [],
        projects=profile.projects or [],
        certifications=profile.certifications or [],
        links=profile.links or {},
        completeness_score=profile.completeness_score,
        profile_status=profile.profile_status,
        created_at=profile.created_at.isoformat() if profile.created_at else None,
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None,
        resume_version=profile.resume_version,
        parser_version=profile.parser_version,
        ai_model=profile.ai_model,
    )


def create_profile(db: Session, request: ProfileCreateRequest) -> ProfileResponse:
    """
    Create a new candidate profile from Resume Parser output.

    Flow:
        1. Validate mandatory fields (name, email, ≥1 skill)
        2. Validate URLs if provided
        3. Check for duplicate email
        4. Merge & deduplicate sections
        5. Normalize locations & degrees
        6. Generate summary if missing
        7. Calculate completeness score + status
        8. Persist via repository
        9. Log "Profile Created"
        10. Return ProfileResponse

    Raises:
        ValidationError: If mandatory fields are missing or invalid.
        DuplicateError: If a profile with the same email already exists.
        DatabaseError: If the database operation fails.
    """
    # Step 1: Validate mandatory fields
    is_valid, errors = validate_profile_data(request)
    if not is_valid:
        logger.warning(f"Validation failed | errors={errors}")
        raise ValidationError(message="Profile validation failed", errors=errors)

    # Step 2: Validate URLs
    if request.links:
        urls_valid, url_errors = validate_urls(request.links)
        if not urls_valid:
            raise ValidationError(message="URL validation failed", errors=url_errors)

    # Step 3: Check for duplicate email
    existing = repository.get_profile_by_email(db, request.email)
    if existing:
        raise DuplicateError(
            message=f"A profile with email '{request.email}' already exists",
            errors=[f"Duplicate email: {request.email}"],
        )

    # Step 4 & 5: Merge, deduplicate, and normalize
    merged_data = merge_profile_sections(request)

    # Step 6: Generate summary if missing
    if not merged_data.get("summary"):
        merged_data["summary"] = generate_summary(merged_data)

    # Step 7: Calculate completeness
    score = calculate_completeness(merged_data)
    status = get_profile_status(score)

    # Step 8: Create ORM model and persist
    try:
        profile = CandidateProfile(
            id=generate_uuid(),
            name=sanitize_string(merged_data["name"]),
            email=merged_data["email"],
            phone=merged_data.get("phone"),
            location=merged_data.get("location"),
            summary=merged_data.get("summary"),
            skills=merged_data.get("skills", []),
            education=merged_data.get("education", []),
            experience=merged_data.get("experience", []),
            projects=merged_data.get("projects", []),
            certifications=merged_data.get("certifications", []),
            links=merged_data.get("links", {}),
            completeness_score=score,
            profile_status=status,
            resume_version=merged_data.get("resume_version"),
            parser_version=merged_data.get("parser_version"),
            ai_model=merged_data.get("ai_model"),
        )
        profile = repository.create_profile(db, profile)
    except Exception as e:
        logger.error(f"Database error during profile creation | error={str(e)}")
        raise DatabaseError(
            message="Failed to create profile",
            errors=[str(e)],
        )

    # Step 9: Log
    logger.info(
        f"Profile Created | candidate_id={profile.id} | "
        f"completeness={score}% | status={status}"
    )

    # Step 10: Return response
    return _profile_to_response(profile)


def get_profile(db: Session, candidate_id: str) -> ProfileResponse:
    """
    Retrieve a candidate profile by ID.

    Raises:
        ValidationError: If the candidate_id format is invalid.
        NotFoundError: If no profile exists with the given ID.
    """
    if not validate_candidate_id(candidate_id):
        raise ValidationError(
            message="Invalid candidate ID format",
            errors=[f"'{candidate_id}' is not a valid UUID"],
        )

    profile = repository.get_profile(db, candidate_id)
    if not profile:
        raise NotFoundError(
            message=f"Profile not found",
            errors=[f"No profile exists with ID: {candidate_id}"],
        )

    return _profile_to_response(profile)


def update_profile(
    db: Session, candidate_id: str, request: ProfileUpdateRequest
) -> ProfileResponse:
    """
    Update an existing candidate profile.

    Flow:
        1. Validate candidate ID
        2. Fetch existing profile
        3. Apply updates (merge with existing data)
        4. Re-deduplicate sections if changed
        5. Recalculate completeness score
        6. Persist via repository
        7. Log "Profile Updated"

    Raises:
        ValidationError: If the candidate_id or update data is invalid.
        NotFoundError: If no profile exists with the given ID.
        DatabaseError: If the database operation fails.
    """
    if not validate_candidate_id(candidate_id):
        raise ValidationError(
            message="Invalid candidate ID format",
            errors=[f"'{candidate_id}' is not a valid UUID"],
        )

    # Fetch existing profile
    existing = repository.get_profile(db, candidate_id)
    if not existing:
        raise NotFoundError(
            message="Profile not found",
            errors=[f"No profile exists with ID: {candidate_id}"],
        )

    # Build update dict from provided fields only
    update_data: dict = {}
    request_dict = request.model_dump(exclude_none=True)

    if "name" in request_dict:
        update_data["name"] = sanitize_string(request_dict["name"])

    if "email" in request_dict:
        # Check for duplicate email (if changing)
        new_email = request_dict["email"].strip().lower()
        if new_email != existing.email.lower():
            dup = repository.get_profile_by_email(db, new_email)
            if dup:
                raise DuplicateError(
                    message=f"A profile with email '{new_email}' already exists",
                    errors=[f"Duplicate email: {new_email}"],
                )
        update_data["email"] = new_email

    if "phone" in request_dict:
        update_data["phone"] = request_dict["phone"]

    if "location" in request_dict:
        from modules.profile_builder.utils import normalize_location
        update_data["location"] = normalize_location(request_dict["location"])

    if "summary" in request_dict:
        update_data["summary"] = request_dict["summary"]

    if "skills" in request_dict:
        from modules.profile_builder.merge import deduplicate_skills
        update_data["skills"] = deduplicate_skills(request_dict["skills"])

    if "education" in request_dict:
        from modules.profile_builder.merge import merge_education
        from modules.profile_builder.schemas import EducationItem
        edu_items = [EducationItem(**e) if isinstance(e, dict) else e for e in request_dict["education"]]
        update_data["education"] = [e.model_dump() for e in merge_education(edu_items)]

    if "experience" in request_dict:
        from modules.profile_builder.merge import merge_experience
        from modules.profile_builder.schemas import ExperienceItem
        exp_items = [ExperienceItem(**e) if isinstance(e, dict) else e for e in request_dict["experience"]]
        update_data["experience"] = [e.model_dump() for e in merge_experience(exp_items)]

    if "projects" in request_dict:
        from modules.profile_builder.merge import deduplicate_projects
        from modules.profile_builder.schemas import ProjectItem
        proj_items = [ProjectItem(**p) if isinstance(p, dict) else p for p in request_dict["projects"]]
        update_data["projects"] = [p.model_dump() for p in deduplicate_projects(proj_items)]

    if "certifications" in request_dict:
        from modules.profile_builder.merge import deduplicate_certifications
        from modules.profile_builder.schemas import CertificationItem
        cert_items = [CertificationItem(**c) if isinstance(c, dict) else c for c in request_dict["certifications"]]
        update_data["certifications"] = [c.model_dump() for c in deduplicate_certifications(cert_items)]

    if "links" in request_dict:
        links_data = request_dict["links"]
        if hasattr(links_data, "model_dump"):
            update_data["links"] = links_data.model_dump()
        elif isinstance(links_data, dict):
            update_data["links"] = links_data
        # Validate URLs
        from modules.profile_builder.schemas import LinksInfo
        links_obj = LinksInfo(**update_data["links"]) if isinstance(update_data["links"], dict) else links_data
        urls_valid, url_errors = validate_urls(links_obj)
        if not urls_valid:
            raise ValidationError(message="URL validation failed", errors=url_errors)

    if "metadata" in request_dict:
        meta = request_dict["metadata"]
        if isinstance(meta, dict):
            if "resume_version" in meta:
                update_data["resume_version"] = meta["resume_version"]
            if "parser_version" in meta:
                update_data["parser_version"] = meta["parser_version"]
            if "ai_model" in meta:
                update_data["ai_model"] = meta["ai_model"]

    # Update timestamp
    update_data["updated_at"] = datetime.now(timezone.utc)

    # Persist updates
    try:
        updated_profile = repository.update_profile(db, candidate_id, update_data)
    except Exception as e:
        logger.error(f"Database error during profile update | id={candidate_id} | error={str(e)}")
        raise DatabaseError(
            message="Failed to update profile",
            errors=[str(e)],
        )

    if not updated_profile:
        raise NotFoundError(
            message="Profile not found",
            errors=[f"No profile exists with ID: {candidate_id}"],
        )

    # Recalculate completeness after update
    profile_dict = updated_profile.to_dict()
    new_score = calculate_completeness(profile_dict)
    new_status = get_profile_status(new_score)

    # Update completeness fields
    repository.update_profile(
        db,
        candidate_id,
        {
            "completeness_score": new_score,
            "profile_status": new_status,
        },
    )
    updated_profile.completeness_score = new_score
    updated_profile.profile_status = new_status

    logger.info(
        f"Profile Updated | candidate_id={candidate_id} | "
        f"completeness={new_score}% | status={new_status}"
    )

    return _profile_to_response(updated_profile)


def delete_profile(db: Session, candidate_id: str) -> bool:
    """
    Delete a candidate profile.

    Raises:
        ValidationError: If the candidate_id format is invalid.
        NotFoundError: If no profile exists with the given ID.
    """
    if not validate_candidate_id(candidate_id):
        raise ValidationError(
            message="Invalid candidate ID format",
            errors=[f"'{candidate_id}' is not a valid UUID"],
        )

    deleted = repository.delete_profile(db, candidate_id)
    if not deleted:
        raise NotFoundError(
            message="Profile not found",
            errors=[f"No profile exists with ID: {candidate_id}"],
        )

    logger.info(f"Profile Deleted | candidate_id={candidate_id}")
    return True


def search_profiles(
    db: Session, params: ProfileSearchParams
) -> list[ProfileResponse]:
    """
    Search candidate profiles with filters.

    Supported filters: skill, min_experience, location, education.

    Returns:
        List of matching ProfileResponse objects.
    """
    profiles = repository.search_profiles(db, params)
    return [_profile_to_response(p) for p in profiles]
