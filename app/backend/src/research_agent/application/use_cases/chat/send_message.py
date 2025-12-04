"""Send message use case (non-streaming)."""

from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID

from research_agent.config import get_settings
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


def _get_default_top_k() -> int:
    """Get default top_k from settings."""
    return get_settings().retrieval_top_k


@dataclass
class SendMessageInput:
    """Input for send message use case."""

    project_id: UUID
    message: str
    document_id: Optional[UUID] = None
    top_k: int = field(default_factory=_get_default_top_k)


@dataclass
class SendMessageOutput:
    """Output for send message use case."""

    answer: str
    sources: List[SourceRef]


class SendMessageUseCase:
    """Use case for sending a chat message with RAG."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_service: LLMService,
    ):
        self._retrieval_service = retrieval_service
        self._llm_service = llm_service

    async def execute(self, input: SendMessageInput) -> SendMessageOutput:
        """Execute the use case."""
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
            return SendMessageOutput(
                answer="I don't have any relevant information in the documents to answer this question.",
                sources=[],
            )

        # 2. Build context
        context_chunks = [
            {
                "content": r.content,
                "page_number": r.page_number,
            }
            for r in results
        ]

        # 3. Generate answer
        user_prompt = build_rag_prompt(input.message, context_chunks)
        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=user_prompt),
        ]

        logger.info("Generating LLM response...")
        response = await self._llm_service.chat(messages)

        # 4. Build sources
        sources = [
            SourceRef(
                document_id=r.document_id,
                page_number=r.page_number,
                snippet=r.content[:200] + "..." if len(r.content) > 200 else r.content,
                similarity=r.similarity,
            )
            for r in results
        ]

        return SendMessageOutput(
            answer=response.content,
            sources=sources,
        )

