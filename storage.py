"""Persistent local storage for deduplication state."""
from __future__ import annotations

import json
from pathlib import Path

import config


class SeenStore:
    def __init__(self, file_path: str | None = None) -> None:
        self.file_path = Path(file_path or config.SEEN_ITEMS_FILE)
        self.processed_ids: set[str] = set()

    def load(self) -> None:
        if not self.file_path.exists():
            self.processed_ids = set()
            return
        with self.file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self.processed_ids = set(data.get("processed_ids", []))

    def save(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"processed_ids": sorted(self.processed_ids)}
        with self.file_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def has(self, item_id: str) -> bool:
        return item_id in self.processed_ids

    def add(self, item_id: str) -> None:
        self.processed_ids.add(item_id)