"""SQLAlchemy implementation of memory repository for RAG memory optimization."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.database.models import ChatMemoryModel, ChatSummaryModel
from research_agent.shared.utils.logger import logger


@dataclass
class MemorySearchResult:
    """Result from memory search."""

    id: UUID
    content: str
    similarity: float
    metadata: Optional[Dict[str, Any]]
    created_at: datetime


class SQLAlchemyMemoryRepository:
    """
    SQLAlchemy implementation of memory repository.

    Handles both long-term episodic memory (ChatMemoryModel) and
    short-term working memory (ChatSummaryModel).
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    # ==========================================================================
    # Long-Term Episodic Memory (ChatMemoryModel)
    # ==========================================================================

    async def add_memory(
        self,
        project_id: UUID,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChatMemoryModel:
        """
        Add a new memory (Q&A pair) to the episodic memory store.

        Args:
            project_id: Project UUID
            content: The formatted Q&A pair (e.g., "User: <q>\nAssistant: <a>")
            embedding: Vector embedding for semantic search
            metadata: Optional metadata (topic, entities, etc.)

        Returns:
            The created ChatMemoryModel
        """
        memory = ChatMemoryModel(
            project_id=project_id,
            content=content,
            embedding=embedding,
            memory_metadata=metadata or {},
        )
        self._session.add(memory)
        await self._session.commit()
        await self._session.refresh(memory)

        logger.debug(f"[Memory] Added memory {memory.id} for project {project_id}")
        return memory

    async def search_memories(
        self,
        project_id: UUID,
        query_embedding: List[float],
        limit: int = 5,
        min_similarity: float = 0.5,
    ) -> List[MemorySearchResult]:
        """
        Search for similar memories using vector similarity.

        Args:
            project_id: Project UUID to search within
            query_embedding: Query vector for similarity search
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold (0-1, cosine)

        Returns:
            List of MemorySearchResult sorted by similarity (descending)
        """
        # Use cosine similarity: 1 - cosine_distance
        # pgvector uses <=> for cosine distance
        query = text(
            """
            SELECT
                id,
                content,
                memory_metadata,
                created_at,
                1 - (embedding <=> :query_embedding::vector) as similarity
            FROM chat_memories
            WHERE project_id = :project_id
                AND embedding IS NOT NULL
                AND 1 - (embedding <=> :query_embedding::vector) >= :min_similarity
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :limit
            """
        )

        result = await self._session.execute(
            query,
            {
                "project_id": str(project_id),
                "query_embedding": str(query_embedding),
                "limit": limit,
                "min_similarity": min_similarity,
            },
        )
        rows = result.fetchall()

        memories = [
            MemorySearchResult(
                id=row.id,
                content=row.content,
                similarity=row.similarity,
                metadata=row.memory_metadata,
                created_at=row.created_at,
            )
            for row in rows
        ]

        logger.debug(
            f"[Memory] Found {len(memories)} memories for project {project_id} "
            f"(min_similarity={min_similarity})"
        )
        return memories

    async def get_recent_memories(
        self,
        project_id: UUID,
        limit: int = 10,
    ) -> List[ChatMemoryModel]:
        """
        Get the most recent memories for a project.

        Args:
            project_id: Project UUID
            limit: Maximum number of results

        Returns:
            List of ChatMemoryModel sorted by created_at (descending)
        """
        stmt = (
            select(ChatMemoryModel)
            .where(ChatMemoryModel.project_id == project_id)
            .order_by(ChatMemoryModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_memories_for_project(self, project_id: UUID) -> int:
        """
        Delete all memories for a project.

        Args:
            project_id: Project UUID

        Returns:
            Number of deleted memories
        """
        stmt = text("DELETE FROM chat_memories WHERE project_id = :project_id")
        result = await self._session.execute(stmt, {"project_id": str(project_id)})
        await self._session.commit()
        return result.rowcount

    # ==========================================================================
    # Short-Term Working Memory (ChatSummaryModel)
    # ==========================================================================

    async def get_session_summary(self, project_id: UUID) -> Optional[ChatSummaryModel]:
        """
        Get the session summary for a project.

        Args:
            project_id: Project UUID

        Returns:
            ChatSummaryModel or None if not exists
        """
        stmt = select(ChatSummaryModel).where(ChatSummaryModel.project_id == project_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_session_summary(
        self,
        project_id: UUID,
        summary: str,
        summarized_message_count: int,
    ) -> ChatSummaryModel:
        """
        Update or create the session summary for a project.

        Args:
            project_id: Project UUID
            summary: The summarized conversation content
            summarized_message_count: Number of messages that have been summarized

        Returns:
            The updated/created ChatSummaryModel
        """
        existing = await self.get_session_summary(project_id)

        if existing:
            existing.summary = summary
            existing.summarized_message_count = summarized_message_count
            await self._session.commit()
            await self._session.refresh(existing)
            logger.debug(f"[Memory] Updated session summary for project {project_id}")
            return existing
        else:
            new_summary = ChatSummaryModel(
                project_id=project_id,
                summary=summary,
                summarized_message_count=summarized_message_count,
            )
            self._session.add(new_summary)
            await self._session.commit()
            await self._session.refresh(new_summary)
            logger.debug(f"[Memory] Created session summary for project {project_id}")
            return new_summary

    async def clear_session_summary(self, project_id: UUID) -> bool:
        """
        Clear the session summary for a project.

        Args:
            project_id: Project UUID

        Returns:
            True if summary was deleted, False if not found
        """
        existing = await self.get_session_summary(project_id)
        if existing:
            await self._session.delete(existing)
            await self._session.commit()
            logger.debug(f"[Memory] Cleared session summary for project {project_id}")
            return True
        return False


