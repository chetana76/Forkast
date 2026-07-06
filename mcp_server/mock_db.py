"""
Pantry data provider — hybrid local + Open Food Facts API.

Strategy:
  1. Try Open Food Facts free API for nutritional data (no key required)
  2. Fall back to local seed data from pantry_seed.json if network is unavailable
  3. Merge: pantry_seed.json defines what is IN STOCK; Open Food Facts enriches
     each item with real nutritional data (calories, protein, carbs, fat)

Open Food Facts API — completely free, no API key:
  https://world.openfoodfacts.org/cgi/search.pl?search_terms={item}&json=1&page_size=1
"""
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("mock_db")

_SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "pantry_seed.json"

# Lightweight local nutrition cache to avoid redundant API calls per session
_nutrition_cache: dict[str, dict] = {}


def _fetch_nutrition_openfoodfacts(item_name: str) -> Optional[dict]:
    """
    Query Open Food Facts for nutritional data on an item.
    Returns a dict with calories, protein, carbs, fat per 100g — or None on failure.
    No API key required. Free tier with no rate limits for reasonable usage.
    """
    try:
        import urllib.request, urllib.parse
        query = urllib.parse.quote(item_name)
        url = (
            f"https://world.openfoodfacts.org/cgi/search.pl"
            f"?search_terms={query}&search_simple=1&action=process"
            f"&json=1&page_size=1&fields=product_name,nutriments"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Forkast/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
        products = data.get("products", [])
        if not products:
            return None
        nutriments = products[0].get("nutriments", {})
        return {
            "calories_per_100g": nutriments.get("energy-kcal_100g"),
            "protein_per_100g": nutriments.get("proteins_100g"),
            "carbs_per_100g": nutriments.get("carbohydrates_100g"),
            "fat_per_100g": nutriments.get("fat_100g"),
            "source": "open_food_facts",
        }
    except Exception as e:
        logger.debug(f"Open Food Facts lookup failed for '{item_name}': {e}")
        return None


def enrich_with_nutrition(item: dict) -> dict:
    """Add nutritional data to a pantry item, using cache to avoid repeat API calls."""
    name = item["item"]
    if name not in _nutrition_cache:
        nutrition = _fetch_nutrition_openfoodfacts(name)
        _nutrition_cache[name] = nutrition or {}
    item_copy = dict(item)
    if _nutrition_cache[name]:
        item_copy["nutrition"] = _nutrition_cache[name]
    return item_copy


class MockPantryDB:
    """
    In-memory pantry store loaded from data/pantry_seed.json.
    Enriches items with real nutritional data from Open Food Facts API
    when available, falling back silently to local-only data.
    """

    def __init__(self, seed_path: Path = _SEED_PATH):
        self._seed_path = seed_path
        self._items: list[dict] = []
        self._load()

    def _load(self) -> None:
        with open(self._seed_path, "r") as f:
            data = json.load(f)
        self._items = data.get("pantry", [])
        logger.info(f"Loaded {len(self._items)} items from {self._seed_path}")

    def all_items(self) -> list[dict]:
        return [enrich_with_nutrition(i) for i in self._items]

    def find_item(self, item_name: str) -> Optional[dict]:
        normalized = item_name.strip().lower()
        for item in self._items:
            if item["item"].lower() == normalized:
                return enrich_with_nutrition(dict(item))
        for item in self._items:
            if normalized in item["item"].lower():
                return enrich_with_nutrition(dict(item))
        return None


db = MockPantryDB()
