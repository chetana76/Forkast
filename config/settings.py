import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Google Cloud / Vertex AI
    GOOGLE_CLOUD_PROJECT: str = Field(..., env="GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_LOCATION: str = Field(default="us-central1", env="GOOGLE_CLOUD_LOCATION")
    GOOGLE_GENAI_USE_VERTEXAI: bool = Field(default=True, env="GOOGLE_GENAI_USE_VERTEXAI")

    # Model config
    ORCHESTRATOR_MODEL: str = Field(default="gemini-2.0-flash-001")
    PLANNER_MODEL: str = Field(default="gemini-2.0-flash-001")
    INTAKE_MODEL: str = Field(default="gemini-2.0-flash-001")
    EMBEDDING_MODEL: str = Field(default="text-embedding-005")

    # Vertex AI Vector Search
    VECTOR_INDEX_ID: str = Field(..., env="VECTOR_INDEX_ID")
    VECTOR_ENDPOINT_ID: str = Field(..., env="VECTOR_ENDPOINT_ID")
    VECTOR_DEPLOYED_INDEX_ID: str = Field(..., env="VECTOR_DEPLOYED_INDEX_ID")

    # MCP Server
    MCP_SERVER_HOST: str = Field(default="127.0.0.1")
    MCP_SERVER_PORT: int = Field(default=8765)
    MCP_SERVER_URL: str = Field(default="http://127.0.0.1:8765")

    # Security
    PII_REDACTION_ENABLED: bool = Field(default=True)
    ALLOWED_PROFILE_FIELDS_FOR_AGENTS: list[str] = Field(
        default=["allergies", "diet_type", "health_flags", "calorie_target"]
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
