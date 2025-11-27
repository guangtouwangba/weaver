"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# Find .env file - check multiple locations
def find_env_file() -> str:
    """Find .env file in current dir or parent dirs."""
    # Check current directory
    if Path(".env").exists():
        return ".env"
    # Check app/backend directory
    backend_env = Path(__file__).parent.parent.parent.parent / ".env"
    if backend_env.exists():
        return str(backend_env)
    # Check project root
    root_env = Path(__file__).parent.parent.parent.parent.parent.parent / ".env"
    if root_env.exists():
        return str(root_env)
    return ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
    )

    # Database
    database_url: str = "postgresql+asyncpg://research_rag:research_rag_dev@localhost:5432/research_rag"

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
        
        # Remove sslmode parameter - asyncpg handles SSL differently
        # We'll configure SSL via connect_args in the engine instead
        import re
        url = re.sub(r'[?&]sslmode=[^&]*', '', url)
        # Clean up any trailing ? or &&
        url = url.rstrip('?').replace('&&', '&').rstrip('&')
        
        return url

    # OpenRouter API
    openrouter_api_key: str = ""
    llm_model: str = "openai/gpt-4o-mini"
    embedding_model: str = "openai/text-embedding-3-small"

    # Storage
    upload_dir: str = "./data/uploads"

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

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

