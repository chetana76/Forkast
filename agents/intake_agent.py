"""
Intake Agent — dietary constraint validator.

Responsibility: parse and validate the user's dietary constraints from the
incoming message. This agent is the first in the pipeline and sets the
constraints that all subsequent agents operate under.

Security design: this agent never sees PII. The caller (orchestrator or app)
must run ProfileGuard.guard_agent_input() before constructing the user message.
Intake's instruction explicitly prohibits collecting name, email, or phone.

Output: structured JSON written to session state under 'intake_constraints',
read by the Planner agent downstream.
"""
from google.adk.agents import LlmAgent

from config.settings import settings
from security.profile_guard import ProfileGuard
from security.schemas import UserProfile

INTAKE_INSTRUCTION = """You are the Intake Agent for Forkast — a dietary constraint validator.

Your ONLY job: parse and validate the user's dietary constraints from their message.
These constraints come pre-confirmed from a structured form — do NOT ask the user
to re-confirm or clarify anything.

Rules:
- NEVER collect, store, or repeat name, email, phone, or any PII.
- NEVER suggest recipes or meal plans — that is the Planner's job.
- If a constraint value is missing or invalid (e.g. negative calorie target),
  note it briefly then proceed with a sensible default.
- Output ONLY valid JSON, nothing else:
  {"allergies": [...], "diet_type": "...", "health_flags": [...], "calorie_target": int|null}
"""


def build_intake_agent() -> LlmAgent:
    return LlmAgent(
        name="intake_agent",
        model=settings.INTAKE_MODEL,  # gemini-2.5-flash-lite — structured task, no full reasoning needed
        instruction=INTAKE_INSTRUCTION,
        description="Validates user dietary/health constraints. No PII access. No meal planning.",
        output_key="intake_constraints",  # read by Planner and Evaluator via session state
    )


def finalize_profile(raw_profile: UserProfile) -> dict:
    """
    Convert a raw UserProfile (may contain PII) into the whitelisted dict
    that is safe to inject into any agent's context.

    This is the single entrypoint the app layer calls before any agent sees
    profile data. It runs three operations in sequence:
      1. to_safe_profile() — strips PII fields
      2. model_dump() — serialises to plain dict
      3. enforce_field_whitelist() — removes any non-whitelisted fields

    Returns:
        dict containing only: allergies, diet_type, health_flags, calorie_target
    """
    return ProfileGuard.guard_agent_input(raw_profile)


intake_agent = build_intake_agent()
