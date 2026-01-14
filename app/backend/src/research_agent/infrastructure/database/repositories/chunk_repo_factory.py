"""Factory function for ChunkRepository."""

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.domain.repositories.chunk_repo import ChunkRepository
from research_agent.shared.utils.logger import logger


def get_chunk_repository(session: AsyncSession) -> ChunkRepository:
    """Get ChunkRepository based on VECTOR_STORE_PROVIDER config.

    Args:
        session: SQLAlchemy async session

    Returns:
        ChunkRepository implementation:
        - QdrantChunkRepository if VECTOR_STORE_PROVIDER=qdrant
        - SQLAlchemyChunkRepository otherwise (default: pgvector)

    Both implementations now use the unified ResourceChunk entity and
    resource_chunks table for storage.
    """
    settings = get_settings()

    if settings.vector_store_provider == "qdrant":
        from research_agent.infrastructure.database.repositories.qdrant_chunk_repo import (
            QdrantChunkRepository,
        )
        logger.debug("[ChunkRepoFactory] Using QdrantChunkRepository")
        return QdrantChunkRepository(session)
    else:
        from research_agent.infrastructure.database.repositories.sqlalchemy_chunk_repo import (
            SQLAlchemyChunkRepository,
        )
        logger.debug("[ChunkRepoFactory] Using SQLAlchemyChunkRepository (pgvector)")
        return SQLAlchemyChunkRepository(session)
