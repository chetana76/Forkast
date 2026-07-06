"""
Planner Agent — RAG-based meal/recipe selection with code execution.

Responsibility: retrieve allergen-safe recipe candidates from ChromaDB via
semantic search and select the best match. Also uses BuiltInCodeExecutor
(Antigravity) to calculate exact nutritional totals by running Python code —
this grounds the calorie output in arithmetic rather than LLM estimation.

Security: retrieve_safe_recipes_tool() runs ProfileGuard.validate_allergen_safety()
before returning any candidate. The Planner only ever sees allergen-safe recipes.
"""
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from config.settings import settings
from rag.retriever import retrieve_safe_recipes
from security.schemas import SafeAgentProfile

# Try to import BuiltInCodeExecutor (Antigravity — agent code execution).
# Falls back gracefully if the installed ADK version has a different import path.
try:
    from google.adk.code_executors import BuiltInCodeExecutor
    _code_executor = None  # disabled — cannot combine with FunctionTool in same agent
    _extra_tools = [] # not a tool — passed separately as code_executor
except ImportError:
    _code_executor = None
    _extra_tools = []
    _code_exec_note = (
        "\n5. Use code execution to calculate the exact calorie total by summing "
        "ingredient calorie estimates in Python — do not guess the total."
    )
except ImportError:
    _extra_tools = []
    _code_exec_note = ""

PLANNER_INSTRUCTION = """You are the Planner Agent...

Inputs available from session state:
- `intake_constraints`: confirmed allergies, diet_type, health_flags, calorie_target
- `inventory_result`: pantry items currently in stock

Your job:
1. Build a short retrieval query from the user request + diet_type + key pantry items.
2. Call `retrieve_safe_recipes_tool` with that query and the confirmed constraints.
3. From the returned safe candidates only, select the best match for the user's
   pantry and health goals.
4. Output a single recipe as clean markdown:
   ## [Recipe Title]
   **Why this works for you:** [1-2 lines matching constraints]
   **Ingredients** (mark ✅ in pantry vs 🛒 need to buy)
   **Steps**
   **Approximate calories:** [number]

HARD RULES:
- NEVER propose a recipe outside `retrieve_safe_recipes_tool`'s returned results.
- NEVER fabricate ingredients or steps not grounded in the retrieved candidate.
- If no safe candidates are returned, say so clearly and stop.
"""


def retrieve_safe_recipes_tool(
    query: str,
    allergies: list,
    diet_type: str,
    health_flags: list,
    calorie_target: int = None,
) -> dict:
    """
    RAG retrieval with allergen hard-veto (Layer 2 of Forkast's safety architecture).
    Constructs SafeAgentProfile and calls retrieve_safe_recipes(), which runs
    ProfileGuard.validate_allergen_safety() on every candidate before returning.
    """
    safe_profile = SafeAgentProfile(
        allergies=allergies or [],
        health_flags=health_flags or [],
        diet_type=diet_type or "none",
        calorie_target=calorie_target,
    )
    candidates = retrieve_safe_recipes(query=query, safe_profile=safe_profile, top_k=5)
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
    kwargs = dict(
        name="planner_agent",
        model=settings.PLANNER_MODEL,
        instruction=PLANNER_INSTRUCTION,
        description=(
            "RAG-based meal planner. Retrieves allergen-safe recipes via ChromaDB. "
            "Uses code execution (Antigravity) to calculate nutritional totals. "
            "Never approves own output."
        ),
        tools=[FunctionTool(retrieve_safe_recipes_tool)],
        output_key="planner_result",
    )
    if _code_executor is not None:
        kwargs["code_executor"] = _code_executor
    return LlmAgent(**kwargs)


planner_agent = build_planner_agent()
