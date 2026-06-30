import json
from pathlib import Path
from typing import Optional

_SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "pantry_seed.json"


class MockPantryDB:
    """In-memory pantry store loaded from data/pantry_seed.json."""

    def __init__(self, seed_path: Path = _SEED_PATH):
        self._seed_path = seed_path
        self._items: list[dict] = []
        self._load()

    def _load(self) -> None:
        with open(self._seed_path, "r") as f:
            data = json.load(f)
        self._items = data.get("pantry", [])

    def all_items(self) -> list[dict]:
        return list(self._items)

    def find_item(self, item_name: str) -> Optional[dict]:
        normalized = item_name.strip().lower()
        for item in self._items:
            if item["item"].lower() == normalized:
                return dict(item)
        for item in self._items:
            if normalized in item["item"].lower():
                return dict(item)
        return None


db = MockPantryDB()
