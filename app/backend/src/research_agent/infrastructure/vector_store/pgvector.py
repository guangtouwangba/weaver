"""pgvector implementation for vector search."""

from typing import List
from uuid import UUID

from sqlalchemy import text, bindparam
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.vector_store.base import SearchResult, VectorStore


class PgVectorStore(VectorStore):
    """PostgreSQL pgvector implementation."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def search(
        self,
        query_embedding: List[float],
        project_id: UUID,
        limit: int = 5,
    ) -> List[SearchResult]:
        """Search for similar chunks using pgvector."""
        # Convert embedding to pgvector format string
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        # Use explicit parameter binding for asyncpg compatibility
        query = text("""
            SELECT 
                id,
                document_id,
                content,
                page_number,
                1 - (embedding <=> cast(:embedding as vector)) AS similarity
            FROM document_chunks
            WHERE project_id = cast(:project_id as uuid)
                AND embedding IS NOT NULL
            ORDER BY embedding <=> cast(:embedding as vector)
            LIMIT :limit
        """).bindparams(
            bindparam("embedding", value=embedding_str),
            bindparam("project_id", value=str(project_id)),
            bindparam("limit", value=limit),
        )

        result = await self._session.execute(query)

        rows = result.fetchall()
        return [
            SearchResult(
                chunk_id=row.id,
                document_id=row.document_id,
                content=row.content,
                page_number=row.page_number or 0,
                similarity=float(row.similarity),
            )
            for row in rows
        ]

