"""Qdrant implementation of ChunkRepository for unified resource chunks."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.domain.entities.resource import ResourceType
from research_agent.domain.entities.resource_chunk import ResourceChunk
from research_agent.domain.repositories.chunk_repo import ChunkRepository, ChunkSearchResult
from research_agent.infrastructure.database.models import ResourceChunkModel
from research_agent.infrastructure.vector_store.qdrant import (
    QdrantVectorStore,
    ensure_collection_exists,
    get_qdrant_client,
)
from research_agent.shared.utils.logger import logger


class QdrantChunkRepository(ChunkRepository):
    """Qdrant + PostgreSQL hybrid chunk repository.

    - Embeddings stored in Qdrant for fast vector search
    - Metadata stored in PostgreSQL for relational queries
    - PostgreSQL embedding column set to None to save space
    """

    def __init__(self, session: AsyncSession):
        self._session = session
        self._settings = get_settings()
        self._qdrant_store = QdrantVectorStore()

    async def _ensure_collection(self, vector_size: int = 1536) -> None:
        """Ensure Qdrant collection exists with proper indexes."""
        client = await get_qdrant_client()
        await ensure_collection_exists(
            client=client,
            collection_name=self._settings.qdrant_collection_name,
            vector_size=vector_size,
        )

    async def save_batch(self, chunks: List[ResourceChunk]) -> List[ResourceChunk]:
        """Save chunks to both Qdrant (embeddings) and PostgreSQL (metadata)."""
        if not chunks:
            return chunks

        # Determine vector size from first chunk with embedding
        vector_size = 1536
        for chunk in chunks:
            if chunk.embedding:
                vector_size = len(chunk.embedding)
                break

        # Ensure Qdrant collection exists
        await self._ensure_collection(vector_size)

        # Write to Qdrant (batch upsert)
        chunks_data = []
        for chunk in chunks:
            if chunk.embedding:
                chunks_data.append(
                    {
                        "chunk_id": chunk.id,
                        "resource_id": chunk.resource_id,
                        "resource_type": chunk.resource_type,
                        "project_id": chunk.project_id,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                        "embedding": chunk.embedding,
                        "metadata": chunk.metadata,
                        "user_id": chunk.user_id,
                    }
                )

        if chunks_data:
            try:
                await self._qdrant_store.upsert_resource_chunks_batch(
                    chunks_data=chunks_data,
                    batch_size=100,  # Optimal batch size for Qdrant
                )
            except Exception as e:
                logger.error(f"[QdrantChunkRepo] Failed to upsert batch: {e}")
                raise

        logger.info(f"[QdrantChunkRepo] Saved {len(chunks_data)} embeddings to Qdrant")

        # Write to PostgreSQL (without embedding to save space)
        models = [self._to_model(chunk, include_embedding=False) for chunk in chunks]
        self._session.add_all(models)
        await self._session.flush()

        logger.info(f"[QdrantChunkRepo] Saved {len(chunks)} metadata to PostgreSQL")
        return chunks

    async def find_by_resource(self, resource_id: UUID) -> List[ResourceChunk]:
        """Find all chunks for a resource from PostgreSQL."""
        result = await self._session.execute(
            select(ResourceChunkModel)
            .where(ResourceChunkModel.resource_id == resource_id)
            .order_by(ResourceChunkModel.chunk_index)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def delete_by_resource(self, resource_id: UUID) -> int:
        """Delete chunks from both Qdrant and PostgreSQL."""
        # Delete from Qdrant first
        try:
            await self._qdrant_store.delete_by_resource(resource_id)
            logger.info(f"[QdrantChunkRepo] Deleted from Qdrant: {resource_id}")
        except Exception as e:
            logger.error(f"[QdrantChunkRepo] Failed to delete from Qdrant: {e}")

        # Delete from PostgreSQL
        result = await self._session.execute(
            delete(ResourceChunkModel).where(ResourceChunkModel.resource_id == resource_id)
        )
        await self._session.flush()

        logger.info(f"[QdrantChunkRepo] Deleted {result.rowcount} from PostgreSQL")
        return result.rowcount

    async def search(
        self,
        query_embedding: List[float],
        project_id: UUID,
        limit: int = 5,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[UUID] = None,
    ) -> List[ChunkSearchResult]:
        """Search for similar chunks using Qdrant vector search."""
        results = await self._qdrant_store.search_resource_chunks(
            query_embedding=query_embedding,
            project_id=project_id,
            limit=limit,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        return results

    async def hybrid_search(
        self,
        query_embedding: List[float],
        query_text: str,
        project_id: UUID,
        limit: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[UUID] = None,
    ) -> List[ChunkSearchResult]:
        """Hybrid search - falls back to vector-only for Qdrant."""
        logger.info("[QdrantChunkRepo] Hybrid search falling back to vector-only")
        return await self.search(
            query_embedding=query_embedding,
            project_id=project_id,
            limit=limit,
            resource_type=resource_type,
            resource_id=resource_id,
        )

    def _to_model(
        self, entity: ResourceChunk, include_embedding: bool = True
    ) -> ResourceChunkModel:
        """Convert ResourceChunk entity to ORM model."""
        return ResourceChunkModel(
            id=entity.id,
            resource_id=entity.resource_id,
            resource_type=entity.resource_type.value,
            project_id=entity.project_id,
            chunk_index=entity.chunk_index,
            content=entity.content,
            embedding=entity.embedding if include_embedding else None,
            chunk_metadata=entity.metadata,
            created_at=entity.created_at,
        )

    def _to_entity(self, model: ResourceChunkModel) -> ResourceChunk:
        """Convert ORM model to ResourceChunk entity."""
        return ResourceChunk(
            id=model.id,
            resource_id=model.resource_id,
            resource_type=ResourceType(model.resource_type),
            project_id=model.project_id,
            chunk_index=model.chunk_index,
            content=model.content,
            embedding=list(model.embedding) if model.embedding else None,
            metadata=model.chunk_metadata or {},
            created_at=model.created_at,
        )
