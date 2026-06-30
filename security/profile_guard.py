import re
import logging
from typing import Any

from security.schemas import UserProfile, SafeAgentProfile
from config.settings import settings

logger = logging.getLogger("profile_guard")

_PII_FIELDS = {"name", "email", "phone", "address", "ssn", "date_of_birth", "dob"}
_PII_PATTERNS = [
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),                 # email
    re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"),         # SSN-like
    re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\d{10}\b"),          # phone
]


class ProfileGuardError(Exception):
    pass


class ProfileGuard:
    """
    Hard boundary between raw UserProfile (PII + health data) and
    anything an LLM agent or prompt can access. Agents NEVER receive
    a UserProfile object directly — only a SafeAgentProfile.
    """

    @staticmethod
    def to_safe_profile(profile: UserProfile) -> SafeAgentProfile:
        return SafeAgentProfile(
            allergies=[a.allergen for a in profile.allergies],
            severities={a.allergen: a.severity for a in profile.allergies},
            health_flags=[h.condition for h in profile.health_flags if h.is_active],
            restricted_nutrients=sorted({
                n for h in profile.health_flags if h.is_active
                for n in h.restricted_nutrients
            }),
            diet_type=profile.diet_type,
            calorie_target=profile.calorie_target,
        )

    @staticmethod
    def scrub_pii(text: str) -> str:
        if not settings.PII_REDACTION_ENABLED:
            return text
        for pattern in _PII_PATTERNS:
            text = pattern.sub("[REDACTED]", text)
        return text

    @staticmethod
    def assert_no_pii_keys(payload: dict[str, Any]) -> None:
        leaked = _PII_FIELDS.intersection(k.lower() for k in payload.keys())
        if leaked:
            logger.warning(f"PII field leak attempt blocked: {leaked}")
            raise ProfileGuardError(f"Blocked PII fields in agent payload: {leaked}")

    @staticmethod
    def validate_allergen_safety(recipe_ingredients: list[str], safe_profile: SafeAgentProfile) -> tuple[bool, list[str]]:
        """Hard veto — used post-RAG-retrieval to block unsafe recipes before they reach the user."""
        normalized = [i.strip().lower() for i in recipe_ingredients]
        violations = [
            allergen for allergen in safe_profile.allergies
            if any(allergen in ing for ing in normalized)
        ]
        return (len(violations) == 0, violations)

    @staticmethod
    def enforce_field_whitelist(payload: dict[str, Any]) -> dict[str, Any]:
        """Strip any field not explicitly whitelisted before injecting into agent context/prompt."""
        ProfileGuard.assert_no_pii_keys(payload)
        return {
            k: v for k, v in payload.items()
            if k in settings.ALLOWED_PROFILE_FIELDS_FOR_AGENTS
        }

    @classmethod
    def guard_agent_input(cls, profile: UserProfile) -> dict[str, Any]:
        """Single entrypoint orchestrator.py should call before building any agent prompt/context."""
        safe = cls.to_safe_profile(profile)
        payload = safe.model_dump()
        return cls.enforce_field_whitelist(payload)
