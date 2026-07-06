"""
Tests for MCP pantry server tool implementations.
Verifies get_pantry_items() and check_stock() return correct structured data.

Run with: pytest tests/test_mcp_tools.py -v
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp_server.tools import get_pantry_items, check_stock


class TestGetPantryItems:

    def test_returns_dict_with_count(self):
        """get_pantry_items must return a dict with 'count' key."""
        result = get_pantry_items()
        assert isinstance(result, dict)
        assert "count" in result

    def test_returns_items_list(self):
        """get_pantry_items must return a non-empty items list."""
        result = get_pantry_items()
        assert "items" in result
        assert isinstance(result["items"], list)
        assert len(result["items"]) > 0

    def test_each_item_has_required_fields(self):
        """Every pantry item must have item, quantity, unit, expiration_date fields."""
        result = get_pantry_items()
        for item in result["items"]:
            assert "item" in item
            assert "quantity" in item
            assert "unit" in item
            assert "expiration_date" in item


class TestCheckStock:

    def test_found_item_returns_in_stock_true(self):
        """check_stock on an existing item must return in_stock=True."""
        result = check_stock("eggs")
        assert result["in_stock"] is True
        assert result["item"] is not None

    def test_missing_item_returns_in_stock_false(self):
        """check_stock on a non-existent item must return in_stock=False."""
        result = check_stock("truffle oil")
        assert result["in_stock"] is False
        assert result["item"] is None

    def test_case_insensitive_match(self):
        """check_stock must match regardless of case."""
        result = check_stock("EGGS")
        assert result["in_stock"] is True

    def test_query_field_echoed(self):
        """check_stock must echo back the original query string."""
        result = check_stock("garlic")
        assert result["query"] == "garlic"

    def test_partial_name_match(self):
        """check_stock must match partial item names."""
        result = check_stock("chicken")
        assert result["in_stock"] is True
