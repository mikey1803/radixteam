"""Repository Layer for Resume Parser — STUB. Insert/Get/List/Delete only."""
from app.shared.utils.file_storage import JSONTable


class ResumeRepository:
    def __init__(self):
        self._table = JSONTable("resumes")

    def insert(self, record: dict) -> dict:
        return self._table.insert(record)

    def get(self, resume_id: str) -> dict | None:
        return self._table.get(resume_id)

    def list(self) -> list[dict]:
        return self._table.list()

    def delete(self, resume_id: str) -> bool:
        return self._table.delete(resume_id)
