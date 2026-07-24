"""
Talent Check Service — STUB with real scoring logic wired in for Role 4.

Design decision made here (per the brief: "decide early what 'ready' means
numerically — that's a design decision"): a category counts as a gap if
candidate_level < required_level. readiness_score = percentage of the 12
categories with no gap.

Role 4 owner: swap `_infer_candidate_level` for something better than "does
the candidate have >=1 skill in this category" if you have time — this stub
version is intentionally simple so it's easy to improve.
"""
from __future__ import annotations

from app.shared.exceptions import NotFoundErrorApp
from app.shared.constants import CATEGORY_CODES
from .repository import TalentCheckRepository


class TalentCheckService:
    def __init__(self, repository: TalentCheckRepository | None = None):
        self.repository = repository or TalentCheckRepository()

    def run_talent_check(self, profile: dict, company: str) -> dict:
        company_bar = self.repository.get_company_skillsets(company)
        if company_bar is None:
            # No snapshot yet (facilitator hasn't handed out the JSON) —
            # fall back to a flat default bar so the button still works.
            company_bar = {code: 6 for code in CATEGORY_CODES if code != "OTHER"}

        candidate_categories = {
            s["category_code"] for s in profile.get("skills", [])
        }

        gap_items = []
        gaps = 0
        total = 0
        for category_code, required_level in company_bar.items():
            if category_code not in CATEGORY_CODES:
                continue
            total += 1
            candidate_level = 8 if category_code in candidate_categories else 2
            is_gap = candidate_level < required_level
            if is_gap:
                gaps += 1
            gap_items.append({
                "category_code": category_code,
                "required_level": required_level,
                "candidate_level": candidate_level,
                "gap": is_gap,
            })

        readiness_score = round(((total - gaps) / total) * 100) if total else 0

        result = {
            "company": company,
            "skillset_gap": gap_items,
            "readiness_score": readiness_score,
        }
        self.repository.save_result(result)
        return result
