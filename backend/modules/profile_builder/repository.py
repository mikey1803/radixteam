"""Repository Layer for Profile Builder — STUB."""
from app.shared.utils.file_storage import JSONTable


class ProfileRepository:
    def __init__(self):
        self._table = JSONTable("profiles")

    def insert(self, record: dict) -> dict:
        return self._table.insert(record)

    def get(self, profile_id: str) -> dict | None:
        return self._table.get(profile_id)

    def list(self) -> list[dict]:
        return self._table.list()

    def update(self, profile_id: str, record: dict) -> dict | None:
        return self._table.update(profile_id, record)

    def delete(self, profile_id: str) -> bool:
        return self._table.delete(profile_id)
