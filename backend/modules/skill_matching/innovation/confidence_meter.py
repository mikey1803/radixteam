"""
Skill Matching — Confidence Meter.

A presentation layer over the four-tier confidence chain already computed
in confidence.py (Milestones 5-8) — Evidence, Skill, Requirement, and
Overall confidence. Computes nothing new; this file exists purely to
package what's already trustworthy into one glanceable summary, exactly
what the intelligence design calls for: "one number that says how much
you should trust this score," reinforcing explainability without adding
a new computation to audit.

`weakest_requirement` deliberately excludes unmatched (NONE) requirements
— those are already the dedicated subject of gap_analysis.py's output,
and the global minimum confidence would almost always just be "the gap
with the least evidence," which would be redundant filler here. Excluding
them surfaces a more useful, distinct signal instead: among the
requirements that DID resolve to some match, which one is least trustworthy.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from ..confidence import requirement_confidence
from ..matching import MatchType, SkillMatch
from ..recommendation import Recommendation


class RequirementConfidenceEntry(BaseModel):
    skill: str
    match_type: str
    confidence: float


class ConfidenceMeter(BaseModel):
    """One glanceable summary of how much to trust this match result."""

    overall_confidence: float
    overall_confidence_label: str
    per_requirement: list[RequirementConfidenceEntry] = Field(default_factory=list)
    weakest_requirement: Optional[RequirementConfidenceEntry] = None


def compute_confidence_meter(
    matches: list[SkillMatch], recommendation: Recommendation, as_of: date
) -> ConfidenceMeter:
    """
    Repackages already-computed confidence values — never recomputes
    overall_confidence or any per-requirement value, only presents them.
    """
    entries = [
        RequirementConfidenceEntry(
            skill=match.requirement.raw_text,
            match_type=match.match_type.value,
            confidence=requirement_confidence(match, as_of),
        )
        for match in matches
    ]

    matched_entries = [e for e in entries if e.match_type != MatchType.NONE.value]
    weakest = min(matched_entries, key=lambda e: e.confidence) if matched_entries else None

    return ConfidenceMeter(
        overall_confidence=recommendation.overall_confidence,
        overall_confidence_label=recommendation.confidence_label.value,
        per_requirement=entries,
        weakest_requirement=weakest,
    )
