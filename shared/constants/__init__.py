"""Shared constants used across backend modules."""

from __future__ import annotations

from enum import Enum


class ProfileStatus(str, Enum):
    """Profile completeness status tiers."""

    INCOMPLETE = "incomplete"
    AVERAGE = "average"
    GOOD = "good"
    EXCELLENT = "excellent"


# Completeness thresholds
COMPLETENESS_THRESHOLDS: dict[str, int] = {
    ProfileStatus.INCOMPLETE: 0,
    ProfileStatus.AVERAGE: 41,
    ProfileStatus.GOOD: 71,
    ProfileStatus.EXCELLENT: 91,
}

# Section weights (must sum to 1.0)
PROFILE_SECTION_WEIGHTS: dict[str, float] = {
    "personal_information": 0.20,
    "skills": 0.20,
    "education": 0.15,
    "experience": 0.20,
    "projects": 0.15,
    "certifications": 0.05,
    "links": 0.05,
}
