"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


# Find .env file - check multiple locations
def find_env_file() -> str:
    """Find .env file in current dir or parent dirs."""
    import os

    candidates = []

    # Current working directory
    cwd = Path.cwd()
    candidates.append(cwd / ".env")

    # Project root (2 levels up from app/backend when running from there)
    candidates.append((cwd / ".." / ".." / ".env").resolve())

    # Based on this file's location
    # __file__ is in app/backend/src/research_agent/config.py
    this_file = Path(__file__).resolve()
    # Go up: config.py -> research_agent -> src -> backend -> app -> project_root
    project_root = this_file.parent.parent.parent.parent.parent
    candidates.append(project_root / ".env")
    candidates.append(project_root / "app" / "backend" / ".env")

    # Check each candidate
    for candidate in candidates:
        if candidate.exists():
            return str(candidate.resolve())

    # Fallback - return first candidate path for error message
    return str(candidates[0])


_env_file_path = find_env_file()
_env_file_exists = Path(_env_file_path).exists()
if _env_file_exists:
    print(f"[Config] Loading .env from: {_env_file_path}")
else:
    # This is normal in production - Zeabur/Docker uses environment variables directly
    print(f"[Config] No .env file found (using environment variables instead)")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=_env_file_path,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
    )

    # Database
    database_url: str = (
        "postgresql+asyncpg://research_rag:research_rag_dev@localhost:5432/research_rag"
    )

    @property
    def async_database_url(self) -> str:
        """Ensure database URL uses asyncpg driver and compatible SSL params."""
        url = self.database_url
        # Convert postgresql:// to postgresql+asyncpg://
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        # Convert postgres:// to postgresql+asyncpg://
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)

        # Remove parameters that asyncpg doesn't understand
        # - sslmode: asyncpg handles SSL via connect_args
        # - pgbouncer: Prisma-specific parameter
        # - connect_timeout: handled differently in asyncpg
        import re

        url = re.sub(r"[?&]sslmode=[^&]*", "", url)
        url = re.sub(r"[?&]pgbouncer=[^&]*", "", url)
        url = re.sub(r"[?&]connect_timeout=[^&]*", "", url)
        # Clean up any trailing ? or &&
        url = url.rstrip("?").replace("&&", "&").rstrip("&")

        return url

    # OpenRouter API (for both LLM and Embeddings)
    # See: https://openrouter.ai/openai/text-embedding-3-small/api
    openrouter_api_key: str = ""
    llm_model: str = "openai/gpt-4o-mini"
    embedding_model: str = "openai/text-embedding-3-small"

    # Optional: OpenAI API key (fallback, not required if using OpenRouter)
    openai_api_key: str = ""

    # Storage
    upload_dir: str = "./data/uploads"

    # Supabase Storage
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    storage_bucket: str = "documents"

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

    # Logging - Loki
    loki_url: str = ""
    loki_enabled: bool = False

    # Evaluation - Ragas
    evaluation_enabled: bool = False
    evaluation_sample_rate: float = 0.1  # Evaluate 10% of queries by default

    # Retrieval Configuration
    retrieval_top_k: int = 5  # Number of top similar documents to retrieve for RAG
    retrieval_min_similarity: float = 0.0  # Minimum similarity threshold (0.0 = no filter)

    # Intent Classification Configuration
    intent_classification_enabled: bool = True  # Enable intent-based adaptive RAG strategies
    intent_cache_enabled: bool = True  # Cache intent classification results

    # Long Context RAG Configuration
    rag_mode: str = "traditional"  # traditional | long_context | auto
    long_context_safety_ratio: float = 0.55  # Use 55% of model context window (conservative)
    long_context_min_tokens: int = 10000  # Minimum tokens to use long context mode
    enable_citation_grounding: bool = True  # Enable citation anchors
    citation_format: str = "both"  # inline | structured | both

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
