"""
Security boundary tests for ProfileGuard.

These tests verify that the three-layer allergen safety architecture works correctly:
  Layer 1 — PII stripping via to_safe_profile()
  Layer 2 — Field whitelist via enforce_field_whitelist()
  Layer 3 — Allergen hard-veto via validate_allergen_safety()

Run with: pytest tests/test_security_boundary.py -v
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from security.schemas import (
    UserProfile, SafeAgentProfile, Allergy, HealthFlag, DietType, Severity
)
from security.profile_guard import ProfileGuard, ProfileGuardError


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def full_profile():
    """A UserProfile containing PII and health data — the raw app-level object."""
    return UserProfile(
        user_id="test_001",
        name="Test User",
        email="test@example.com",
        phone="+1-555-123-4567",
        allergies=[
            Allergy(allergen="peanuts", severity=Severity.ANAPHYLACTIC),
            Allergy(allergen="shellfish", severity=Severity.SEVERE),
        ],
        health_flags=[
            HealthFlag(
                condition="diabetes_type2",
                restricted_nutrients=["sugar", "refined_carbs"],
            ),
        ],
        diet_type=DietType.VEGETARIAN,
        calorie_target=1800,
    )


@pytest.fixture
def safe_profile(full_profile):
    """A SafeAgentProfile — the only shape agents may see."""
    return ProfileGuard.to_safe_profile(full_profile)


# ── Layer 1: PII Stripping ────────────────────────────────────────────────────

class TestPIIStripping:

    def test_name_not_in_safe_profile(self, full_profile):
        """Name must be completely absent from the safe profile."""
        safe = ProfileGuard.to_safe_profile(full_profile)
        assert not hasattr(safe, "name") or safe.model_dump().get("name") is None

    def test_email_not_in_safe_profile(self, full_profile):
        """Email must be completely absent from the safe profile."""
        safe = ProfileGuard.to_safe_profile(full_profile)
        safe_dict = safe.model_dump()
        assert "email" not in safe_dict or safe_dict.get("email") is None

    def test_phone_not_in_safe_profile(self, full_profile):
        """Phone number must be completely absent from the safe profile."""
        safe = ProfileGuard.to_safe_profile(full_profile)
        safe_dict = safe.model_dump()
        assert "phone" not in safe_dict or safe_dict.get("phone") is None

    def test_user_id_not_in_safe_profile(self, full_profile):
        """User ID must not appear in the safe profile."""
        safe = ProfileGuard.to_safe_profile(full_profile)
        safe_dict = safe.model_dump()
        assert "user_id" not in safe_dict

    def test_allergens_preserved_in_safe_profile(self, full_profile):
        """Allergens must be preserved after PII stripping."""
        safe = ProfileGuard.to_safe_profile(full_profile)
        assert "peanuts" in safe.allergies
        assert "shellfish" in safe.allergies

    def test_diet_type_preserved(self, full_profile):
        """Diet type must be preserved after stripping."""
        safe = ProfileGuard.to_safe_profile(full_profile)
        assert safe.diet_type == DietType.VEGETARIAN

    def test_calorie_target_preserved(self, full_profile):
        """Calorie target must be preserved after stripping."""
        safe = ProfileGuard.to_safe_profile(full_profile)
        assert safe.calorie_target == 1800

    def test_scrub_pii_removes_email(self):
        """scrub_pii must redact email addresses from arbitrary text."""
        text = "User email is test@example.com please help"
        result = ProfileGuard.scrub_pii(text)
        assert "test@example.com" not in result
        assert "[REDACTED]" in result

    def test_scrub_pii_removes_phone(self):
        """scrub_pii must redact phone-like patterns."""
        text = "Call me at 5551234567 for results"
        result = ProfileGuard.scrub_pii(text)
        assert "5551234567" not in result


# ── Layer 2: Field Whitelist ──────────────────────────────────────────────────

class TestFieldWhitelist:

    def test_whitelisted_fields_pass_through(self, full_profile):
        """Only the four whitelisted fields should appear in agent payload."""
        payload = ProfileGuard.guard_agent_input(full_profile)
        allowed = {"allergies", "diet_type", "health_flags", "calorie_target"}
        assert set(payload.keys()).issubset(allowed)

    def test_pii_keys_raise_error(self):
        """Any payload with PII keys must raise ProfileGuardError immediately."""
        bad_payload = {
            "name": "Test User",
            "allergies": ["peanuts"],
            "diet_type": "vegetarian",
        }
        with pytest.raises(ProfileGuardError):
            ProfileGuard.assert_no_pii_keys(bad_payload)

    def test_email_key_raises_error(self):
        """Email key specifically must trigger ProfileGuardError."""
        with pytest.raises(ProfileGuardError):
            ProfileGuard.assert_no_pii_keys({"email": "x@y.com", "allergies": []})

    def test_clean_payload_passes_whitelist(self):
        """A clean payload with only allowed fields must pass silently."""
        clean = {"allergies": ["peanuts"], "diet_type": "vegetarian", "calorie_target": 1800}
        result = ProfileGuard.enforce_field_whitelist(clean)
        assert result == clean


# ── Layer 3: Allergen Hard-Veto ───────────────────────────────────────────────

class TestAllergenHardVeto:

    def test_recipe_with_allergen_blocked(self, safe_profile):
        """A recipe containing a user allergen must be blocked — is_safe=False."""
        ingredients = ["pasta", "peanut sauce", "garlic", "basil"]
        is_safe, violations = ProfileGuard.validate_allergen_safety(ingredients, safe_profile)
        assert not is_safe
        assert "peanuts" in violations

    def test_shellfish_recipe_blocked(self, safe_profile):
        """Shellfish allergy must block any recipe containing shrimp/crab/lobster."""
        ingredients = ["shrimp", "garlic", "lemon", "olive oil"]
        is_safe, violations = ProfileGuard.validate_allergen_safety(ingredients, safe_profile)
        assert not is_safe
        assert "shellfish" in violations

    def test_safe_recipe_passes(self, safe_profile):
        """A recipe with no allergens must pass the veto — is_safe=True."""
        ingredients = ["chickpeas", "spinach", "tomatoes", "garlic", "cumin"]
        is_safe, violations = ProfileGuard.validate_allergen_safety(ingredients, safe_profile)
        assert is_safe
        assert violations == []

    def test_another_safe_recipe_passes(self, safe_profile):
        """A second safe recipe must also pass."""
        ingredients = ["eggs", "bell peppers", "onions", "spinach", "olive oil"]
        is_safe, violations = ProfileGuard.validate_allergen_safety(ingredients, safe_profile)
        assert is_safe

    def test_partial_allergen_match_blocked(self, safe_profile):
        """Substring allergen match must also be caught (e.g. 'peanut oil' contains 'peanut')."""
        ingredients = ["peanut oil", "garlic", "soy sauce"]
        is_safe, violations = ProfileGuard.validate_allergen_safety(ingredients, safe_profile)
        assert not is_safe

    def test_empty_profile_allows_everything(self):
        """A profile with no allergies must allow all recipes."""
        empty_profile = SafeAgentProfile(
            allergies=[], diet_type=DietType.NONE, calorie_target=None
        )
        ingredients = ["peanuts", "shellfish", "eggs", "milk"]
        is_safe, violations = ProfileGuard.validate_allergen_safety(ingredients, empty_profile)
        assert is_safe
        assert violations == []

    def test_multiple_violations_all_reported(self, safe_profile):
        """All violated allergens must appear in the violations list."""
        ingredients = ["peanut butter", "shrimp paste", "garlic"]
        is_safe, violations = ProfileGuard.validate_allergen_safety(ingredients, safe_profile)
        assert not is_safe
        assert len(violations) == 2
