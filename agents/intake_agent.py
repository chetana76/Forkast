from google.adk.agents import LlmAgent

from config.settings import settings
from security.profile_guard import ProfileGuard
from security.schemas import UserProfile

INTAKE_INSTRUCTION = """You are the Intake Agent for Forkast.

Your sole job is to collect and confirm the user's dietary constraints:
allergies, health conditions, diet type, and calorie target.

Rules:
- Never ask for or store name, email, phone, or any other PII.
- Confirm allergens explicitly with the user before finalizing (e.g. "Confirming: peanut allergy, severe — correct?").
- Once constraints are confirmed, output them as structured JSON only, matching this shape:
  {"allergies": [...], "diet_type": "...", "health_flags": [...], "calorie_target": int|null}
- Do not generate recipes, meal plans, or pantry queries. Hand off once constraints are confirmed.
"""


def build_intake_agent() -> LlmAgent:
    return LlmAgent(
        name="intake_agent",
        model=settings.INTAKE_MODEL,
        instruction=INTAKE_INSTRUCTION,
        description="Collects and validates user dietary/health constraints. No PII, no meal planning.",
        output_key="intake_constraints",
    )


def finalize_profile(raw_profile: UserProfile) -> dict:
    """Run the confirmed UserProfile through ProfileGuard before any agent sees it."""
    return ProfileGuard.guard_agent_input(raw_profile)


intake_agent = build_intake_agent()
