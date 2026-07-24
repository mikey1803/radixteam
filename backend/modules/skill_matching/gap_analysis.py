"""
Skill Matching — Gap Analysis Engine.

Deterministic gap severity classification (algorithm design §6): every
requirement NOT resolved as an EXACT match is a real gap worth surfacing
to a recruiter, categorized Critical / Moderate / Low Impact / Nice-to-Have.

Uses confidence.py's UNDAMPENED requirement_confidence as the "how much
mitigating evidence exists" signal — deliberately NOT scoring.py's further-
dampened requirement_score_contribution. The algorithm design is explicit
that adjacent-match evidence should be free to soften gap severity even
though it must stay capped in its score contribution: those are different
questions ("should a recruiter feel better about this gap" vs. "how much
should this move the headline number"), and conflating them would mean
adjacent evidence never meaningfully helps a gap's story even when it
genuinely should.

Filling in the rule table: the algorithm design's original rule table
names "core-technical category" as the qualifying condition for Critical,
using it as the flagship example -- but its own recruiter-reasoning
discussion elsewhere gives "a specific compliance certification" (category
CERTIFICATION_COMPLIANCE, not core-technical) as an equally valid Critical
example. Read literally, the two would conflict; read as intent, both
agree that "required, fundamentally needed, no mitigating evidence" is
what makes a gap Critical, with core-technical as the prototypical case
rather than an exclusive gate. This implementation resolves that by
applying the Critical/Moderate split to every category by default, and
only softening it for categories where "required but structurally
unevidenced" is genuinely less informative (see
GAP_SEVERITY_SOFTENING_CATEGORIES) — every example given in the design
docs still classifies exactly as documented under this rule table.

Deliberately NOT implemented: the design's "or the skill is
characteristically fast to ramp for this role's seniority" clause for
downgrading Required gaps to Moderate. That would need a real mapping of
which skills are fast-to-learn at which seniority level, which doesn't
exist and would be pure invention to fabricate now -- an honest scope
decision, not an oversight, consistent with never inventing arbitrary
weights without a documented basis (see constants.py's own discipline).
"""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field

from .confidence import requirement_confidence
from .constants import GAP_MITIGATION_FLOOR, GAP_SEVERITY_SOFTENING_CATEGORIES
from .matching import MatchType, SkillMatch
from .models import CandidateSkill, JobSkillRequirement, RequirementLevel, SkillCategory


class GapSeverity(str, Enum):
    CRITICAL = "critical"
    MODERATE = "moderate"
    LOW_IMPACT = "low_impact"
    NICE_TO_HAVE = "nice_to_have"


class Gap(BaseModel):
    """One unresolved-or-under-matched requirement, classified by severity."""

    requirement: JobSkillRequirement
    match_type: MatchType
    severity: GapSeverity
    mitigating_confidence: float = Field(
        description="The requirement_confidence value that drove this classification -- "
        "0.0 for an unresolved (NONE) requirement."
    )
    matched_via: list[CandidateSkill] = Field(
        default_factory=list,
        description="Candidate skills providing transferable/adjacent evidence, if any.",
    )


def classify_gap_severity(match: SkillMatch, as_of: date) -> GapSeverity:
    """
    Classify one non-exact match into a gap severity tier.

    Only meaningful for match_type in {TRANSFERABLE, ADJACENT, NONE} --
    callers should not invoke this for EXACT matches (analyze_gaps already
    filters them out, since an exact match is not a gap at all).
    """
    confidence = requirement_confidence(match, as_of)
    category = match.requirement.category or SkillCategory.UNKNOWN
    softened = category in GAP_SEVERITY_SOFTENING_CATEGORIES
    mitigated = confidence >= GAP_MITIGATION_FLOOR

    if match.requirement.level == RequirementLevel.REQUIRED:
        if mitigated or softened:
            return GapSeverity.MODERATE
        return GapSeverity.CRITICAL

    # PREFERRED
    if mitigated or softened:
        return GapSeverity.NICE_TO_HAVE
    return GapSeverity.LOW_IMPACT


def analyze_gaps(matches: list[SkillMatch], as_of: date) -> list[Gap]:
    """
    Classify every non-exact match in a full match list into a Gap.

    EXACT matches are fully satisfied and are not gaps -- they're simply
    excluded from the result, not represented as a "no gap" entry.
    """
    gaps: list[Gap] = []
    for match in matches:
        if match.match_type == MatchType.EXACT:
            continue

        gaps.append(
            Gap(
                requirement=match.requirement,
                match_type=match.match_type,
                severity=classify_gap_severity(match, as_of),
                mitigating_confidence=requirement_confidence(match, as_of),
                matched_via=match.matched_candidate_skills,
            )
        )
    return gaps
