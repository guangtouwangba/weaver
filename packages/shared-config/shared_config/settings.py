"""Pydantic settings for the minimal RAG service."""

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Application configuration exposed to service components."""

    app_env: str = Field("development", alias="APP_ENV")
    vector_top_k: int = Field(4, alias="VECTOR_TOP_K")
    fake_embedding_size: int = Field(768, alias="FAKE_EMBEDDING_SIZE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
