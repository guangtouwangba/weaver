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
