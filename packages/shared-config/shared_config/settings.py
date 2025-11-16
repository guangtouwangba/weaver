"""Pydantic settings for the minimal RAG service."""

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ========================================
# 模块化配置类
# ========================================


class LLMConfig(BaseSettings):
    """LLM configuration."""

    # Provider selection
    provider: str = Field("fake", alias="LLM_PROVIDER")  # fake, openai, openrouter
    model: str = Field("openai/gpt-3.5-turbo", alias="LLM_MODEL")

    # Generation parameters
    temperature: float = Field(0.7, alias="LLM_TEMPERATURE", ge=0.0, le=2.0)
    max_tokens: int = Field(2000, alias="LLM_MAX_TOKENS", ge=1)  # 默认2000，可根据需要调整
    top_p: float = Field(1.0, alias="LLM_TOP_P", ge=0.0, le=1.0)
    frequency_penalty: float = Field(0.0, alias="LLM_FREQUENCY_PENALTY", ge=-2.0, le=2.0)
    presence_penalty: float = Field(0.0, alias="LLM_PRESENCE_PENALTY", ge=-2.0, le=2.0)
    n: int = Field(1, alias="LLM_N", ge=1)
    stream: bool = Field(False, alias="LLM_STREAM")
    stop: str | None = Field(None, alias="LLM_STOP")

    # Reliability
    timeout: float = Field(60.0, alias="LLM_TIMEOUT")
    max_retries: int = Field(3, alias="LLM_MAX_RETRIES", ge=0)

    # OpenRouter specific
    openrouter_api_key: SecretStr | None = Field(None, alias="OPENROUTER_API_KEY")
    openrouter_site_url: str | None = Field(None, alias="OPENROUTER_SITE_URL")
    openrouter_site_name: str | None = Field(None, alias="OPENROUTER_SITE_NAME")

    # OpenAI specific (if needed separately)
    openai_api_key: SecretStr | None = Field(None, alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(None, alias="OPENAI_BASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class EmbeddingConfig(BaseSettings):
    """Embedding configuration."""

    # Provider selection
    provider: str = Field("fake", alias="EMBEDDING_PROVIDER")  # fake, openai, openrouter
    model: str = Field("openai/text-embedding-3-small", alias="EMBEDDING_MODEL")  # Use provider prefix for openrouter
    dimensions: int | None = Field(None, alias="EMBEDDING_DIMENSIONS")

    # Embedding parameters
    encoding_format: str = Field("float", alias="EMBEDDING_ENCODING_FORMAT")

    # Fake embeddings config (for testing)
    fake_embedding_size: int = Field(768, alias="FAKE_EMBEDDING_SIZE")

    # Reliability
    timeout: float = Field(60.0, alias="EMBEDDING_TIMEOUT")
    max_retries: int = Field(3, alias="EMBEDDING_MAX_RETRIES", ge=0)

    # OpenRouter specific
    openrouter_api_key: SecretStr | None = Field(None, alias="OPENROUTER_API_KEY")
    openrouter_site_url: str | None = Field(None, alias="OPENROUTER_SITE_URL")
    openrouter_site_name: str | None = Field(None, alias="OPENROUTER_SITE_NAME")

    # OpenAI specific
    openai_api_key: SecretStr | None = Field(None, alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(None, alias="OPENAI_BASE_URL")

    @field_validator("dimensions", mode="before")
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
        extra="ignore",
    )


class MemoryConfig(BaseSettings):
    """Conversational memory configuration for embedding-based history retrieval."""

    # Conversation-level memory (within same conversation)
    conversation_memory_limit: int = Field(2, alias="MEMORY_CONVERSATION_LIMIT", ge=0, le=10)
    conversation_similarity_threshold: float = Field(0.75, alias="MEMORY_CONVERSATION_THRESHOLD", ge=0.0, le=1.0)

    # Topic-level memory (across conversations in same topic)
    topic_memory_limit: int = Field(3, alias="MEMORY_TOPIC_LIMIT", ge=0, le=10)
    topic_similarity_threshold: float = Field(0.70, alias="MEMORY_TOPIC_THRESHOLD", ge=0.0, le=1.0)

    # Total memory limit (combined)
    max_total_memories: int = Field(5, alias="MEMORY_MAX_TOTAL", ge=1, le=20)

    # Enable/disable memory retrieval
    enable_conversation_memory: bool = Field(True, alias="MEMORY_ENABLE_CONVERSATION")
    enable_topic_memory: bool = Field(True, alias="MEMORY_ENABLE_TOPIC")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class RetrieverConfig(BaseSettings):
    """Retriever configuration."""

    # Search parameters
    top_k: int = Field(4, alias="VECTOR_TOP_K", ge=1)
    search_type: str = Field("similarity", alias="RETRIEVER_SEARCH_TYPE")  # similarity, mmr
    similarity_threshold: float = Field(0.7, alias="RETRIEVER_SIMILARITY_THRESHOLD", ge=0.0, le=1.0)

    # MMR parameters (for future use)
    lambda_mult: float = Field(0.5, alias="RETRIEVER_LAMBDA_MULT", ge=0.0, le=1.0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    database_url: str = Field("postgresql://localhost:5432/knowledge_platform", alias="DATABASE_URL")
    pool_size: int = Field(5, alias="DB_POOL_SIZE", ge=1)
    max_overflow: int = Field(10, alias="DB_MAX_OVERFLOW", ge=0)
    echo: bool = Field(False, alias="DB_ECHO")  # SQL logging

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class DocumentParserConfig(BaseSettings):
    """Document parser configuration."""

    # Parser selection: "default" (standard loaders) or "langextract" (AI-powered)
    parser_type: str = Field("langextract", alias="DOCUMENT_PARSER_TYPE")
    
    # LangExtract specific settings
    langextract_model_id: str = Field("gemini-2.5-flash", alias="LANGEXTRACT_MODEL_ID")
    langextract_api_key: SecretStr | None = Field(None, alias="LANGEXTRACT_API_KEY")
    langextract_provider: str = Field("gemini", alias="LANGEXTRACT_PROVIDER")
    langextract_base_url: str | None = Field(None, alias="LANGEXTRACT_BASE_URL")
    langextract_use_schema: bool = Field(True, alias="LANGEXTRACT_USE_SCHEMA")
    langextract_fence_output: bool = Field(False, alias="LANGEXTRACT_FENCE_OUTPUT")
    
    # Parser behavior
    enable_enhanced_parsing: bool = Field(True, alias="PARSER_ENABLE_ENHANCED")
    
    # OpenRouter specific (shared with LLM/Embedding configs)
    openrouter_api_key: SecretStr | None = Field(None, alias="OPENROUTER_API_KEY")
    openrouter_site_url: str | None = Field(None, alias="OPENROUTER_SITE_URL")
    openrouter_site_name: str | None = Field(None, alias="OPENROUTER_SITE_NAME")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# ========================================
# 聚合配置类（向后兼容）
# ========================================


class AppSettings(BaseSettings):
    """Application configuration exposed to service components."""

    # General
    app_env: str = Field("development", alias="APP_ENV")

    # Vector store persistence
    vector_store_path: str = Field("./data/vector_store", alias="VECTOR_STORE_PATH")

    # 聚合模块化配置
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    retriever: RetrieverConfig = Field(default_factory=RetrieverConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    document_parser: DocumentParserConfig = Field(default_factory=DocumentParserConfig)

    # ========================================
    # 向后兼容属性（保持旧代码正常工作）
    # ========================================

    @property
    def vector_top_k(self) -> int:
        """Backward compatibility for vector_top_k."""
        return self.retriever.top_k

    @property
    def fake_embedding_size(self) -> int:
        """Backward compatibility for fake_embedding_size."""
        return self.embedding.fake_embedding_size

    @property
    def embedding_provider(self) -> str:
        """Backward compatibility for embedding_provider."""
        return self.embedding.provider

    @property
    def embedding_model(self) -> str:
        """Backward compatibility for embedding_model."""
        return self.embedding.model

    @property
    def embedding_dimensions(self) -> int | None:
        """Backward compatibility for embedding_dimensions."""
        return self.embedding.dimensions

    @property
    def openai_api_key(self) -> str | None:
        """Backward compatibility for openai_api_key."""
        key = self.embedding.openai_api_key
        return key.get_secret_value() if key else None

    @property
    def openrouter_api_key(self) -> str | None:
        """Backward compatibility for openrouter_api_key."""
        key = self.embedding.openrouter_api_key
        return key.get_secret_value() if key else None

    @property
    def openrouter_site_url(self) -> str | None:
        """Backward compatibility for openrouter_site_url."""
        return self.embedding.openrouter_site_url

    @property
    def openrouter_site_name(self) -> str | None:
        """Backward compatibility for openrouter_site_name."""
        return self.embedding.openrouter_site_name

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
