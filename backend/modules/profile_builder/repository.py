"""
Profile Builder — Repository Layer.

Pure data access layer — no business logic.
All database operations use SQLAlchemy parameterized queries (SQL injection safe).

Responsibilities:
    - Create Profile
    - Update Profile
    - Delete Profile
    - Fetch Profile
    - Search Profile
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, cast, String

from modules.profile_builder.models import CandidateProfile
from modules.profile_builder.schemas import ProfileSearchParams
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_profile(db: Session, profile: CandidateProfile) -> CandidateProfile:
    """
    Insert a new candidate profile into the database.

    Args:
        db: Database session.
        profile: Populated CandidateProfile ORM instance.

    Returns:
        The persisted CandidateProfile with generated ID and timestamps.
    """
    db.add(profile)
    db.commit()
    db.refresh(profile)
    logger.info(f"Repository: Profile created | id={profile.id}")
    return profile


def get_profile(db: Session, candidate_id: str) -> CandidateProfile | None:
    """
    Fetch a single candidate profile by ID.

    Args:
        db: Database session.
        candidate_id: UUID string of the candidate.

    Returns:
        CandidateProfile if found, None otherwise.
    """
    return (
        db.query(CandidateProfile)
        .filter(CandidateProfile.id == candidate_id)
        .first()
    )


def get_profile_by_email(db: Session, email: str) -> CandidateProfile | None:
    """
    Fetch a candidate profile by email address.

    Used for duplicate detection during profile creation.

    Args:
        db: Database session.
        email: Email address to search for.

    Returns:
        CandidateProfile if found, None otherwise.
    """
    return (
        db.query(CandidateProfile)
        .filter(func.lower(CandidateProfile.email) == email.strip().lower())
        .first()
    )


def update_profile(
    db: Session, candidate_id: str, update_data: dict
) -> CandidateProfile | None:
    """
    Update an existing candidate profile.

    Only updates fields present in update_data.
    Parameterized queries prevent SQL injection.

    Args:
        db: Database session.
        candidate_id: UUID string of the candidate.
        update_data: Dict of fields to update.

    Returns:
        Updated CandidateProfile if found, None otherwise.
    """
    profile = get_profile(db, candidate_id)
    if not profile:
        return None

    for key, value in update_data.items():
        if hasattr(profile, key) and value is not None:
            setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    logger.info(f"Repository: Profile updated | id={candidate_id}")
    return profile


def delete_profile(db: Session, candidate_id: str) -> bool:
    """
    Delete a candidate profile from the database.

    Args:
        db: Database session.
        candidate_id: UUID string of the candidate.

    Returns:
        True if deleted, False if not found.
    """
    profile = get_profile(db, candidate_id)
    if not profile:
        return False

    db.delete(profile)
    db.commit()
    logger.info(f"Repository: Profile deleted | id={candidate_id}")
    return True


def search_profiles(
    db: Session, filters: ProfileSearchParams
) -> list[CandidateProfile]:
    """
    Search candidate profiles with filters.

    Supported filters:
        - skill: Matches profiles containing the skill (case-insensitive)
        - min_experience: Matches profiles with ≥ N experience entries
        - location: Matches profile location (case-insensitive partial match)
        - education: Matches education institution or degree (case-insensitive)

    Future enhancement: Semantic search using embeddings.

    Args:
        db: Database session.
        filters: ProfileSearchParams with optional filter values.

    Returns:
        List of matching CandidateProfile instances.
    """
    query = db.query(CandidateProfile)

    if filters.skill:
        # JSON contains search — works with SQLite and PostgreSQL
        skill_lower = filters.skill.strip().lower()
        query = query.filter(
            func.lower(cast(CandidateProfile.skills, String)).contains(skill_lower)
        )

    if filters.location:
        location_lower = filters.location.strip().lower()
        query = query.filter(
            func.lower(CandidateProfile.location).contains(location_lower)
        )

    if filters.education:
        edu_lower = filters.education.strip().lower()
        query = query.filter(
            func.lower(cast(CandidateProfile.education, String)).contains(edu_lower)
        )

    results = query.all()

    # Post-filter for min_experience (JSON array length)
    if filters.min_experience is not None:
        results = [
            p
            for p in results
            if p.experience and len(p.experience) >= filters.min_experience
        ]

    logger.info(
        f"Repository: Search completed | filters={filters.model_dump(exclude_none=True)} | results={len(results)}"
    )
    return results
