"""
Configuration management for RAG Research Agent System.
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(default="postgresql://rag_user:rag_password@localhost:5432/rag_db")
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0)
    echo: bool = Field(default=False)
    
    class Config:
        env_prefix = "DATABASE_"


class VectorStoreConfig(BaseSettings):
    """Vector store configuration settings."""
    
    weaviate_url: str = Field(default="http://localhost:8080")
    chroma_url: str = Field(default="http://localhost:8000")
    embedding_dimension: int = Field(default=1536)
    
    class Config:
        env_prefix = "VECTOR_STORE_"


class LLMConfig(BaseSettings):
    """LLM configuration settings."""
    
    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)
    model_name: str = Field(default="gpt-3.5-turbo")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=4000)
    
    class Config:
        env_prefix = "LLM_"


class StorageConfig(BaseSettings):
    """Storage configuration settings."""
    
    minio_endpoint: str = Field(default="localhost:9000")
    minio_access_key: str = Field(default="minioadmin")
    minio_secret_key: str = Field(default="minioadmin")
    minio_secure: bool = Field(default=False)
    
    class Config:
        env_prefix = "STORAGE_"


class Config(PydanticBaseSettings):
    """Main configuration class for RAG system."""
    
    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    
    # Database
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # Vector Store
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    
    # LLM
    llm: LLMConfig = Field(default_factory=LLMConfig)
    
    # Storage
    storage: StorageConfig = Field(default_factory=StorageConfig)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production")
    access_token_expire_minutes: int = Field(default=30, ge=1)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "testing", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return v.upper()


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment."""
    global _config
    _config = Config()
    return _config
