"""Chat API endpoints."""

import json
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db, get_embedding_service, get_llm_service
from research_agent.shared.utils.logger import logger
from research_agent.application.dto.chat import (
    ChatHistoryResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    HistoryMessage,
    SourceReference,
)
from research_agent.application.use_cases.chat.get_history import (
    GetHistoryInput,
    GetHistoryUseCase,
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
from research_agent.infrastructure.database.repositories.sqlalchemy_chat_repo import (
    SQLAlchemyChatRepository,
)
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
    start_time = time.time()
    
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
    
    # Log chat request with question for Grafana
    duration_ms = round((time.time() - start_time) * 1000, 2)
    question_short = request.message[:200] + "..." if len(request.message) > 200 else request.message
    logger.info(
        f"ChatRequest: endpoint_type=chat duration_ms={duration_ms} "
        f"question_length={len(request.message)} question=\"{question_short}\" | "
        f"JSON: {json.dumps({'endpoint_type': 'chat', 'duration_ms': duration_ms, 'question': question_short, 'question_length': len(request.message)}, ensure_ascii=False)}"
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
    
    start_time = time.time()
    question_short = request.message[:200] + "..." if len(request.message) > 200 else request.message
    
    # Log chat stream request start with question for Grafana
    logger.info(
        f"ChatStreamStart: endpoint_type=chat_stream question_length={len(request.message)} "
        f"question=\"{question_short}\" | "
        f"JSON: {json.dumps({'endpoint_type': 'chat_stream', 'question': question_short, 'question_length': len(request.message)}, ensure_ascii=False)}"
    )

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
                # Log stream completion with duration
                duration_ms = round((time.time() - start_time) * 1000, 2)
                logger.info(
                    f"ChatStreamEnd: endpoint_type=chat_stream duration_ms={duration_ms} "
                    f"question_length={len(request.message)} | "
                    f"JSON: {json.dumps({'endpoint_type': 'chat_stream', 'duration_ms': duration_ms, 'question_length': len(request.message)}, ensure_ascii=False)}"
                )
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


@router.get("/projects/{project_id}/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    project_id: UUID,
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
) -> ChatHistoryResponse:
    """Get chat history for a project."""
    chat_repo = SQLAlchemyChatRepository(session)
    use_case = GetHistoryUseCase(chat_repo)

    result = await use_case.execute(GetHistoryInput(project_id=project_id, limit=limit))

    return ChatHistoryResponse(
        messages=[
            HistoryMessage(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                created_at=m.created_at,
            )
            for m in result.messages
        ]
    )
