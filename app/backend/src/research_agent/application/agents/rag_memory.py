from typing import Any
from uuid import UUID

from research_agent.domain.services.memory_service import MemoryService
from research_agent.shared.utils.logger import logger


class SessionSummaryMemory:
    """Manages short-term working memory (session summaries)."""

    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service

    async def get_summary(self, project_id: UUID, user_id: str | None = None) -> str:
        """Get the current session summary."""
        try:
            return await self.memory_service.get_session_summary(project_id, user_id)
        except Exception as e:
            logger.error(f"[Memory] Failed to get session summary: {e}")
            return ""

    async def update_summary(
        self, project_id: UUID, messages: list[tuple[str, str]], user_id: str | None = None
    ) -> str:
        """Update session summary based on new messages."""
        try:
            # Check if summarization is needed logic could be here or in service
            # Service has should_summarize and summarize_history
            if await self.memory_service.should_summarize(
                project_id, len(messages), user_id=user_id
            ):
                return await self.memory_service.summarize_history(
                    project_id, messages, user_id=user_id
                )
            return ""
        except Exception as e:
            logger.error(f"[Memory] Failed to update session summary: {e}")
            return ""


class EpisodicMemory:
    """Manages long-term episodic memory (past Q&A)."""

    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service

    async def retrieve(
        self,
        query: str,
        project_id: UUID,
        limit: int = 5,
        min_similarity: float = 0.6,
        user_id: str | None = None,
    ) -> list[Any]:
        """Retrieve relevant past memories."""
        try:
            memories = await self.memory_service.retrieve_relevant_memories(
                project_id, query, limit, min_similarity, user_id
            )
            # Return raw objects, caller can format
            return memories
        except Exception as e:
            logger.error(f"[Memory] Failed to retrieve memories: {e}")
            return []

    async def store(
        self, project_id: UUID, question: str, answer: str, user_id: str | None = None
    ) -> None:
        """Store a new interaction."""
        try:
            await self.memory_service.store_memory(
                project_id=project_id, question=question, answer=answer, user_id=user_id
            )
        except Exception as e:
            logger.error(f"[Memory] Failed to store memory: {e}")


class RAGAgentMemory:
    """
    Unified memory interface for the RAG Agent.
    Combines session summary and episodic memory.
    """

    def __init__(self, session: Any, embedding_service: Any, llm: Any = None):
        self.memory_service = MemoryService(session, embedding_service, llm)
        self.session = SessionSummaryMemory(self.memory_service)
        self.episodic = EpisodicMemory(self.memory_service)

    async def get_session_summary(self, project_id: UUID, user_id: str | None = None) -> str:
        return await self.session.get_summary(project_id, user_id)

    async def retrieve_relevant_memories(
        self, query: str, project_id: UUID, limit: int = 5, user_id: str | None = None
    ) -> list[Any]:
        return await self.episodic.retrieve(query, project_id, limit, 0.6, user_id=user_id)

    async def store_interaction(
        self, question: str, answer: str, project_id: UUID, user_id: str | None = None
    ) -> None:
        await self.episodic.store(project_id, question, answer, user_id)
