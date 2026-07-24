"""
Skill normalization — per Chapter 4.12.
"JS" / "Javascript" / "Java Script" -> "JavaScript", etc.
"""
from __future__ import annotations

from app.shared.constants import CATEGORY_CODES, SKILL_MAPPING


def normalize_skill_name(name: str) -> str:
    key = name.strip().lower()
    return SKILL_MAPPING.get(key, name.strip())


def normalize_category(category_code: str) -> str:
    code = (category_code or "OTHER").strip().upper()
    return code if code in CATEGORY_CODES else "OTHER"


def normalize_ai_skills(raw_skills: list[dict]) -> list[dict]:
    normalized = []
    seen = set()
    for s in raw_skills:
        name = normalize_skill_name(s.get("skill_name", ""))
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue  # de-dupe, per Chapter 4.24 "no duplicate skill names"
        seen.add(key)
        normalized.append({
            "skill_name": name,
            "category_code": normalize_category(s.get("category_code", "OTHER")),
            "evidence": s.get("evidence", ""),
            "confidence": s.get("confidence", "medium")
            if s.get("confidence") in ("high", "medium", "low") else "medium",
        })
    return normalized
