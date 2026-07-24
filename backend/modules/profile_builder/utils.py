"""Normalization and sanitisation utilities for profile data."""

from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

from shared.validators import validate_email as _validate_email
from shared.validators import validate_phone as _validate_phone

# ── Degree names ────────────────────────────────────────────────────

_DEGREE_ALIASES: dict[str, str] = {
    "bs": "Bachelor of Science",
    "b.s.": "Bachelor of Science",
    "bsc": "Bachelor of Science",
    "b.sc.": "Bachelor of Science",
    "ba": "Bachelor of Arts",
    "b.a.": "Bachelor of Arts",
    "beng": "Bachelor of Engineering",
    "b.eng.": "Bachelor of Engineering",
    "ms": "Master of Science",
    "m.s.": "Master of Science",
    "msc": "Master of Science",
    "m.sc.": "Master of Science",
    "ma": "Master of Arts",
    "m.a.": "Master of Arts",
    "mba": "Master of Business Administration",
    "meng": "Master of Engineering",
    "m.eng.": "Master of Engineering",
    "phd": "Doctor of Philosophy",
    "ph.d.": "Doctor of Philosophy",
    "dr": "Doctorate",
    "md": "Doctor of Medicine",
    "jd": "Juris Doctor",
    "associate": "Associate Degree",
    "a.s.": "Associate of Science",
    "a.a.": "Associate of Arts",
}


def normalize_degree(degree: str) -> str:
    """Expand common degree abbreviations to their full form."""
    cleaned = degree.strip()
    key = cleaned.lower().rstrip(".")
    # Also try with trailing dots preserved (e.g. "b.s." → "b.s.")
    key_dotted = cleaned.lower()
    if key in _DEGREE_ALIASES:
        return _DEGREE_ALIASES[key]
    if key_dotted in _DEGREE_ALIASES:
        return _DEGREE_ALIASES[key_dotted]
    return cleaned


# ── Location ────────────────────────────────────────────────────────

_LOCATION_ALIASES: dict[str, str] = {
    "sf": "San Francisco, CA",
    "nyc": "New York, NY",
    "la": "Los Angeles, CA",
    "dc": "Washington, DC",
    "uk": "United Kingdom",
    "usa": "United States",
    "us": "United States",
}


def normalize_location(location: str) -> str:
    """Expand common location abbreviations and tidy whitespace."""
    cleaned = re.sub(r"\s+", " ", location.strip())
    key = cleaned.lower()
    if key in _LOCATION_ALIASES:
        return _LOCATION_ALIASES[key]
    return cleaned


# ── URL ─────────────────────────────────────────────────────────────


def normalize_url(url: str) -> str:
    """Canonicalise a URL: lowercase scheme & host, strip trailing slash."""
    try:
        parsed = urlparse(url.strip())
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/") or "/"
        canonical = urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))
        # urlunparse re-adds trailing slash when path="/"; strip it
        if canonical.endswith("/") and path == "/":
            canonical = canonical[:-1]
        return canonical
    except Exception:
        return url.strip().rstrip("/")


# ── Email ───────────────────────────────────────────────────────────


def normalize_email(email: str) -> str:
    """Lowercase and strip whitespace from an email address."""
    return email.strip().lower()


# ── Phone ───────────────────────────────────────────────────────────

_PHONE_STRIP_RE = re.compile(r"[\s\-\(\)\.]+")


def normalize_phone(phone: str) -> str:
    """Strip non-digit chars (except leading +) and normalise phone numbers."""
    stripped = _PHONE_STRIP_RE.sub("", phone)
    if stripped.startswith("+"):
        return "+" + re.sub(r"\D", "", stripped[1:])
    return re.sub(r"\D", "", stripped)


# ── Public validation re-exports ────────────────────────────────────

validate_email = _validate_email
validate_phone = _validate_phone
