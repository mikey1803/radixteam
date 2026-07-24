"""
Skill Matching — Candidate Insights.

Deterministic "what does this candidate bring beyond what the JD asked
for" (intelligence design §11): every candidate skill that isn't tied to
any job requirement at all, surfaced grouped by category. This is the
deterministic core of Candidate Insights; an AI-generated narrative on
top (reusing reasoning.py's infrastructure) is a natural additive
extension but deliberately out of scope here, since this milestone
depends only on Milestone 8's output, not Milestone 9's AI layer.

Unmapped candidate skills (no canonical_skill_id — an unknown or emerging
technology, per algorithm doc §9) are still included as bonus content,
just without a confident category: excluding them would understate a
candidate's real extra value just because the taxonomy hasn't caught up
to a skill name yet, which is exactly the kind of silent under-reporting
this module tries to avoid elsewhere.
"""

from pydantic import BaseModel, Field

from ..matching import SkillMatch
from ..models import Candidate, SkillCategory


class BonusSkill(BaseModel):
    skill: str
    category: SkillCategory


class CandidateInsights(BaseModel):
    """Skills the candidate has that go beyond what this specific job asked for."""

    bonus_skills: list[BonusSkill] = Field(default_factory=list)
    bonus_skill_count: int = 0
    categories_represented: list[SkillCategory] = Field(default_factory=list)


def compute_candidate_insights(candidate: Candidate, matches: list[SkillMatch]) -> CandidateInsights:
    """
    `candidate` must be normalized (Milestone 3); `matches` is the output
    of matching this candidate against the job in question (Milestone 4).
    """
    requirement_canonical_ids = {
        match.requirement.canonical_skill_id
        for match in matches
        if match.requirement.canonical_skill_id is not None
    }

    bonus: list[BonusSkill] = []
    seen: set[str] = set()  # dedupe key: canonical_skill_id if known, else lowercased raw text
    for skill in candidate.skills:
        if skill.canonical_skill_id is not None and skill.canonical_skill_id in requirement_canonical_ids:
            continue  # already covered by a requirement -- not "bonus"

        dedupe_key = skill.canonical_skill_id or skill.raw_text.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        bonus.append(BonusSkill(skill=skill.raw_text, category=skill.category or SkillCategory.UNKNOWN))

    categories = sorted({b.category for b in bonus}, key=lambda c: c.value)

    return CandidateInsights(
        bonus_skills=bonus,
        bonus_skill_count=len(bonus),
        categories_represented=categories,
    )
