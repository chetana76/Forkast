"""
Forkast root orchestrator — SequentialAgent pipeline.

Uses ADK's SequentialAgent rather than an LLM-routed LlmAgent because the
pipeline is fully deterministic: Intake → Inventory → Planner → Evaluator,
every time, without exception. LLM routing would waste one gemini-2.5-flash
call per request just to make a decision that is always the same.

ADK session state is used for inter-agent communication — each agent writes
to its output_key, which the next agent reads from session state automatically.
"""
from google.adk.agents import SequentialAgent

from agents.intake_agent import intake_agent
from agents.inventory_agent import inventory_agent
from agents.planner_agent import planner_agent
from agents.evaluator_agent import evaluator_agent

# SequentialAgent runs sub-agents in declaration order.
# Each agent inherits the session state populated by all previous agents.
root_agent = SequentialAgent(
    name="forkast_pipeline",
    sub_agents=[intake_agent, inventory_agent, planner_agent, evaluator_agent],
    description=(
        "Forkast 4-agent pipeline: "
        "Intake validates constraints → "
        "Inventory checks pantry via MCP → "
        "Planner retrieves safe recipes via RAG → "
        "Evaluator independently verifies before output reaches user."
    ),
)
