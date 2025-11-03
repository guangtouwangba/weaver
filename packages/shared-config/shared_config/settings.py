"""Pydantic settings for the minimal RAG service."""

from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application configuration exposed to service components."""

    # General
    app_env: str = Field("development", alias="APP_ENV")
    vector_top_k: int = Field(4, alias="VECTOR_TOP_K")
    fake_embedding_size: int = Field(768, alias="FAKE_EMBEDDING_SIZE")

    # Embedding configuration
    embedding_provider: str = Field("fake", alias="EMBEDDING_PROVIDER")  # fake, openai, openrouter
    embedding_model: str = Field("text-embedding-3-small", alias="EMBEDDING_MODEL")
    embedding_dimensions: Optional[int] = Field(None, alias="EMBEDDING_DIMENSIONS")

    # OpenAI configuration
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(None, alias="OPENAI_BASE_URL")

    # OpenRouter configuration
    openrouter_api_key: Optional[str] = Field(None, alias="OPENROUTER_API_KEY")
    openrouter_site_url: Optional[str] = Field(None, alias="OPENROUTER_SITE_URL")
    openrouter_site_name: Optional[str] = Field(None, alias="OPENROUTER_SITE_NAME")

    @field_validator("embedding_dimensions", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty string to None for optional int fields."""
        if v == "" or v is None:
            return None
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
    )
