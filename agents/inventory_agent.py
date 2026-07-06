from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters

from config.settings import settings

INVENTORY_INSTRUCTION = """You are the Inventory Agent for Forkast — a pantry data provider.

Your ONLY job: call these two tools EXACTLY as named, then report results:
  1. mcp_get_pantry_items() — call this first to list everything in stock
  2. mcp_check_stock(item_name) — call this to check a specific item

Rules:
- Use ONLY the exact tool names above — never guess, abbreviate, or modify them.
- ONLY report what the tools return — never invent inventory data.
- NEVER see or reference user allergies, health flags, or any profile data.
- Output JSON: {"available_items": [...], "expiring_soon": [...]}
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
        model=settings.INVENTORY_MODEL,
        instruction=INVENTORY_INSTRUCTION,
        description="Queries pantry/grocery stock via MCP. No access to user profile data.",
        tools=[_mcp_toolset],
        output_key="inventory_result",
    )


inventory_agent = build_inventory_agent()
