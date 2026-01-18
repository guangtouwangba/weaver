"""Qdrant vector store implementation."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from research_agent.config import get_settings
from research_agent.domain.entities.resource import ResourceType
from research_agent.domain.repositories.chunk_repo import ChunkSearchResult
from research_agent.infrastructure.vector_store.base import SearchResult, VectorStore
from research_agent.shared.utils.logger import logger

# Singleton client instance
_qdrant_client: AsyncQdrantClient | None = None


async def get_qdrant_client() -> AsyncQdrantClient:
    """Get or create the singleton Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        settings = get_settings()
        _qdrant_client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
        )
        logger.info(f"[Qdrant] Connected to {settings.qdrant_url}")
    return _qdrant_client


async def ensure_collection_exists(
    client: AsyncQdrantClient,
    collection_name: str,
    vector_size: int = 1536,
) -> None:
    """Create collection if it doesn't exist.

    Args:
        client: Qdrant async client
        collection_name: Name of the collection
        vector_size: Dimension of vectors (default: 1536 for OpenAI embeddings)
    """
    try:
        collections = await client.get_collections()
        existing_names = [c.name for c in collections.collections]

        if collection_name not in existing_names:
            logger.info(f"[Qdrant] Creating collection: {collection_name}")
            await client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
            # Create payload indexes for efficient filtering
            await client.create_payload_index(
                collection_name=collection_name,
                field_name="project_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            await client.create_payload_index(
                collection_name=collection_name,
                field_name="resource_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            await client.create_payload_index(
                collection_name=collection_name,
                field_name="resource_type",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            # Legacy index for backward compatibility
            await client.create_payload_index(
                collection_name=collection_name,
                field_name="document_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            logger.info(f"[Qdrant] Collection '{collection_name}' created with payload indexes")
        else:
            logger.info(f"[Qdrant] Collection '{collection_name}' already exists")
    except Exception as e:
        logger.error(f"[Qdrant] Failed to ensure collection exists: {e}")
        raise


class QdrantVectorStore(VectorStore):
    """Qdrant vector store implementation."""

    def __init__(self, client: AsyncQdrantClient | None = None):
        """Initialize Qdrant vector store.

        Args:
            client: Optional pre-configured Qdrant client.
                   If not provided, will use singleton client.
        """
        self._client = client
        self._settings = get_settings()
        self._collection_name = self._settings.qdrant_collection_name

    async def _get_client(self) -> AsyncQdrantClient:
        """Get the Qdrant client."""
        if self._client is not None:
            return self._client
        return await get_qdrant_client()

    async def search(
        self,
        query_embedding: list[float],
        project_id: UUID,
        limit: int = 5,
        document_id: UUID | None = None,
        user_id: str | None = None,
    ) -> list[SearchResult]:
        """Search for similar chunks using Qdrant.

        Args:
            query_embedding: Vector embedding of the query
            project_id: Project UUID to filter by
            limit: Maximum number of results to return
            document_id: Optional document UUID to filter by
            user_id: Optional user ID for data isolation (reserved for future use)

        Returns:
            List of SearchResult sorted by similarity
        """
        client = await self._get_client()

        # Build filter conditions
        must_conditions = [
            FieldCondition(
                key="project_id",
                match=MatchValue(value=str(project_id)),
            )
        ]

        if document_id:
            must_conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=str(document_id)),
                )
            )

        if user_id:
            must_conditions.append(
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id),
                )
            )

        logger.info(
            f"[Qdrant] Search: project_id={project_id}, document_id={document_id}, user_id={user_id}, limit={limit}"
        )

        try:
            results = await client.query_points(
                collection_name=self._collection_name,
                query=query_embedding,
                query_filter=Filter(must=must_conditions),
                limit=limit,
                with_payload=True,
            )

            search_results = []
            for point in results.points:
                payload = point.payload or {}
                search_results.append(
                    SearchResult(
                        chunk_id=UUID(payload.get("chunk_id", str(point.id))),
                        document_id=UUID(payload.get("document_id", "")),
                        content=payload.get("content", ""),
                        page_number=payload.get("page_number", 0),
                        similarity=point.score,
                    )
                )

            logger.info(f"[Qdrant] Found {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"[Qdrant] Search failed: {e}")
            raise

    async def hybrid_search(
        self,
        query_embedding: list[float],
        query_text: str,
        project_id: UUID,
        limit: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        k: int = 20,
        document_id: UUID | None = None,
        user_id: str | None = None,
    ) -> list[SearchResult]:
        """Hybrid search combining vector similarity and keyword matching.

        Note: Initial implementation uses vector-only search.
        True hybrid search with sparse vectors can be added later.

        Args:
            query_embedding: Vector embedding of the query
            query_text: Original query text (currently unused)
            project_id: Project UUID to filter by
            limit: Maximum number of results to return
            vector_weight: Weight for vector search (currently unused)
            keyword_weight: Weight for keyword search (currently unused)
            k: Number of results to retrieve (currently unused)
            document_id: Optional document UUID to filter by
            user_id: Optional user ID for data isolation (reserved for future use)

        Returns:
            List of SearchResult sorted by similarity
        """
        # TODO: Implement true hybrid search with sparse vectors
        # For now, fall back to vector-only search
        logger.info("[Qdrant] Hybrid search falling back to vector-only search")
        return await self.search(
            query_embedding=query_embedding,
            project_id=project_id,
            limit=limit,
            document_id=document_id,
            user_id=user_id,
        )

    async def upsert(
        self,
        chunk_id: UUID,
        document_id: UUID,
        project_id: UUID,
        content: str,
        embedding: list[float],
        page_number: int = 0,
    ) -> None:
        """Upsert a chunk with its embedding to Qdrant.

        Args:
            chunk_id: Unique chunk identifier
            document_id: Document this chunk belongs to
            project_id: Project this chunk belongs to
            content: Text content of the chunk
            embedding: Vector embedding of the content
            page_number: Page number in the source document
        """
        client = await self._get_client()

        point = PointStruct(
            id=str(chunk_id),
            vector=embedding,
            payload={
                "chunk_id": str(chunk_id),
                "document_id": str(document_id),
                "project_id": str(project_id),
                "content": content,
                "page_number": page_number,
            },
        )

        try:
            await client.upsert(
                collection_name=self._collection_name,
                points=[point],
            )
            logger.debug(f"[Qdrant] Upserted chunk: {chunk_id}")
        except Exception as e:
            logger.error(f"[Qdrant] Upsert failed: {e}")
            raise

    async def delete_by_document(self, document_id: UUID) -> None:
        """Delete all chunks for a document.

        Args:
            document_id: Document UUID to delete chunks for
        """
        client = await self._get_client()

        try:
            await client.delete(
                collection_name=self._collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=str(document_id)),
                        )
                    ]
                ),
            )
            logger.info(f"[Qdrant] Deleted chunks for document: {document_id}")
        except Exception as e:
            logger.error(f"[Qdrant] Delete failed: {e}")
            raise

    # =========================================================================
    # Unified Resource Chunk Methods (new API)
    # =========================================================================

    async def upsert_resource_chunk(
        self,
        chunk_id: UUID,
        resource_id: UUID,
        resource_type: ResourceType,
        project_id: UUID,
        chunk_index: int,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        user_id: str | None = None,
    ) -> None:
        """Upsert a resource chunk with unified payload schema.

        Args:
            chunk_id: Unique chunk identifier
            resource_id: Parent resource ID
            resource_type: Type of resource (document, video, etc.)
            project_id: Project this chunk belongs to
            chunk_index: Position within the resource
            content: Text content of the chunk
            embedding: Vector embedding
            metadata: Type-specific metadata (title, platform, timestamps, etc.)
            user_id: Optional user ID for data isolation
        """
        await self.upsert_resource_chunks_batch(
            [
                {
                    "chunk_id": chunk_id,
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "project_id": project_id,
                    "chunk_index": chunk_index,
                    "content": content,
                    "embedding": embedding,
                    "metadata": metadata,
                    "user_id": user_id,
                }
            ]
        )

    async def upsert_resource_chunks_batch(
        self,
        chunks_data: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> None:
        """Upsert multiple resource chunks in batches.

        Args:
            chunks_data: List of dictionaries containing chunk data
            batch_size: Maximum number of points per upsert call
        """
        if not chunks_data:
            return

        client = await self._get_client()
        points = []

        for data in chunks_data:
            metadata = data["metadata"]

            # Build unified payload
            payload = {
                "chunk_id": str(data["chunk_id"]),
                "resource_id": str(data["resource_id"]),
                "resource_type": data["resource_type"].value,
                "project_id": str(data["project_id"]),
                "chunk_index": data["chunk_index"],
                "content": data["content"],
                # Metadata fields
                "title": metadata.get("title", ""),
                "platform": metadata.get("platform", "local"),
                "page_number": metadata.get("page_number"),
                "start_time": metadata.get("start_time"),
                "end_time": metadata.get("end_time"),
                # Legacy compatibility
                "document_id": str(data["resource_id"]),
                # User isolation
                "user_id": data.get("user_id"),
            }

            points.append(
                PointStruct(
                    id=str(data["chunk_id"]),
                    vector=data["embedding"],
                    payload=payload,
                )
            )

        # Upsert in batches
        total_points = len(points)
        for i in range(0, total_points, batch_size):
            batch = points[i : i + batch_size]
            try:
                await client.upsert(
                    collection_name=self._collection_name,
                    points=batch,
                )
                logger.debug(f"[Qdrant] Upserted batch of {len(batch)} chunks")
            except Exception as e:
                logger.error(f"[Qdrant] Batch upsert failed: {e}")
                raise

    async def search_resource_chunks(
        self,
        query_embedding: List[float],
        project_id: UUID,
        limit: int = 5,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[UUID] = None,
    ) -> List[ChunkSearchResult]:
        """Search for similar resource chunks with type filtering.

        Args:
            query_embedding: Vector embedding of the query
            project_id: Project UUID to filter by
            limit: Maximum number of results
            resource_type: Optional filter by resource type
            resource_id: Optional filter by specific resource

        Returns:
            List of ChunkSearchResult sorted by similarity
        """
        client = await self._get_client()

        # Build filter conditions
        must_conditions = [
            FieldCondition(
                key="project_id",
                match=MatchValue(value=str(project_id)),
            )
        ]

        if resource_type:
            must_conditions.append(
                FieldCondition(
                    key="resource_type",
                    match=MatchValue(value=resource_type.value),
                )
            )

        if resource_id:
            must_conditions.append(
                FieldCondition(
                    key="resource_id",
                    match=MatchValue(value=str(resource_id)),
                )
            )

        logger.info(
            f"[Qdrant] Resource search: project={project_id}, type={resource_type}, limit={limit}"
        )

        try:
            results = await client.query_points(
                collection_name=self._collection_name,
                query=query_embedding,
                query_filter=Filter(must=must_conditions),
                limit=limit,
                with_payload=True,
            )

            search_results = []
            for point in results.points:
                payload = point.payload or {}

                # Determine resource type
                rt_str = payload.get("resource_type", "document")
                try:
                    rt = ResourceType(rt_str)
                except ValueError:
                    rt = ResourceType.DOCUMENT

                # Build metadata from payload
                metadata = {
                    "title": payload.get("title", ""),
                    "platform": payload.get("platform", "local"),
                }
                if payload.get("page_number") is not None:
                    metadata["page_number"] = payload["page_number"]
                if payload.get("start_time") is not None:
                    metadata["start_time"] = payload["start_time"]
                if payload.get("end_time") is not None:
                    metadata["end_time"] = payload["end_time"]

                search_results.append(
                    ChunkSearchResult(
                        chunk_id=UUID(payload.get("chunk_id", str(point.id))),
                        resource_id=UUID(
                            payload.get("resource_id", payload.get("document_id", ""))
                        ),
                        resource_type=rt,
                        content=payload.get("content", ""),
                        similarity=point.score,
                        metadata=metadata,
                    )
                )

            logger.info(f"[Qdrant] Found {len(search_results)} resource chunks")
            return search_results

        except Exception as e:
            logger.error(f"[Qdrant] Resource search failed: {e}")
            raise

    async def delete_by_resource(self, resource_id: UUID) -> None:
        """Delete all chunks for a resource.

        Args:
            resource_id: Resource UUID to delete chunks for
        """
        client = await self._get_client()

        try:
            # Try both resource_id and document_id for compatibility
            await client.delete(
                collection_name=self._collection_name,
                points_selector=Filter(
                    should=[
                        FieldCondition(
                            key="resource_id",
                            match=MatchValue(value=str(resource_id)),
                        ),
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=str(resource_id)),
                        ),
                    ]
                ),
            )
            logger.info(f"[Qdrant] Deleted chunks for resource: {resource_id}")
        except Exception as e:
            logger.error(f"[Qdrant] Delete by resource failed: {e}")
            raise
