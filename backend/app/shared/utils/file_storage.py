"""
Local JSON-file storage helper.

Per the hackathon brief: "we're using local files today rather than live
Supabase." This gives every module a tiny repository-style API
(insert/get/update/delete/list) backed by a JSON file per table, so the
Repository Pattern (Chapter 2.7) still holds and swapping this for a real
Supabase/Postgres repository later is a drop-in replacement — service layers
never touch this file directly, they only import from it via their own
module's repository.py.
"""
from __future__ import annotations

import json
import os
import threading
import uuid
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[3] / "db" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()


class JSONTable:
    """A single JSON file acting as one 'table'."""

    def __init__(self, table_name: str):
        self.path = DATA_DIR / f"{table_name}.json"
        if not self.path.exists():
            self._write({})

    def _read(self) -> dict:
        with _lock:
            if not self.path.exists():
                return {}
            with open(self.path, "r") as f:
                content = f.read().strip()
                return json.loads(content) if content else {}

    def _write(self, data: dict) -> None:
        with _lock:
            with open(self.path, "w") as f:
                json.dump(data, f, indent=2, default=str)

    def insert(self, record: dict, record_id: str | None = None) -> dict:
        data = self._read()
        record_id = record_id or str(uuid.uuid4())
        record = {**record, "id": record_id}
        data[record_id] = record
        self._write(data)
        return record

    def get(self, record_id: str) -> dict | None:
        return self._read().get(record_id)

    def list(self) -> list[dict]:
        return list(self._read().values())

    def update(self, record_id: str, record: dict) -> dict | None:
        data = self._read()
        if record_id not in data:
            return None
        record = {**record, "id": record_id}
        data[record_id] = record
        self._write(data)
        return record

    def delete(self, record_id: str) -> bool:
        data = self._read()
        if record_id not in data:
            return False
        del data[record_id]
        self._write(data)
        return True
