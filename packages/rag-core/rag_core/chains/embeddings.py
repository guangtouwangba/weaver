"""Embedding helpers."""

from typing import Any

from langchain_community.embeddings import FakeEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.pydantic_v1 import BaseModel, Field, SecretStr
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

from rag_core.graphs.state import DocumentIngestState
from shared_config.settings import AppSettings


class OpenRouterEmbeddings(BaseModel, Embeddings):
    """OpenRouter embeddings using OpenAI-compatible API.

    Supports any model available on OpenRouter, including:
    - Google: google/gemini-embedding-001
    - OpenAI: openai/text-embedding-3-small
    - Cohere: cohere/embed-english-v3.0
    - And many more...

    Example::

        embeddings = OpenRouterEmbeddings(
            model="google/gemini-embedding-001",
            openrouter_api_key="your-key",
            site_url="https://yoursite.com",
            site_name="Your App Name"
        )
        vectors = embeddings.embed_documents(["Hello", "World"])

    Note:
        Replace "your-key" with your actual OpenRouter API key from
        https://openrouter.ai/keys
    """

    client: Any = None  #: :meta private:
    model: str = Field(default="openai/text-embedding-3-small")
    openrouter_api_key: SecretStr = Field(default=None)
    base_url: str = Field(default="https://openrouter.ai/api/v1")

    # Optional headers for OpenRouter rankings
    site_url: str | None = Field(default=None)
    site_name: str | None = Field(default=None)

    # Embedding parameters
    dimensions: int | None = Field(default=None)
    encoding_format: str = Field(default="float")

    # Request parameters
    max_retries: int = Field(default=3)
    timeout: float | None = Field(default=60.0)

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    def __init__(self, **data: Any):
        """Initialize OpenRouter embeddings."""
        super().__init__(**data)

        # Initialize OpenAI client with OpenRouter endpoint
        self.client = OpenAI(
            api_key=self.openrouter_api_key.get_secret_value() if self.openrouter_api_key else None,
            base_url=self.base_url,
            max_retries=self.max_retries,
            timeout=self.timeout,
        )

    def _get_extra_headers(self) -> dict[str, str]:
        """Build extra headers for OpenRouter."""
        headers = {}
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            headers["X-Title"] = self.site_name
        return headers

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents using OpenRouter.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embeddings, one for each text.
        """
        if not texts:
            return []

        # Log API call details
        print(f"  📡 调用 OpenRouter API...")
        print(f"    ├─ Endpoint: {self.base_url}")
        print(f"    ├─ Model: {self.model}")
        print(f"    ├─ 文本数量: {len(texts)}")
        if self.dimensions:
            print(f"    ├─ 指定维度: {self.dimensions}")

        # Build request parameters
        params: dict[str, Any] = {
            "model": self.model,
            "input": texts,
            "encoding_format": self.encoding_format,
        }

        if self.dimensions is not None:
            params["dimensions"] = self.dimensions

        # Add extra headers if provided
        extra_headers = self._get_extra_headers()

        # Call OpenRouter API
        print(f"    └─ 发送请求...")
        response = self.client.embeddings.create(extra_headers=extra_headers if extra_headers else None, **params)
        print(f"    ✓ API 响应成功")

        # Extract embeddings from response
        embeddings = [item.embedding for item in response.data]
        print(f"    ✓ 解析 {len(embeddings)} 个向量，维度={len(embeddings[0]) if embeddings else 0}")
        
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query text using OpenRouter.

        Args:
            text: Text string to embed.

        Returns:
            Embedding vector for the text.
        """
        return self.embed_documents([text])[0]


def build_embedding_function(settings: AppSettings) -> Embeddings:
    """Return an embeddings implementation based on configured provider.

    Supported providers:
    - openai: OpenAI embeddings (text-embedding-3-small, etc.)
    - openrouter: OpenRouter embeddings (supports multiple models)
    - fake: Fake embeddings for testing
    """
    provider = settings.embedding_provider.lower()

    if provider == "openai":
        return OpenAIEmbeddings(
            model=settings.embedding_model,
        )

    elif provider == "openrouter":
        return OpenRouterEmbeddings(
            model=settings.embedding_model,
            openrouter_api_key=settings.openrouter_api_key,
            site_url=settings.openrouter_site_url,
            site_name=settings.openrouter_site_name,
            dimensions=settings.embedding_dimensions if settings.embedding_dimensions else None,
        )

    # Default to fake embeddings for development
    return FakeEmbeddings(size=settings.fake_embedding_size)


async def embed_chunks(state: DocumentIngestState) -> DocumentIngestState:
    """Generate embeddings for text chunks."""
    if not state.chunks:
        raise ValueError("split step must run before embedding")
    
    settings = AppSettings()  # type: ignore[arg-type]
    embeddings_model = build_embedding_function(settings)
    
    # Log embedding start
    print(f"🎯 开始生成 Embeddings...")
    print(f"  ├─ Provider: {settings.embedding_provider}")
    print(f"  ├─ Model: {settings.embedding_model}")
    print(f"  ├─ Chunks 数量: {len(state.chunks)}")
    print(f"  ├─ 文档ID: {state.document_id}")
    
    # Generate embeddings
    embeddings: list[list[float]] = embeddings_model.embed_documents(state.chunks)
    
    # Log completion
    print(f"✅ Embeddings 生成完成!")
    print(f"  ├─ 生成向量数量: {len(embeddings)}")
    print(f"  └─ 向量维度: {len(embeddings[0]) if embeddings else 0}")
    
    return state.model_copy(update={"embeddings": embeddings})
