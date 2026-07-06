from google.adk.agents import LlmAgent

from config.settings import settings
from security.profile_guard import ProfileGuard
from security.schemas import UserProfile

INTAKE_INSTRUCTION = """You are the Intake Agent for Forkast.

Your sole job is to validate the user's dietary constraints: allergies, health
conditions, diet type, and calorie target. These arrive already explicitly
confirmed by the user via a structured form — do NOT ask the user to
re-confirm them in conversation. Treat the values given in the message as final.

Rules:
- Never ask for or store name, email, phone, or any other PII.
- Validate the values are sensible (e.g. calorie target > 0). If something is
  clearly malformed, note it briefly, otherwise proceed immediately.
- Output the constraints as structured JSON only, matching this shape:
  {"allergies": [...], "diet_type": "...", "health_flags": [...], "calorie_target": int|null}
- Do not generate recipes, meal plans, or pantry queries. Hand off immediately.
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
