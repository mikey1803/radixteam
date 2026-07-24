"""
Skill Matching Service — STUB with real fuzzy-matching logic wired in for Role 5.

Per the brief: "prioritize the gap list over the number." Uses simple
case-insensitive + substring fuzzy matching by default (no AI dependency),
so it works standalone. Role 5 owner can upgrade `_skills_match` to call
AIProvider().complete_json(...) for genuine semantic matching if time allows.
"""
from __future__ import annotations

from difflib import SequenceMatcher

from .repository import SkillMatchRepository


def _skills_match(a: str, b: str, threshold: float = 0.75) -> bool:
    a, b = a.lower().strip(), b.lower().strip()
    if a == b or a in b or b in a:
        return True
    return SequenceMatcher(None, a, b).ratio() >= threshold


class SkillMatchingService:
    def __init__(self, repository: SkillMatchRepository | None = None):
        self.repository = repository or SkillMatchRepository()

    def match(self, candidate_skills: list[dict], jd_skill_list: dict) -> dict:
        candidate_names = [s["skill_name"] for s in candidate_skills]
        jd_names = [s["skill_name"] for s in jd_skill_list.get("skills", [])]

        matched, missing = [], []
        for jd_skill in jd_names:
            if any(_skills_match(jd_skill, c) for c in candidate_names):
                matched.append(jd_skill)
            else:
                missing.append(jd_skill)

        match_score = round((len(matched) / len(jd_names)) * 100) if jd_names else 0

        result = {
            "jd_source_file": jd_skill_list.get("source_file", "unknown"),
            "match_score": match_score,
            "matched_skills": matched,
            "missing_skills": missing,
        }
        self.repository.save_result(result)
        return result
