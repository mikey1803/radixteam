"""
Talent Check Repository — STUB.
Reads the company skillset snapshot (talent_check_company_skillsets.json,
per the hackathon brief) and the saved candidate profiles.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.shared.utils.file_storage import JSONTable, DATA_DIR

COMPANY_SNAPSHOT_PATH = DATA_DIR / "talent_check_company_skillsets.json"


class TalentCheckRepository:
    def __init__(self):
        self._results = JSONTable("talent_check_results")

    def get_company_skillsets(self, company: str) -> dict | None:
        if not COMPANY_SNAPSHOT_PATH.exists():
            return None
        with open(COMPANY_SNAPSHOT_PATH) as f:
            data = json.load(f)
        return data.get(company)

    def save_result(self, record: dict) -> dict:
        return self._results.insert(record)
