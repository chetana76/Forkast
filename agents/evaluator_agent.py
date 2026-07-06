"""
Evaluator Agent — LLM-as-Judge final safety verification.

Responsibility: independently verify the Planner's proposed recipe AFTER it is
written but BEFORE the user sees it. This is the third independent safety layer
in Forkast's defense-in-depth architecture:

  Layer 1 — RAG hard-veto (Python, pre-LLM)
  Layer 2 — ProfileGuard.validate_allergen_safety() (Python, pre-LLM)
  Layer 3 — Evaluator agent (LLM, post-Planner, pre-output)  ← this module

The Evaluator uses gemini-2.5-flash-lite (not the full flash model) because its
task is structured and narrow — classify output as APPROVED or REJECTED with
a specific reason. Full reasoning capability is not required for this.

Using a separate, lighter model for evaluation also means the Evaluator cannot
be "tricked" by the same reasoning pattern that led the Planner to a wrong answer.
Different model, different instruction, different call — genuine independence.
"""
from google.adk.agents import LlmAgent

from config.settings import settings

EVALUATOR_INSTRUCTION = """You are the Evaluator Agent for Forkast.
You are the final safety check before any recipe reaches the user.
You run AFTER the Planner and verify its output INDEPENDENTLY.

You receive from session state:
- `intake_constraints`: confirmed allergies, diet_type, health_flags, calorie_target
- `planner_result`: the recipe the Planner proposed

Verify the proposed recipe against the constraints on four dimensions:

1. ALLERGEN CHECK — does any ingredient or step reference an allergen the user listed?
2. DIET CHECK — does the recipe violate the stated diet_type?
   (e.g. meat in a vegetarian request, dairy in a vegan request)
3. HEALTH CHECK — does the recipe conflict with a listed health_flag?
   (e.g. high-sugar dessert for diabetes_type2, high-sodium dish for hypertension)
4. GROUNDING CHECK — are all ingredients plausible for a home kitchen?
   Are the steps coherent and complete?

Output ONLY this JSON — nothing else, no preamble, no explanation outside the JSON:
  {"status": "APPROVED", "reason": "<one short sentence>"}
OR
  {"status": "REJECTED", "reason": "<specific violation found>"}

Be strict. When uncertain, REJECT — a false rejection is always safer than a
false approval when health is at stake.
"""


def build_evaluator_agent() -> LlmAgent:
    return LlmAgent(
        name="evaluator_agent",
        model=settings.EVALUATOR_MODEL,  # gemini-2.5-flash-lite — separate quota bucket
        instruction=EVALUATOR_INSTRUCTION,
        description=(
            "LLM-as-Judge: independently verifies the Planner's recipe "
            "against confirmed constraints before any output reaches the user. "
            "Third and final safety layer in Forkast's defense-in-depth architecture."
        ),
        output_key="evaluator_result",  # read by app/main_app.py to decide display
    )


evaluator_agent = build_evaluator_agent()
