from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from config.settings import settings
from rag.retriever import retrieve_safe_recipes
from security.schemas import SafeAgentProfile

PLANNER_INSTRUCTION = """You are the Planner Agent for Forkast.

Inputs you receive from the orchestrator's session state:
- `intake_constraints`: confirmed allergies, diet_type, health_flags, restricted_nutrients, calorie_target
- `inventory_result`: pantry items currently in stock

Your job:
1. Build a short retrieval query from the user's request + diet_type + available key ingredients.
2. Call `retrieve_recipes_tool` with that query and the confirmed constraints.
3. From the returned safe candidates only, select the best match for the user's pantry and goals.
4. Output a single recipe as clean markdown with: title, why-it-fits (1-2 lines), ingredients
   (mark which are already in pantry vs. need buying), steps, and approximate calories.

Hard rules:
- NEVER propose a recipe outside `retrieve_recipes_tool`'s safe results.
- NEVER fabricate ingredients or steps not grounded in the retrieved candidate.
- If no safe candidates are returned, say so plainly and ask the user to broaden their request.
"""


def retrieve_recipes_tool(query: str, safe_profile: dict) -> dict:
    """Retrieve allergen-safe recipe candidates for the given query and confirmed profile."""
    profile = SafeAgentProfile(**safe_profile)
    candidates = retrieve_safe_recipes(query=query, safe_profile=profile, top_k=5)
    return {
        "count": len(candidates),
        "candidates": [
            {
                "doc_id": c.doc_id,
                "distance": c.distance,
                "ingredients": c.ingredients,
            }
            for c in candidates
        ],
    }


def build_planner_agent() -> LlmAgent:
    return LlmAgent(
        name="planner_agent",
        model=settings.PLANNER_MODEL,
        instruction=PLANNER_INSTRUCTION,
        description="RAG-based meal planner. Retrieves allergen-safe recipes via Vertex AI Vector Search.",
        tools=[FunctionTool(retrieve_recipes_tool)],
        output_key="planner_result",
    )


planner_agent = build_planner_agent()
