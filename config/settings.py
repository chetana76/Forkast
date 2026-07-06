import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Google AI Studio (free tier) — used for all model calls + embeddings
    GOOGLE_API_KEY: str = Field(..., env="GOOGLE_API_KEY")
    GOOGLE_GENAI_USE_VERTEXAI: bool = Field(default=False, env="GOOGLE_GENAI_USE_VERTEXAI")

    # Model config
    # Model config — only 2.5 and 3.x series are currently available on free tier.
    # gemini-1.5 and gemini-2.0 are fully shut down as of June 2026.
    PLANNER_MODEL: str = Field(default="gemini-2.5-flash")       # 10 RPM free tier
    INTAKE_MODEL: str = Field(default="gemini-2.5-flash-lite")   # 15 RPM free tier, separate bucket
    INVENTORY_MODEL: str = Field(default="gemini-2.5-flash-lite")
    EVALUATOR_MODEL: str = Field(default="gemini-2.5-flash-lite")
    EMBEDDING_MODEL: str = Field(default="gemini-embedding-001")

    # Local vector store (Chroma) — replaces Vertex AI Vector Search, zero cost
    CHROMA_PERSIST_DIR: str = Field(default="./data/chroma")
    CHROMA_COLLECTION_NAME: str = Field(default="recipes")

    # Local observability — zero-cost replacement for LangSmith-style tracing
    TRACE_LOG_PATH: str = Field(default="./data/traces/trace_log.jsonl")

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

# ADK's internal genai client reads these directly from os.environ — pydantic-settings
# loading .env into this object alone does NOT export them to the process environment.
os.environ.setdefault("GOOGLE_API_KEY", settings.GOOGLE_API_KEY)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", str(settings.GOOGLE_GENAI_USE_VERTEXAI).upper())
