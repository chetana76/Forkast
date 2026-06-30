from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    ANAPHYLACTIC = "anaphylactic"


class Allergy(BaseModel):
    allergen: str
    severity: Severity
    notes: Optional[str] = None

    @field_validator("allergen")
    @classmethod
    def normalize_allergen(cls, v: str) -> str:
        return v.strip().lower()


class HealthFlag(BaseModel):
    condition: str  # e.g. "diabetes_type2", "hypertension", "ckd_stage3"
    is_active: bool = True
    restricted_nutrients: list[str] = Field(default_factory=list)  # e.g. ["sodium","sugar"]

    @field_validator("condition")
    @classmethod
    def normalize_condition(cls, v: str) -> str:
        return v.strip().lower()


class DietType(str, Enum):
    NONE = "none"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    KETO = "keto"
    HALAL = "halal"
    KOSHER = "kosher"
    GLUTEN_FREE = "gluten_free"


class UserProfile(BaseModel):
    user_id: str
    name: Optional[str] = None          # PII — never forwarded to agents
    email: Optional[str] = None         # PII — never forwarded to agents
    allergies: list[Allergy] = Field(default_factory=list)
    health_flags: list[HealthFlag] = Field(default_factory=list)
    diet_type: DietType = DietType.NONE
    calorie_target: Optional[int] = None

    class Config:
        frozen = True  # immutable once constructed


class SafeAgentProfile(BaseModel):
    """Redacted profile view — the ONLY shape agents are allowed to see."""
    allergies: list[str]
    severities: dict[str, Severity]
    health_flags: list[str]
    restricted_nutrients: list[str]
    diet_type: DietType
    calorie_target: Optional[int] = None
