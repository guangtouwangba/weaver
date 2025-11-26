"""Stream message use case (SSE streaming)."""

from dataclasses import dataclass
from typing import AsyncIterator, List, Optional
from uuid import UUID

from research_agent.domain.services.retrieval_service import RetrievalService
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.infrastructure.llm.prompts.rag_prompt import SYSTEM_PROMPT, build_rag_prompt
from research_agent.shared.utils.logger import logger


@dataclass
class SourceRef:
    """Source reference."""

    document_id: UUID
    page_number: int
    snippet: str
    similarity: float


@dataclass
class StreamMessageInput:
    """Input for stream message use case."""

    project_id: UUID
    message: str
    document_id: Optional[UUID] = None
    top_k: int = 5


@dataclass
class StreamEvent:
    """Streaming event."""

    type: str  # "token" | "sources" | "done" | "error"
    content: Optional[str] = None
    sources: Optional[List[SourceRef]] = None


class StreamMessageUseCase:
    """Use case for streaming chat message with RAG."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_service: LLMService,
    ):
        self._retrieval_service = retrieval_service
        self._llm_service = llm_service

    async def execute(self, input: StreamMessageInput) -> AsyncIterator[StreamEvent]:
        """Execute the use case with streaming."""
        # 1. Retrieve relevant chunks
        logger.info(f"Retrieving chunks for query: {input.message[:50]}...")
        results = await self._retrieval_service.retrieve(
            query=input.message,
            project_id=input.project_id,
            top_k=input.top_k,
        )

        # Filter by document if specified
        if input.document_id:
            results = [r for r in results if r.document_id == input.document_id]

        if not results:
            yield StreamEvent(
                type="token",
                content="I don't have any relevant information in the documents to answer this question.",
            )
            yield StreamEvent(type="done")
            return

        # 2. Build context
        context_chunks = [
            {
                "content": r.content,
                "page_number": r.page_number,
            }
            for r in results
        ]

        # 3. Build sources
        sources = [
            SourceRef(
                document_id=r.document_id,
                page_number=r.page_number,
                snippet=r.content[:200] + "..." if len(r.content) > 200 else r.content,
                similarity=r.similarity,
            )
            for r in results
        ]

        # 4. Stream LLM response
        user_prompt = build_rag_prompt(input.message, context_chunks)
        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=user_prompt),
        ]

        logger.info("Streaming LLM response...")
        try:
            async for token in self._llm_service.chat_stream(messages):
                yield StreamEvent(type="token", content=token)

            # Send sources after completion
            yield StreamEvent(type="sources", sources=sources)
            yield StreamEvent(type="done")

        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield StreamEvent(type="error", content=str(e))

