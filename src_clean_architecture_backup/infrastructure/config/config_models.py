"""
Configuration data models.

Defines the structure of configuration objects.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class AIConfig:
    """AI service configuration."""
    provider: str = "openai"  # openai, local, etc.
    api_key: Optional[str] = None
    chat_model: str = "gpt-3.5-turbo"
    embedding_model: str = "text-embedding-ada-002"
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30


@dataclass
class StorageConfig:
    """Storage configuration."""
    type: str = "local"  # local, minio, s3, etc.
    base_path: Optional[str] = None
    bucket: Optional[str] = None
    endpoint: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    secure: bool = True


@dataclass
class CacheConfig:
    """Cache configuration."""
    type: str = "memory"  # memory, redis, etc.
    url: Optional[str] = None
    ttl: int = 3600
    max_size: int = 1000


@dataclass
class VectorStoreConfig:
    """Vector store configuration."""
    type: str = "memory"  # memory, weaviate, chroma, etc.
    url: Optional[str] = None
    api_key: Optional[str] = None
    collection_name: str = "documents"
    dimension: int = 1536


@dataclass
class ApplicationConfig:
    """Main application configuration."""
    # Component configurations (required fields first)
    database: DatabaseConfig
    ai: AIConfig
    storage: StorageConfig
    cache: CacheConfig
    vector_store: VectorStoreConfig
    
    # Optional fields with defaults
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"