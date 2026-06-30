from mcp.server.fastmcp import FastMCP

from mcp_server.tools import get_pantry_items, check_stock

mcp = FastMCP("forkast-pantry")


@mcp.tool()
def get_pantry_items_tool() -> dict:
    """Return all items currently in the pantry, with quantity and expiration date."""
    return get_pantry_items()


@mcp.tool()
def check_stock_tool(item_name: str) -> dict:
    """Check whether a specific item is in stock. Returns quantity and expiration if found."""
    return check_stock(item_name)


if __name__ == "__main__":
    mcp.run(transport="stdio")
