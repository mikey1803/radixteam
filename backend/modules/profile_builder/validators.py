"""Validation logic for Candidate Profiles."""

from __future__ import annotations

from shared.logging import get_logger
from shared.validators import validate_email, validate_url

from backend.modules.profile_builder.schemas import (
    ProfileCreate,
    ProfileUpdate,
    ValidationResult,
)

logger = get_logger(__name__)

REQUIRED_FIELDS = {"first_name", "last_name", "email"}
RECOMMENDED_FIELDS = {"summary", "linkedin", "github", "projects"}
OPTIONAL_FIELDS = {"certifications", "portfolio", "achievements"}


def validate_profile_create(payload: ProfileCreate) -> ValidationResult:
    """Validate a profile creation payload against all rules."""
    errors_required: list[str] = []
    errors_recommended: list[str] = []
    warnings: list[str] = []

    # ── Required ────────────────────────────────────────────────────
    if not payload.personal_info.first_name.strip():
        errors_required.append("personal_info.first_name is required")
    if not payload.personal_info.last_name.strip():
        errors_required.append("personal_info.last_name is required")
    if not validate_email(payload.personal_info.email):
        errors_required.append("personal_info.email must be a valid email address")

    if not payload.skills:
        errors_required.append("At least one skill is required")

    # ── Recommended ─────────────────────────────────────────────────
    if not payload.summary:
        errors_recommended.append("summary is recommended")

    has_linkedin = any(
        lnk.label.lower() == "linkedin" for lnk in payload.links
    )
    has_github = any(
        lnk.label.lower() == "github" for lnk in payload.links
    )
    if not has_linkedin:
        errors_recommended.append("LinkedIn link is recommended")
    if not has_github:
        errors_recommended.append("GitHub link is recommended")
    if not payload.projects:
        errors_recommended.append("At least one project is recommended")

    # ── Optional warnings ───────────────────────────────────────────
    if not payload.certifications:
        warnings.append("certifications are optional but improve profile completeness")
    has_portfolio = any(
        lnk.label.lower() == "portfolio" for lnk in payload.links
    )
    if not has_portfolio:
        warnings.append("portfolio link is optional")

    # ── URL validation ──────────────────────────────────────────────
    for lnk in payload.links:
        if not validate_url(lnk.url):
            errors_required.append(f"Invalid URL for link '{lnk.label}': {lnk.url}")

    for proj in payload.projects:
        if proj.url and not validate_url(proj.url):
            errors_required.append(f"Invalid URL for project '{proj.name}': {proj.url}")

    for cert in payload.certifications:
        if cert.url and not validate_url(cert.url):
            errors_required.append(f"Invalid URL for certification '{cert.name}': {cert.url}")

    is_valid = len(errors_required) == 0

    if not is_valid:
        logger.warning(
            "Validation Failed",
            required_errors=errors_required,
            recommended_errors=errors_recommended,
        )

    return ValidationResult(
        is_valid=is_valid,
        required_errors=errors_required,
        recommended_errors=errors_recommended,
        warnings=warnings,
    )


def validate_profile_update(payload: ProfileUpdate) -> ValidationResult:
    """Validate a profile update payload."""
    errors_required: list[str] = []
    errors_recommended: list[str] = []
    warnings: list[str] = []

    if payload.personal_info is not None:
        if not payload.personal_info.first_name.strip():
            errors_required.append("personal_info.first_name cannot be empty")
        if not payload.personal_info.last_name.strip():
            errors_required.append("personal_info.last_name cannot be empty")
        if not validate_email(payload.personal_info.email):
            errors_required.append("personal_info.email must be a valid email address")

    if payload.skills is not None and len(payload.skills) == 0:
        errors_required.append("At least one skill is required")

    if payload.links is not None:
        for lnk in payload.links:
            if not validate_url(lnk.url):
                errors_required.append(f"Invalid URL for link '{lnk.label}': {lnk.url}")

    is_valid = len(errors_required) == 0

    if not is_valid:
        logger.warning(
            "Validation Failed",
            required_errors=errors_required,
        )

    return ValidationResult(
        is_valid=is_valid,
        required_errors=errors_required,
        recommended_errors=errors_recommended,
        warnings=warnings,
    )
