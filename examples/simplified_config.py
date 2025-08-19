"""
Simplified Configuration Management Example

This demonstrates how to consolidate the scattered configuration
into a single, hierarchical, type-safe system using Pydantic Settings.
"""

from typing import Dict, Any, List, Optional
from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, validator, Field
from pydantic_settings import SettingsConfigDict


# =============================================================================
# Component-Specific Settings
# =============================================================================

class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    # Core connection settings
    host: str = "localhost"
    port: int = 5432
    name: str = "rag_db"
    username: str = "rag_user"
    password: str = "rag_password"
    
    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    # Async settings
    echo: bool = False
    echo_pool: bool = False
    
    @property
    def url(self) -> str:
        """Generate database URL."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    @property
    def alembic_url(self) -> str:
        """Generate synchronous database URL for Alembic."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    model_config = SettingsConfigDict(env_prefix="DB_")


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    
    # Connection settings
    max_connections: int = 20
    decode_responses: bool = True
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    
    @property
    def url(self) -> str:
        """Generate Redis URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.database}"
    
    model_config = SettingsConfigDict(env_prefix="REDIS_")


class MinIOSettings(BaseSettings):
    """MinIO S3-compatible storage settings."""
    
    endpoint: str = "localhost:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    secure: bool = False
    region: str = "us-east-1"
    
    # Bucket settings
    default_bucket: str = "rag-documents"
    auto_create_bucket: bool = True
    
    model_config = SettingsConfigDict(env_prefix="MINIO_")


class S3Settings(BaseSettings):
    """AWS S3 storage settings."""
    
    access_key_id: str
    secret_access_key: str
    region: str = "us-east-1"
    endpoint_url: Optional[str] = None
    
    # Bucket settings
    default_bucket: str = "rag-documents"
    
    model_config = SettingsConfigDict(env_prefix="AWS_")


class GCPSettings(BaseSettings):
    """Google Cloud Storage settings."""
    
    project_id: str
    credentials_path: Optional[str] = None
    credentials_json: Optional[str] = None
    
    # Bucket settings
    default_bucket: str = "rag-documents"
    
    model_config = SettingsConfigDict(env_prefix="GCP_")


class StorageSettings(BaseSettings):
    """Multi-provider storage configuration."""
    
    # Provider selection
    provider: str = Field(default="minio", description="Storage provider: minio, s3, gcs, alibaba")
    
    # Provider-specific settings
    minio: MinIOSettings = Field(default_factory=MinIOSettings)
    s3: S3Settings = Field(default_factory=lambda: S3Settings(access_key_id="", secret_access_key=""))
    gcp: GCPSettings = Field(default_factory=lambda: GCPSettings(project_id=""))
    
    @validator("provider")
    def validate_provider(cls, v):
        """Validate storage provider."""
        allowed = ["minio", "s3", "gcs", "alibaba"]
        if v not in allowed:
            raise ValueError(f"Storage provider must be one of: {allowed}")
        return v


class EmbeddingSettings(BaseSettings):
    """Embedding model configuration."""
    
    # Model selection
    provider: str = Field(default="huggingface", description="Embedding provider: huggingface, openai, cohere")
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Hugging Face settings
    hf_token: Optional[str] = None
    device: str = "auto"  # auto, cpu, cuda
    
    # OpenAI settings
    openai_api_key: Optional[str] = None
    
    # Cohere settings
    cohere_api_key: Optional[str] = None
    
    # Processing settings
    batch_size: int = 32
    max_length: int = 512
    
    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")


class VectorStoreSettings(BaseSettings):
    """Vector store configuration."""
    
    # Provider selection
    provider: str = Field(default="weaviate", description="Vector store: weaviate, chroma, qdrant, pinecone")
    
    # Weaviate settings
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: Optional[str] = None
    
    # Chroma settings
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_persist_directory: Optional[str] = None
    
    # Index settings
    default_index_name: str = "documents"
    dimension: int = 384  # Should match embedding model
    
    model_config = SettingsConfigDict(env_prefix="VECTOR_")


class RAGSettings(BaseSettings):
    """RAG processing configuration."""
    
    # Document processing
    chunk_size: int = 512
    chunk_overlap: int = 50
    chunk_strategy: str = "recursive"  # recursive, fixed, semantic
    
    # OCR settings
    enable_ocr: bool = True
    ocr_language: str = "eng"
    
    # Processing features
    enable_auto_tagging: bool = True
    enable_summary: bool = True
    enable_image_extraction: bool = True
    
    # Search settings
    default_search_strategy: str = "semantic"  # semantic, keyword, hybrid
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    
    # Performance settings
    max_parallel_processing: int = 4
    processing_timeout: int = 300  # seconds
    
    model_config = SettingsConfigDict(env_prefix="RAG_")


class SecuritySettings(BaseSettings):
    """Security and authentication settings."""
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_headers: List[str] = ["*"]
    
    # API settings
    api_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # seconds
    
    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    model_config = SettingsConfigDict(env_prefix="SECURITY_")


# =============================================================================
# Main Application Settings
# =============================================================================

class Settings(BaseSettings):
    """
    Main application settings with hierarchical configuration.
    
    This consolidates all configuration into a single, type-safe,
    environment-aware settings system.
    """
    
    # Application settings
    app_name: str = "Research Agent RAG"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"  # json, text
    log_file: Optional[str] = None
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return v.upper()
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get configuration for the selected storage provider."""
        if self.storage.provider == "minio":
            return {
                "endpoint": self.storage.minio.endpoint,
                "access_key": self.storage.minio.access_key,
                "secret_key": self.storage.minio.secret_key,
                "secure": self.storage.minio.secure,
                "region": self.storage.minio.region,
                "bucket": self.storage.minio.default_bucket,
            }
        elif self.storage.provider == "s3":
            return {
                "access_key_id": self.storage.s3.access_key_id,
                "secret_access_key": self.storage.s3.secret_access_key,
                "region": self.storage.s3.region,
                "endpoint_url": self.storage.s3.endpoint_url,
                "bucket": self.storage.s3.default_bucket,
            }
        elif self.storage.provider == "gcp":
            return {
                "project_id": self.storage.gcp.project_id,
                "credentials_path": self.storage.gcp.credentials_path,
                "credentials_json": self.storage.gcp.credentials_json,
                "bucket": self.storage.gcp.default_bucket,
            }
        else:
            raise ValueError(f"Unsupported storage provider: {self.storage.provider}")
    
    def get_vector_store_config(self) -> Dict[str, Any]:
        """Get configuration for the selected vector store."""
        if self.vector_store.provider == "weaviate":
            return {
                "url": self.vector_store.weaviate_url,
                "api_key": self.vector_store.weaviate_api_key,
                "index_name": self.vector_store.default_index_name,
            }
        elif self.vector_store.provider == "chroma":
            return {
                "host": self.vector_store.chroma_host,
                "port": self.vector_store.chroma_port,
                "persist_directory": self.vector_store.chroma_persist_directory,
            }
        else:
            raise ValueError(f"Unsupported vector store provider: {self.vector_store.provider}")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )


# =============================================================================
# Settings Factory and Utilities
# =============================================================================

@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    
    This function loads settings once and caches them for the application lifetime.
    The cache can be cleared by calling get_settings.cache_clear().
    """
    return Settings()


def get_settings_for_testing() -> Settings:
    """
    Get settings for testing without caching.
    
    This allows tests to override settings without affecting the global cache.
    """
    return Settings(
        database=DatabaseSettings(
            host="localhost",
            port=5432,
            name="test_rag_db",
            username="test_user",
            password="test_password"
        ),
        storage=StorageSettings(
            provider="minio",
            minio=MinIOSettings(
                endpoint="localhost:9000",
                default_bucket="test-bucket"
            )
        ),
        environment="development",
        debug=True
    )


def load_settings_from_file(config_file: Path) -> Settings:
    """
    Load settings from a specific configuration file.
    
    Useful for loading different configurations for different environments.
    """
    return Settings(_env_file=config_file)


# =============================================================================
# Environment Configuration Examples
# =============================================================================

"""
# .env.development
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Database
DB__HOST=localhost
DB__PORT=5432
DB__NAME=rag_db_dev
DB__USERNAME=dev_user
DB__PASSWORD=dev_password

# Storage
STORAGE__PROVIDER=minio
MINIO__ENDPOINT=localhost:9000
MINIO__DEFAULT_BUCKET=dev-documents

# RAG
RAG__CHUNK_SIZE=512
RAG__ENABLE_OCR=true
RAG__MAX_PARALLEL_PROCESSING=2

# Vector Store
VECTOR__PROVIDER=weaviate
VECTOR__WEAVIATE_URL=http://localhost:8080

# Embedding
EMBEDDING__PROVIDER=huggingface
EMBEDDING__MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
"""

"""
# .env.production
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database
DB__HOST=prod-postgres.example.com
DB__PORT=5432
DB__NAME=rag_production
DB__USERNAME=rag_prod_user
DB__PASSWORD=${DB_PASSWORD}  # From environment

# Storage
STORAGE__PROVIDER=s3
AWS__ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS__SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS__REGION=us-west-2
AWS__DEFAULT_BUCKET=production-rag-docs

# Vector Store
VECTOR__PROVIDER=pinecone
VECTOR__PINECONE_API_KEY=${PINECONE_API_KEY}

# Security
SECURITY__CORS_ORIGINS=["https://yourdomain.com"]
SECURITY__API_KEY=${API_KEY}
SECURITY__JWT_SECRET=${JWT_SECRET}
"""


# =============================================================================
# Usage Examples
# =============================================================================

"""
# In main.py
from examples.simplified_config import get_settings

def create_app():
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug
    )
    
    # Use settings throughout the application
    return app

# In database configuration
def get_database_engine():
    settings = get_settings()
    return create_async_engine(
        settings.database.url,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        echo=settings.database.echo
    )

# In storage factory
def create_storage():
    settings = get_settings()
    config = settings.get_storage_config()
    
    if settings.storage.provider == "minio":
        return MinIOStorage(**config)
    elif settings.storage.provider == "s3":
        return S3Storage(**config)
    else:
        raise ValueError(f"Unsupported storage: {settings.storage.provider}")

# In tests
def test_topic_creation():
    settings = get_settings_for_testing()
    # Override specific settings for test
    settings.database.name = "test_specific_db"
    
    # Use settings in test...
"""


# =============================================================================
# Benefits of This Approach
# =============================================================================

"""
Benefits of this consolidated configuration system:

1. **Single Source of Truth**: All configuration in one place
2. **Type Safety**: Full Pydantic validation and type hints
3. **Environment-Aware**: Different configs for dev/staging/production
4. **Hierarchical**: Nested settings with clear organization
5. **Validation**: Built-in validation with custom validators
6. **IDE Support**: Full autocomplete and type checking
7. **Testing Friendly**: Easy to override settings for tests
8. **Documentation**: Self-documenting with field descriptions
9. **Flexible Loading**: Support for .env files, environment variables, JSON
10. **Provider Abstraction**: Easy to switch between providers

This eliminates the configuration fragmentation across multiple files
while providing a robust, maintainable configuration system.
"""