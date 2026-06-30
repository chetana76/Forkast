from typing import Any

from mcp_server.mock_db import db


def get_pantry_items() -> dict[str, Any]:
    """Return all items currently in the pantry."""
    items = db.all_items()
    return {
        "count": len(items),
        "items": items,
    }


def check_stock(item_name: str) -> dict[str, Any]:
    """Check whether a specific item is in stock, with quantity and expiration."""
    item = db.find_item(item_name)
    if item is None:
        return {
            "query": item_name,
            "in_stock": False,
            "item": None,
        }
    return {
        "query": item_name,
        "in_stock": True,
        "item": item,
    }
