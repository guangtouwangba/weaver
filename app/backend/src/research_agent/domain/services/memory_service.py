"""Memory service for RAG memory optimization.

This service handles both short-term (working memory) and long-term (episodic memory)
memory operations for the RAG system.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.database.repositories.sqlalchemy_memory_repo import (
    MemorySearchResult,
    SQLAlchemyMemoryRepository,
)
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.shared.utils.logger import logger

# Configuration constants
DEFAULT_SUMMARY_TOKEN_THRESHOLD = 2000  # Trigger summarization when history exceeds this
DEFAULT_MEMORY_SEARCH_LIMIT = 5
DEFAULT_MEMORY_MIN_SIMILARITY = 0.6


SUMMARIZATION_PROMPT = """You are a conversation summarizer. Your task is to summarize the following conversation history into a concise summary that captures the key points, decisions, and context.

Focus on:
1. Main topics discussed
2. Key decisions or conclusions reached
3. Important context that should be remembered
4. User preferences or requirements mentioned

Keep the summary concise but comprehensive. Write in a neutral, factual tone.

Conversation to summarize:
{conversation}

Summary:"""


@dataclass
class MemoryContext:
    """Context assembled from memory for RAG generation."""

    session_summary: str  # Short-term: summarized older conversation
    recent_history: List[tuple[str, str]]  # Short-term: recent (human, ai) pairs
    relevant_memories: List[MemorySearchResult]  # Long-term: semantically similar past discussions


class MemoryService:
    """
    Service for managing RAG memory.

    Handles:
    - Short-term working memory (session summaries)
    - Long-term episodic memory (vectorized Q&A pairs)
    """

    def __init__(
        self,
        session: AsyncSession,
        embedding_service: EmbeddingService,
        llm: Optional[ChatOpenAI] = None,
    ):
        self._session = session
        self._embedding_service = embedding_service
        self._llm = llm
        self._memory_repo = SQLAlchemyMemoryRepository(session)

    # ==========================================================================
    # Long-Term Episodic Memory
    # ==========================================================================

    async def store_memory(
        self,
        project_id: UUID,
        question: str,
        answer: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Store a Q&A interaction as a memory for future retrieval.

        Args:
            project_id: Project UUID
            question: User's question
            answer: AI's answer
            metadata: Optional metadata (topic, entities, etc.)
            user_id: Optional user ID for data isolation
        """
        # Format the content
        content = f"User: {question}\nAssistant: {answer}"

        # Generate embedding for the Q&A pair
        # We embed the question primarily since that's what we'll search against
        try:
            embedding = await self._embedding_service.embed(question)
        except Exception as e:
            logger.error(f"[Memory] Failed to generate embedding: {e}")
            return

        # Store in database
        try:
            await self._memory_repo.add_memory(
                project_id=project_id,
                content=content,
                embedding=embedding,
                metadata=metadata,
                user_id=user_id,
            )
            logger.info(f"[Memory] Stored memory for project {project_id}")
        except Exception as e:
            logger.error(f"[Memory] Failed to store memory: {e}")

    async def retrieve_relevant_memories(
        self,
        project_id: UUID,
        query: str,
        limit: int = DEFAULT_MEMORY_SEARCH_LIMIT,
        min_similarity: float = DEFAULT_MEMORY_MIN_SIMILARITY,
        user_id: Optional[str] = None,
    ) -> List[MemorySearchResult]:
        """
        Retrieve memories relevant to the current query.

        Args:
            project_id: Project UUID
            query: Current user query
            limit: Maximum number of memories to retrieve
            min_similarity: Minimum similarity threshold
            user_id: Optional user ID for data isolation

        Returns:
            List of relevant memories sorted by similarity
        """
        try:
            # Generate embedding for the query
            query_embedding = await self._embedding_service.embed(query)

            # Search memories
            memories = await self._memory_repo.search_memories(
                project_id=project_id,
                query_embedding=query_embedding,
                limit=limit,
                min_similarity=min_similarity,
                user_id=user_id,
            )

            logger.info(
                f"[Memory] Retrieved {len(memories)} relevant memories for query: {query[:50]}..."
            )
            return memories

        except Exception as e:
            logger.error(f"[Memory] Failed to retrieve memories: {e}")
            return []

    # ==========================================================================
    # Short-Term Working Memory
    # ==========================================================================

    async def get_session_summary(self, project_id: UUID, user_id: Optional[str] = None) -> str:
        """
        Get the current session summary for a project.

        Args:
            project_id: Project UUID
            user_id: Optional user ID for data isolation

        Returns:
            Session summary string (empty if none exists)
        """
        summary_model = await self._memory_repo.get_session_summary(project_id, user_id)
        return summary_model.summary if summary_model else ""

    async def should_summarize(
        self,
        project_id: UUID,
        current_message_count: int,
        threshold: int = 10,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Determine if the conversation should be summarized.

        Args:
            project_id: Project UUID
            current_message_count: Current number of messages in history
            threshold: Number of messages that triggers summarization
            user_id: Optional user ID for data isolation

        Returns:
            True if summarization is needed
        """
        summary_model = await self._memory_repo.get_session_summary(project_id, user_id)
        summarized_count = summary_model.summarized_message_count if summary_model else 0

        # Summarize if we have more than threshold messages beyond what's been summarized
        unsummarized_count = current_message_count - summarized_count
        return unsummarized_count >= threshold

    async def summarize_history(
        self,
        project_id: UUID,
        messages: List[tuple[str, str]],
        keep_recent: int = 3,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Summarize older conversation history.

        Args:
            project_id: Project UUID
            messages: List of (human, ai) message tuples
            keep_recent: Number of recent messages to keep unsummarized
            user_id: Optional user ID for data isolation

        Returns:
            Updated session summary
        """
        if not self._llm:
            logger.warning("[Memory] No LLM provided for summarization")
            return ""

        if len(messages) <= keep_recent:
            logger.debug("[Memory] Not enough messages to summarize")
            return ""

        # Get existing summary
        existing_summary = await self.get_session_summary(project_id, user_id)

        # Messages to summarize (excluding recent ones)
        messages_to_summarize = messages[:-keep_recent] if keep_recent > 0 else messages

        # Format conversation for summarization
        conversation_text = ""
        if existing_summary:
            conversation_text += f"Previous Summary:\n{existing_summary}\n\n"
            conversation_text += "New Conversation:\n"

        for human, ai in messages_to_summarize:
            conversation_text += f"User: {human}\nAssistant: {ai}\n\n"

        # Generate summary using LLM
        try:
            prompt = ChatPromptTemplate.from_messages([("human", SUMMARIZATION_PROMPT)])
            chain = prompt | self._llm | StrOutputParser()

            summary = await chain.ainvoke({"conversation": conversation_text})
            summary = summary.strip()

            # Update in database
            total_summarized = len(messages) - keep_recent
            await self._memory_repo.update_session_summary(
                project_id=project_id,
                summary=summary,
                summarized_message_count=total_summarized,
                user_id=user_id,
            )

            logger.info(
                f"[Memory] Summarized {len(messages_to_summarize)} messages for project {project_id}"
            )
            return summary

        except Exception as e:
            logger.error(f"[Memory] Failed to summarize history: {e}")
            return existing_summary

    # ==========================================================================
    # Combined Memory Context
    # ==========================================================================

    async def get_memory_context(
        self,
        project_id: UUID,
        query: str,
        chat_history: List[tuple[str, str]],
        recent_history_count: int = 3,
        memory_search_limit: int = DEFAULT_MEMORY_SEARCH_LIMIT,
        user_id: Optional[str] = None,
    ) -> MemoryContext:
        """
        Assemble complete memory context for RAG generation.

        This combines:
        - Session summary (summarized older conversation)
        - Recent history (last N conversation turns)
        - Relevant memories (semantically similar past discussions)

        Args:
            project_id: Project UUID
            query: Current user query
            chat_history: Full chat history as (human, ai) tuples
            recent_history_count: Number of recent turns to include directly
            memory_search_limit: Max memories to retrieve
            user_id: Optional user ID for data isolation

        Returns:
            MemoryContext with all assembled context
        """
        # Get session summary
        session_summary = await self.get_session_summary(project_id, user_id)

        # Get recent history (last N turns)
        recent_history = chat_history[-recent_history_count:] if chat_history else []

        # Retrieve relevant memories from long-term store
        relevant_memories = await self.retrieve_relevant_memories(
            project_id=project_id,
            query=query,
            limit=memory_search_limit,
            user_id=user_id,
        )

        return MemoryContext(
            session_summary=session_summary,
            recent_history=recent_history,
            relevant_memories=relevant_memories,
        )

    def format_memory_context_for_prompt(
        self,
        memory_context: MemoryContext,
    ) -> str:
        """
        Format memory context into a string for inclusion in prompts.

        Args:
            memory_context: The assembled memory context

        Returns:
            Formatted string for prompt injection
        """
        parts = []

        # Add session summary if available
        if memory_context.session_summary:
            parts.append(f"## Conversation Summary\n{memory_context.session_summary}")

        # Add relevant memories if available
        if memory_context.relevant_memories:
            memories_text = "\n\n".join(
                f"[Relevance: {m.similarity:.2f}]\n{m.content}"
                for m in memory_context.relevant_memories
            )
            parts.append(f"## Relevant Past Discussions\n{memories_text}")

        # Add recent history
        if memory_context.recent_history:
            recent_text = "\n".join(
                f"User: {human}\nAssistant: {ai}" for human, ai in memory_context.recent_history
            )
            parts.append(f"## Recent Conversation\n{recent_text}")

        return "\n\n".join(parts)
