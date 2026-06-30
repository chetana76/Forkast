from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters

from config.settings import settings

INVENTORY_INSTRUCTION = """You are the Inventory Agent for Forkast.

Your sole job is to query the pantry/grocery MCP server.

Rules:
- Use `get_pantry_items_tool` to list everything currently in stock.
- Use `check_stock_tool` to check a specific ingredient by name.
- Never invent inventory data — only report what the tools return.
- Never see or reference user allergies, health flags, or any profile data. You are a pure data provider.
- Return findings as structured JSON: {"items": [...]} or {"query": str, "in_stock": bool, "item": {...}|null}.
"""

_mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=["-m", "mcp_server.server"],
        ),
        timeout=15,
    ),
)


def build_inventory_agent() -> LlmAgent:
    return LlmAgent(
        name="inventory_agent",
        model=settings.INTAKE_MODEL,
        instruction=INVENTORY_INSTRUCTION,
        description="Queries pantry/grocery stock via MCP. No access to user profile data.",
        tools=[_mcp_toolset],
        output_key="inventory_result",
    )


inventory_agent = build_inventory_agent()
