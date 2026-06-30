from google.adk.agents import LlmAgent

from config.settings import settings
from agents.intake_agent import intake_agent
from agents.inventory_agent import inventory_agent
from agents.planner_agent import planner_agent

ORCHESTRATOR_INSTRUCTION = """You are the root orchestrator for Forkast, an AI meal advisor.

You route the conversation between three specialist sub-agents. You never answer
nutrition, allergy, or recipe questions yourself — always delegate.

Routing rules:
1. If the user's dietary constraints (allergies, diet type, health flags, calorie target)
   are not yet confirmed for this session, delegate to `intake_agent` first.
2. Once constraints are confirmed, if the user asks what's available or you need pantry
   data to plan meals, delegate to `inventory_agent`.
3. Once both constraints and pantry data are available, delegate to `planner_agent` to
   produce recipe/meal suggestions.
4. Never let `inventory_agent` see user profile data, and never let `intake_agent` or
   `inventory_agent` generate meal suggestions — that is `planner_agent`'s job only.
5. If a sub-agent's output is incomplete or ambiguous, re-delegate to the same agent
   rather than guessing on its behalf.

Maintain strict separation of concerns. Each sub-agent owns exactly one responsibility.
"""


def build_orchestrator() -> LlmAgent:
    return LlmAgent(
        name="forkast_orchestrator",
        model=settings.ORCHESTRATOR_MODEL,
        instruction=ORCHESTRATOR_INSTRUCTION,
        description="Root router coordinating Intake, Inventory, and Planner agents.",
        sub_agents=[intake_agent, inventory_agent, planner_agent],
    )


root_agent = build_orchestrator()
