"""SQLAlchemy implementation of ChunkRepository for unified resource chunks."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.resource import ResourceType
from research_agent.domain.entities.resource_chunk import ResourceChunk
from research_agent.domain.repositories.chunk_repo import ChunkRepository, ChunkSearchResult
from research_agent.infrastructure.database.models import ResourceChunkModel
from research_agent.shared.utils.logger import logger


class SQLAlchemyChunkRepository(ChunkRepository):
    """SQLAlchemy implementation of chunk repository using pgvector.
    
    This implementation stores both embeddings and metadata in PostgreSQL,
    supporting vector similarity search and hybrid search with tsvector.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_batch(self, chunks: List[ResourceChunk]) -> List[ResourceChunk]:
        """Save multiple resource chunks to PostgreSQL."""
        if not chunks:
            return chunks

        models = [self._to_model(chunk) for chunk in chunks]
        self._session.add_all(models)
        await self._session.flush()

        logger.info(f"[SQLAlchemyChunkRepo] Saved {len(chunks)} chunks to PostgreSQL")
        return chunks

    async def find_by_resource(self, resource_id: UUID) -> List[ResourceChunk]:
        """Find all chunks for a resource."""
        result = await self._session.execute(
            select(ResourceChunkModel)
            .where(ResourceChunkModel.resource_id == resource_id)
            .order_by(ResourceChunkModel.chunk_index)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def delete_by_resource(self, resource_id: UUID) -> int:
        """Delete all chunks for a resource."""
        result = await self._session.execute(
            delete(ResourceChunkModel).where(ResourceChunkModel.resource_id == resource_id)
        )
        await self._session.flush()

        logger.info(f"[SQLAlchemyChunkRepo] Deleted {result.rowcount} chunks for resource {resource_id}")
        return result.rowcount

    async def search(
        self,
        query_embedding: List[float],
        project_id: UUID,
        limit: int = 5,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[UUID] = None,
    ) -> List[ChunkSearchResult]:
        """Search for similar chunks using pgvector cosine similarity."""
        # Build base query with vector similarity
        query = (
            select(
                ResourceChunkModel.id,
                ResourceChunkModel.resource_id,
                ResourceChunkModel.resource_type,
                ResourceChunkModel.content,
                ResourceChunkModel.chunk_metadata,
                (1 - ResourceChunkModel.embedding.cosine_distance(query_embedding)).label("similarity"),
            )
            .where(ResourceChunkModel.project_id == project_id)
            .where(ResourceChunkModel.embedding.isnot(None))
        )

        # Apply optional filters
        if resource_type:
            query = query.where(ResourceChunkModel.resource_type == resource_type.value)
        if resource_id:
            query = query.where(ResourceChunkModel.resource_id == resource_id)

        # Order by similarity and limit
        query = query.order_by(text("similarity DESC")).limit(limit)

        result = await self._session.execute(query)
        rows = result.all()

        search_results = []
        for row in rows:
            search_results.append(
                ChunkSearchResult(
                    chunk_id=row.id,
                    resource_id=row.resource_id,
                    resource_type=ResourceType(row.resource_type),
                    content=row.content,
                    similarity=float(row.similarity),
                    metadata=row.chunk_metadata or {},
                )
            )

        logger.info(f"[SQLAlchemyChunkRepo] Vector search found {len(search_results)} results")
        return search_results

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
        """Hybrid search using Reciprocal Rank Fusion (RRF).
        
        Combines vector similarity search and full-text keyword search,
        then fuses results using RRF for better retrieval quality.
        """
        k = 60  # RRF constant

        # Get more results for fusion
        fetch_limit = limit * 3

        # Vector search
        vector_results = await self.search(
            query_embedding=query_embedding,
            project_id=project_id,
            limit=fetch_limit,
            resource_type=resource_type,
            resource_id=resource_id,
        )

        # Keyword search using tsvector
        keyword_query = (
            select(
                ResourceChunkModel.id,
                ResourceChunkModel.resource_id,
                ResourceChunkModel.resource_type,
                ResourceChunkModel.content,
                ResourceChunkModel.chunk_metadata,
                func.ts_rank(
                    ResourceChunkModel.content_tsvector,
                    func.websearch_to_tsquery("english", query_text),
                ).label("rank"),
            )
            .where(ResourceChunkModel.project_id == project_id)
            .where(
                ResourceChunkModel.content_tsvector.op("@@")(
                    func.websearch_to_tsquery("english", query_text)
                )
            )
        )

        if resource_type:
            keyword_query = keyword_query.where(
                ResourceChunkModel.resource_type == resource_type.value
            )
        if resource_id:
            keyword_query = keyword_query.where(ResourceChunkModel.resource_id == resource_id)

        keyword_query = keyword_query.order_by(text("rank DESC")).limit(fetch_limit)

        keyword_result = await self._session.execute(keyword_query)
        keyword_rows = keyword_result.all()

        # Build keyword results map
        keyword_results = {}
        for i, row in enumerate(keyword_rows):
            keyword_results[row.id] = {
                "rank": i + 1,
                "resource_id": row.resource_id,
                "resource_type": row.resource_type,
                "content": row.content,
                "metadata": row.chunk_metadata or {},
            }

        # RRF fusion
        rrf_scores = {}
        chunk_data = {}

        # Add vector search scores
        for i, result in enumerate(vector_results):
            rank = i + 1
            rrf_scores[result.chunk_id] = vector_weight / (k + rank)
            chunk_data[result.chunk_id] = result

        # Add keyword search scores
        for chunk_id, data in keyword_results.items():
            rank = data["rank"]
            score = keyword_weight / (k + rank)
            if chunk_id in rrf_scores:
                rrf_scores[chunk_id] += score
            else:
                rrf_scores[chunk_id] = score
                chunk_data[chunk_id] = ChunkSearchResult(
                    chunk_id=chunk_id,
                    resource_id=data["resource_id"],
                    resource_type=ResourceType(data["resource_type"]),
                    content=data["content"],
                    similarity=0.0,  # Will be replaced by RRF score
                    metadata=data["metadata"],
                )

        # Sort by RRF score and return top results
        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:limit]

        results = []
        for chunk_id, rrf_score in sorted_chunks:
            result = chunk_data[chunk_id]
            # Replace similarity with RRF score for consistent interface
            results.append(
                ChunkSearchResult(
                    chunk_id=result.chunk_id,
                    resource_id=result.resource_id,
                    resource_type=result.resource_type,
                    content=result.content,
                    similarity=rrf_score,
                    metadata=result.metadata,
                )
            )

        logger.info(
            f"[SQLAlchemyChunkRepo] Hybrid search: {len(vector_results)} vector, "
            f"{len(keyword_results)} keyword, {len(results)} fused"
        )
        return results

    def _to_model(self, entity: ResourceChunk) -> ResourceChunkModel:
        """Convert ResourceChunk entity to ORM model."""
        return ResourceChunkModel(
            id=entity.id,
            resource_id=entity.resource_id,
            resource_type=entity.resource_type.value,
            project_id=entity.project_id,
            chunk_index=entity.chunk_index,
            content=entity.content,
            embedding=entity.embedding,
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
