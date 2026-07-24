"""Reusable input validators shared across modules."""

from __future__ import annotations

import re
from urllib.parse import urlparse

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_PHONE_RE = re.compile(
    r"^\+?1?\d{7,15}$"
)


def validate_email(email: str) -> bool:
    """Return True if *email* matches a basic RFC-5322 pattern."""
    return bool(_EMAIL_RE.match(email.strip().lower()))


def validate_phone(phone: str) -> bool:
    """Return True if *phone* looks like a valid international number."""
    digits = re.sub(r"[\s\-\(\)]", "", phone)
    return bool(_PHONE_RE.match(digits))


def validate_url(url: str) -> bool:
    """Return True if *url* is a well-formed HTTP(S) URL."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def sanitize_url(url: str) -> str:
    """Strip trailing slashes and whitespace from a URL."""
    return url.strip().rstrip("/")
