"""
Profile Builder — Input Validators.

Validates mandatory fields, email format, URL format, and candidate IDs.
Sanitizes strings to prevent injection attacks.
"""

import re
import uuid
import html

from modules.profile_builder.schemas import ProfileCreateRequest, LinksInfo


def validate_profile_data(data: ProfileCreateRequest) -> tuple[bool, list[str]]:
    """
    Validate mandatory profile fields.

    Mandatory:
        - name (non-empty)
        - email (valid format)
        - at least one skill

    Returns:
        (is_valid, list_of_error_messages)
    """
    errors: list[str] = []

    # Name validation
    if not data.name or not data.name.strip():
        errors.append("Missing required field: name")

    # Email validation
    if not data.email or not data.email.strip():
        errors.append("Missing required field: email")
    elif not validate_email(data.email):
        errors.append(f"Invalid email format: {data.email}")

    # Skills validation — at least one required
    if not data.skills or len(data.skills) == 0:
        errors.append("At least one skill is required")

    return (len(errors) == 0, errors)


def validate_email(email: str) -> bool:
    """
    Validate email format using RFC-compliant regex.

    Rejects malformed email addresses per the security checklist.
    """
    if not email:
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def validate_urls(links: LinksInfo | None) -> tuple[bool, list[str]]:
    """
    Validate URL format for profile links.

    Checks linkedin, github, and portfolio URLs if provided.
    """
    if links is None:
        return (True, [])

    errors: list[str] = []
    url_pattern = re.compile(
        r"^https?://"
        r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
        r"[a-zA-Z]{2,}"
        r"(?:/[^\s]*)?$"
    )

    for field_name in ["linkedin", "github", "portfolio"]:
        url = getattr(links, field_name, None)
        if url and not url_pattern.match(url.strip()):
            errors.append(f"Invalid URL format for {field_name}: {url}")

    return (len(errors) == 0, errors)


def validate_candidate_id(candidate_id: str) -> bool:
    """
    Validate that a candidate ID is a valid UUID4 format.

    Prevents invalid ID lookups and potential injection.
    """
    try:
        val = uuid.UUID(candidate_id, version=4)
        return str(val) == candidate_id
    except (ValueError, AttributeError):
        return False


def sanitize_string(value: str) -> str:
    """
    Sanitize a string input.

    - Strips leading/trailing whitespace
    - Escapes HTML entities to prevent XSS
    - Removes null bytes
    """
    if not value:
        return ""

    value = value.strip()
    value = value.replace("\x00", "")
    value = html.escape(value)
    return value
