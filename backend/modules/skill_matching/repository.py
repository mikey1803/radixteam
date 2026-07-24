"""Skill Matching Repository — STUB. Stores match results."""
from app.shared.utils.file_storage import JSONTable


class SkillMatchRepository:
    def __init__(self):
        self._table = JSONTable("skill_match_results")

    def save_result(self, record: dict) -> dict:
        return self._table.insert(record)
