"""Profile completeness scoring and summary generation."""

from __future__ import annotations

from shared.constants import PROFILE_SECTION_WEIGHTS, ProfileStatus
from shared.logging import get_logger

from backend.modules.profile_builder.schemas import (
    CompletenessResult,
    ProfileCreate,
    ProfileUpdate,
)

logger = get_logger(__name__)

MAX_SUMMARY_WORDS = 150


def _score_personal_info(profile: ProfileCreate) -> float:
    """Score 0-100 for personal information completeness."""
    score = 0.0
    if profile.personal_info.first_name:
        score += 15
    if profile.personal_info.last_name:
        score += 15
    if profile.personal_info.email:
        score += 20
    if profile.personal_info.phone:
        score += 15
    if profile.personal_info.location:
        score += 15
    if profile.personal_info.headline:
        score += 20
    return min(score, 100.0)


def _score_skills(profile: ProfileCreate) -> float:
    """Score skills section. 1 skill = 40, 3+ = 100."""
    count = len(profile.skills)
    if count == 0:
        return 0.0
    if count == 1:
        return 40.0
    if count == 2:
        return 70.0
    if count >= 5:
        return 100.0
    return 80.0


def _score_education(profile: ProfileCreate) -> float:
    """Score education section."""
    count = len(profile.education)
    if count == 0:
        return 0.0
    score = 50.0
    if any(e.degree for e in profile.education):
        score += 30
    if any(e.gpa is not None for e in profile.education):
        score += 20
    return min(score, 100.0)


def _score_experience(profile: ProfileCreate) -> float:
    """Score experience section."""
    count = len(profile.experience)
    if count == 0:
        return 0.0
    if count == 1:
        return 40.0
    if count == 2:
        return 70.0
    if count >= 4:
        return 100.0
    return 85.0


def _score_projects(profile: ProfileCreate) -> float:
    """Score projects section."""
    count = len(profile.projects)
    if count == 0:
        return 0.0
    if count == 1:
        return 50.0
    if count >= 3:
        return 100.0
    return 75.0


def _score_certifications(profile: ProfileCreate) -> float:
    """Score certifications section."""
    count = len(profile.certifications)
    if count == 0:
        return 0.0
    if count >= 2:
        return 100.0
    return 60.0


def _score_links(profile: ProfileCreate) -> float:
    """Score links section."""
    count = len(profile.links)
    if count == 0:
        return 0.0
    if count == 1:
        return 40.0
    if count >= 3:
        return 100.0
    return 70.0


def calculate_completeness(profile: ProfileCreate) -> CompletenessResult:
    """Compute a weighted completeness score for a profile."""
    section_scores: dict[str, float] = {
        "personal_information": _score_personal_info(profile),
        "skills": _score_skills(profile),
        "education": _score_education(profile),
        "experience": _score_experience(profile),
        "projects": _score_projects(profile),
        "certifications": _score_certifications(profile),
        "links": _score_links(profile),
    }

    total = sum(
        section_scores[section] * weight
        for section, weight in PROFILE_SECTION_WEIGHTS.items()
    )
    total = round(min(max(total, 0.0), 100.0), 2)

    status = _score_to_status(total)

    logger.info(
        "Completeness Calculated",
        score=total,
        status=status,
        section_scores=section_scores,
    )

    return CompletenessResult(
        score=total,
        status=status,
        section_scores=section_scores,
    )


def recalculate_from_update(
    existing: ProfileCreate,
    update: ProfileUpdate,
) -> CompletenessResult:
    """Merge an update into existing data, then recalculate."""
    merged = _apply_update(existing, update)
    return calculate_completeness(merged)


def _apply_update(existing: ProfileCreate, update: ProfileUpdate) -> ProfileCreate:
    """Merge update fields into the existing profile data."""
    personal = existing.personal_info
    if update.personal_info is not None:
        personal = update.personal_info

    return ProfileCreate(
        personal_info=personal,
        summary=update.summary if update.summary is not None else existing.summary,
        education=update.education if update.education is not None else existing.education,
        experience=update.experience if update.experience is not None else existing.experience,
        skills=update.skills if update.skills is not None else existing.skills,
        projects=update.projects if update.projects is not None else existing.projects,
        certifications=update.certifications if update.certifications is not None else existing.certifications,
        links=update.links if update.links is not None else existing.links,
        parser_version=existing.parser_version,
        resume_version=existing.resume_version,
        ai_model=existing.ai_model,
    )


def _score_to_status(score: float) -> str:
    """Map a numeric score to a status label."""
    if score >= 91:
        return ProfileStatus.EXCELLENT.value
    if score >= 71:
        return ProfileStatus.GOOD.value
    if score >= 41:
        return ProfileStatus.AVERAGE.value
    return ProfileStatus.INCOMPLETE.value


def generate_summary(profile: ProfileCreate) -> str:
    """Auto-generate a professional summary from available profile data.

    Produces a text of at most ``MAX_SUMMARY_WORDS`` words.
    """
    parts: list[str] = []

    name = f"{profile.personal_info.first_name} {profile.personal_info.last_name}"
    headline = profile.personal_info.headline or "professional"

    parts.append(f"{name} is a {headline}")

    if profile.skills:
        top_skills = [s.name for s in profile.skills[:5]]
        parts.append(f"skilled in {', '.join(top_skills)}")

    if profile.experience:
        latest = profile.experience[0]
        parts.append(f"currently working as {latest.title} at {latest.company}")

    if profile.education:
        latest_edu = profile.education[0]
        degree_info = latest_edu.degree or "a degree"
        field_info = f" in {latest_edu.field_of_study}" if latest_edu.field_of_study else ""
        parts.append(
            f"with {degree_info}{field_info} from {latest_edu.institution}"
        )

    summary = " ".join(parts) + "."

    words = summary.split()
    if len(words) > MAX_SUMMARY_WORDS:
        summary = " ".join(words[: MAX_SUMMARY_WORDS]) + "..."

    return summary
