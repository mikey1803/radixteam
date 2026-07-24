"""
Repository Layer — per Chapter 2.9 / 4.15.
ONLY Insert / Update / Delete / Fetch. No business logic here, ever.
"""
from __future__ import annotations

from app.shared.utils.file_storage import JSONTable


class JobRepository:
    def __init__(self):
        self._table = JSONTable("jobs")

    def insert(self, record: dict) -> dict:
        return self._table.insert(record)

    def get(self, job_id: str) -> dict | None:
        return self._table.get(job_id)

    def list(self) -> list[dict]:
        return self._table.list()

    def delete(self, job_id: str) -> bool:
        return self._table.delete(job_id)
