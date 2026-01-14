"""pgvector implementation for vector search with hybrid search support."""

import asyncio
from typing import Any
from uuid import UUID

from sqlalchemy import bindparam, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.vector_store.base import SearchResult, VectorStore
from research_agent.shared.utils.logger import logger


class PgVectorStore(VectorStore):
    """PostgreSQL pgvector implementation with hybrid search."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def _ensure_clean_transaction(self) -> None:
        """
        Ensure the session is in a clean transaction state.
        Rollback if there's a failed transaction.
        """
        try:
            # Check if connection is in a failed transaction by attempting a simple query
            # If it fails with InFailedSQLTransactionError, we need to rollback
            await self._session.execute(text("SELECT 1"))
        except DBAPIError as e:
            if "InFailedSQLTransactionError" in str(e) or "current transaction is aborted" in str(
                e
            ):
                logger.warning("Detected failed transaction state, rolling back...")
                await self._session.rollback()
            else:
                raise

    async def search(
        self,
        query_embedding: list[float],
        project_id: UUID,
        limit: int = 5,
        document_id: UUID | None = None,
        user_id: str | None = None,
    ) -> list[SearchResult]:
        """
        Search for similar chunks using pgvector.
        This is the original vector-only search for backward compatibility.
        """
        # Ensure clean transaction state before executing query
        await self._ensure_clean_transaction()

        # Convert embedding to pgvector format string
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        # Build query
        where_clause = "project_id = cast(:project_id as uuid) AND embedding IS NOT NULL"
        params = {
            "embedding": embedding_str,
            "project_id": str(project_id),
            "limit": limit,
        }

        if user_id:
            where_clause += " AND user_id = :user_id"
            params["user_id"] = user_id

        # Debug logging for search parameters
        debug_params = params.copy()
        debug_params["embedding"] = "..."  # Truncate for logging
        logger.info(
            f"[VectorStore] Search Prams: project_id={project_id}, document_id={document_id}, user_id={user_id}, limit={limit}"
        )

        if document_id:
            where_clause += " AND resource_id = cast(:document_id as uuid)"
            params["document_id"] = str(document_id)

        # Use explicit parameter binding for asyncpg compatibility
        query = text(f"""
            SELECT
                id,
                resource_id as document_id,
                content,
                (metadata->>'page_number')::int as page_number,
                1 - (embedding <=> cast(:embedding as vector)) AS similarity
            FROM resource_chunks
            WHERE {where_clause}
            ORDER BY embedding <=> cast(:embedding as vector)
            LIMIT :limit
        """).bindparams(*[bindparam(k, value=v) for k, v in params.items()])

        try:
            result = await self._session.execute(query)
        except DBAPIError as e:
            if "InFailedSQLTransactionError" in str(e) or "current transaction is aborted" in str(
                e
            ):
                logger.warning("Transaction failed during search, rolling back and retrying...")
                await self._session.rollback()
                result = await self._session.execute(query)
            else:
                raise

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

    async def hybrid_search(
        self,
        query_embedding: list[float],
        query_text: str,
        project_id: UUID,
        limit: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        k: int = 20,  # Retrieve top-k from each method before fusion
        document_id: UUID | None = None,
        user_id: str | None = None,
    ) -> list[SearchResult]:
        """
        Hybrid search combining vector similarity and full-text search using RRF.

        Args:
            query_embedding: Vector embedding of the query
            query_text: Original query text for keyword search
            project_id: Project UUID
            limit: Final number of results to return
            vector_weight: Weight for vector search (0-1)
            keyword_weight: Weight for keyword search (0-1)
            k: Number of results to retrieve from each method before fusion
            user_id: Optional user ID for isolation

        Returns:
            List of SearchResult sorted by RRF score
        """
        logger.info(
            f"Hybrid search: vector_weight={vector_weight}, keyword_weight={keyword_weight}, k={k}, user_id={user_id}"
        )

        # Ensure clean transaction state before parallel searches
        await self._ensure_clean_transaction()

        # Run both searches in parallel
        vector_results, keyword_results = await asyncio.gather(
            self._vector_search(query_embedding, project_id, k, document_id, user_id),
            self._keyword_search(query_text, project_id, k, document_id, user_id),
        )

        # Apply Reciprocal Rank Fusion (RRF)
        fused_results = self._reciprocal_rank_fusion(
            vector_results=vector_results,
            keyword_results=keyword_results,
            vector_weight=vector_weight,
            keyword_weight=keyword_weight,
            limit=limit,
        )

        logger.info(f"Hybrid search returned {len(fused_results)} results")
        return fused_results

    async def _vector_search(
        self,
        query_embedding: list[float],
        project_id: UUID,
        limit: int,
        document_id: UUID | None = None,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Vector similarity search returning raw results."""
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        where_clause = "project_id = cast(:project_id as uuid) AND embedding IS NOT NULL"
        params = {
            "embedding": embedding_str,
            "project_id": str(project_id),
            "limit": limit,
        }

        if user_id:
            where_clause += " AND user_id = :user_id"
            params["user_id"] = user_id

        if document_id:
            where_clause += " AND resource_id = cast(:document_id as uuid)"
            params["document_id"] = str(document_id)

        query = text(f"""
            SELECT
                id,
                resource_id as document_id,
                content,
                (metadata->>'page_number')::int as page_number,
                1 - (embedding <=> cast(:embedding as vector)) AS score
            FROM resource_chunks
            WHERE {where_clause}
            ORDER BY embedding <=> cast(:embedding as vector)
            LIMIT :limit
        """).bindparams(*[bindparam(k, value=v) for k, v in params.items()])

        try:
            result = await self._session.execute(query)
        except DBAPIError as e:
            if "InFailedSQLTransactionError" in str(e) or "current transaction is aborted" in str(
                e
            ):
                logger.warning(
                    "Transaction failed during vector search, rolling back and retrying..."
                )
                await self._session.rollback()
                result = await self._session.execute(query)
            else:
                raise

        rows = result.fetchall()

        return [
            {
                "id": row.id,
                "document_id": row.document_id,
                "content": row.content,
                "page_number": row.page_number or 0,
                "score": float(row.score),
            }
            for row in rows
        ]

    async def _keyword_search(
        self,
        query_text: str,
        project_id: UUID,
        limit: int,
        document_id: UUID | None = None,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Full-text search using PostgreSQL TSVector."""
        # Sanitize query text for tsquery
        # Replace special characters and prepare for websearch_to_tsquery
        sanitized_query = query_text.strip()

        where_clause = "project_id = cast(:project_id as uuid) AND content_tsvector @@ websearch_to_tsquery('english', :query)"
        params = {
            "query": sanitized_query,
            "project_id": str(project_id),
            "limit": limit,
        }

        if user_id:
            where_clause += " AND user_id = :user_id"
            params["user_id"] = user_id

        if document_id:
            where_clause += " AND resource_id = cast(:document_id as uuid)"
            params["document_id"] = str(document_id)

        query = text(f"""
            SELECT
                id,
                resource_id as document_id,
                content,
                (metadata->>'page_number')::int as page_number,
                ts_rank_cd(content_tsvector, websearch_to_tsquery('english', :query)) AS score
            FROM resource_chunks
            WHERE {where_clause}
            ORDER BY score DESC
            LIMIT :limit
        """).bindparams(*[bindparam(k, value=v) for k, v in params.items()])

        try:
            result = await self._session.execute(query)
        except DBAPIError as e:
            if "InFailedSQLTransactionError" in str(e) or "current transaction is aborted" in str(
                e
            ):
                logger.warning(
                    "Transaction failed during keyword search, rolling back and retrying..."
                )
                await self._session.rollback()
                result = await self._session.execute(query)
            else:
                raise

        rows = result.fetchall()

        return [
            {
                "id": row.id,
                "document_id": row.document_id,
                "content": row.content,
                "page_number": row.page_number or 0,
                "score": float(row.score) if row.score else 0.0,
            }
            for row in rows
        ]

    def _reciprocal_rank_fusion(
        self,
        vector_results: list[dict[str, Any]],
        keyword_results: list[dict[str, Any]],
        vector_weight: float,
        keyword_weight: float,
        limit: int,
        k: int = 60,  # RRF constant
    ) -> list[SearchResult]:
        """
        Combine results using Reciprocal Rank Fusion (RRF).

        RRF Score = Σ (weight / (k + rank))

        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
            vector_weight: Weight for vector scores
            keyword_weight: Weight for keyword scores
            limit: Number of final results
            k: RRF constant (default 60)

        Returns:
            Fused and ranked results
        """
        # Build rank maps for both result sets
        vector_ranks = {str(r["id"]): (i + 1, r) for i, r in enumerate(vector_results)}
        keyword_ranks = {str(r["id"]): (i + 1, r) for i, r in enumerate(keyword_results)}

        # Get all unique chunk IDs
        all_ids = set(vector_ranks.keys()) | set(keyword_ranks.keys())

        # Calculate RRF scores
        fused_scores = {}
        for chunk_id in all_ids:
            rrf_score = 0.0
            result_data = None

            # Add vector contribution
            if chunk_id in vector_ranks:
                rank, data = vector_ranks[chunk_id]
                rrf_score += vector_weight / (k + rank)
                result_data = data

            # Add keyword contribution
            if chunk_id in keyword_ranks:
                rank, data = keyword_ranks[chunk_id]
                rrf_score += keyword_weight / (k + rank)
                if result_data is None:
                    result_data = data

            fused_scores[chunk_id] = (rrf_score, result_data)

        # Sort by RRF score and take top-k
        sorted_results = sorted(fused_scores.items(), key=lambda x: x[1][0], reverse=True)[:limit]

        # Convert to SearchResult objects
        return [
            SearchResult(
                chunk_id=UUID(chunk_id),
                document_id=data["document_id"],
                content=data["content"],
                page_number=data["page_number"],
                similarity=score,  # Use RRF score as similarity
            )
            for chunk_id, (score, data) in sorted_results
        ]
