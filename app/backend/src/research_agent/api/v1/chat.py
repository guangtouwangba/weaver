"""Chat API endpoints."""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db, get_embedding_service, get_llm_service
from research_agent.application.dto.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    SourceReference,
)
from research_agent.application.use_cases.chat.send_message import (
    SendMessageInput,
    SendMessageUseCase,
)
from research_agent.application.use_cases.chat.stream_message import (
    StreamMessageInput,
    StreamMessageUseCase,
)
from research_agent.domain.services.retrieval_service import RetrievalService
from research_agent.infrastructure.embedding.openrouter import OpenRouterEmbeddingService
from research_agent.infrastructure.llm.openrouter import OpenRouterLLMService
from research_agent.infrastructure.vector_store.pgvector import PgVectorStore

router = APIRouter()


@router.post("/projects/{project_id}/chat", response_model=ChatMessageResponse)
async def send_message(
    project_id: UUID,
    request: ChatMessageRequest,
    session: AsyncSession = Depends(get_db),
    llm_service: OpenRouterLLMService = Depends(get_llm_service),
    embedding_service: OpenRouterEmbeddingService = Depends(get_embedding_service),
) -> ChatMessageResponse:
    """Send a chat message and get RAG response."""
    # Create services
    vector_store = PgVectorStore(session)
    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    use_case = SendMessageUseCase(
        retrieval_service=retrieval_service,
        llm_service=llm_service,
    )

    result = await use_case.execute(
        SendMessageInput(
            project_id=project_id,
            message=request.message,
            document_id=request.document_id,
        )
    )

    return ChatMessageResponse(
        answer=result.answer,
        sources=[
            SourceReference(
                document_id=s.document_id,
                page_number=s.page_number,
                snippet=s.snippet,
                similarity=s.similarity,
            )
            for s in result.sources
        ],
    )


@router.post("/projects/{project_id}/chat/stream")
async def stream_message(
    project_id: UUID,
    request: ChatMessageRequest,
    session: AsyncSession = Depends(get_db),
    embedding_service: OpenRouterEmbeddingService = Depends(get_embedding_service),
) -> StreamingResponse:
    """Send a chat message and get streaming RAG response (SSE) using LangGraph."""
    from research_agent.config import get_settings
    settings = get_settings()
    
    use_case = StreamMessageUseCase(
        session=session,
        embedding_service=embedding_service,
        api_key=settings.openrouter_api_key,
        model=settings.llm_model,
    )

    async def event_generator():
        """Generate SSE events."""
        async for event in use_case.execute(
            StreamMessageInput(
                project_id=project_id,
                message=request.message,
                document_id=request.document_id,
            )
        ):
            if event.type == "token":
                data = {"type": "token", "content": event.content}
            elif event.type == "sources":
                data = {
                    "type": "sources",
                    "sources": [
                        {
                            "document_id": str(s.document_id),
                            "page_number": s.page_number,
                            "snippet": s.snippet,
                            "similarity": s.similarity,
                        }
                        for s in (event.sources or [])
                    ],
                }
            elif event.type == "error":
                data = {"type": "error", "content": event.content}
            else:
                data = {"type": "done"}

            yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
