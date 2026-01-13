"""Vector store factory for creating provider-specific implementations."""

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.infrastructure.vector_store.base import VectorStore


def get_vector_store(
    session: AsyncSession,
    provider: str | None = None,
) -> VectorStore:
    """Get a vector store instance based on configuration.

    Args:
        session: SQLAlchemy async session (required for pgvector)
        provider: Optional provider override. If not provided,
                 uses VECTOR_STORE_PROVIDER from config.

    Returns:
        VectorStore implementation instance

    Raises:
        ValueError: If provider is not supported
    """
    settings = get_settings()
    provider = provider or settings.vector_store_provider

    if provider == "qdrant":
        from research_agent.infrastructure.vector_store.qdrant import QdrantVectorStore

        return QdrantVectorStore()
    elif provider == "pgvector":
        from research_agent.infrastructure.vector_store.pgvector import PgVectorStore

        return PgVectorStore(session)
    else:
        raise ValueError(
            f"Unsupported vector store provider: {provider}. "
            "Supported providers: pgvector, qdrant"
        )
