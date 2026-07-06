from google.adk.agents import SequentialAgent

from agents.intake_agent import intake_agent
from agents.inventory_agent import inventory_agent
from agents.planner_agent import planner_agent
from agents.evaluator_agent import evaluator_agent

# Routing here is fixed and deterministic (Intake -> Inventory -> Planner -> Evaluator),
# so a SequentialAgent is used instead of an LLM-routed root agent. This avoids spending
# an extra Gemini call purely on routing decisions — important on the free tier where
# gemini-2.5-flash is capped at a handful of requests per minute.
root_agent = SequentialAgent(
    name="forkast_pipeline",
    sub_agents=[intake_agent, inventory_agent, planner_agent, evaluator_agent],
    description=(
        "Forkast pipeline: Intake validates constraints, Inventory checks pantry via MCP, "
        "Planner retrieves a safe recipe via RAG, Evaluator independently verifies it."
    ),
)
