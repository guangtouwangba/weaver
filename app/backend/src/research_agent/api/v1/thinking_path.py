"""Thinking Path API endpoints for automatic thinking path generation."""

import asyncio
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db, get_embedding_service
from research_agent.application.services.thinking_path_service import (
    ThinkingPathAnalysisResult,
    ThinkingPathService,
)
from research_agent.domain.entities.chat import ChatMessage
from research_agent.infrastructure.database.repositories.sqlalchemy_chat_repo import (
    SQLAlchemyChatRepository,
)
from research_agent.infrastructure.embedding.openrouter import OpenRouterEmbeddingService
from research_agent.shared.utils.logger import logger

router = APIRouter()


class ThinkingPathSettingsRequest(BaseModel):
    """Request to update thinking path settings."""

    auto_generate_enabled: bool = True


class ThinkingPathAnalyzeRequest(BaseModel):
    """Request to analyze conversation and generate thinking path."""

    message_id: Optional[str] = None  # Specific message to analyze
    start_index: int = 0  # For batch analysis
    max_messages: int = 20


class ThinkingPathAnalyzeResponse(BaseModel):
    """Response from thinking path analysis."""

    nodes_created: int
    edges_created: int
    duplicate_count: int
    error: Optional[str] = None


class ThinkingPathStatusResponse(BaseModel):
    """Status of thinking path service."""

    auto_generate_enabled: bool
    websocket_connections: int
    cached_embeddings: int


@router.post(
    "/projects/{project_id}/thinking-path/analyze",
    response_model=ThinkingPathAnalyzeResponse,
)
async def analyze_conversation(
    project_id: UUID,
    request: ThinkingPathAnalyzeRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    embedding_service: OpenRouterEmbeddingService = Depends(get_embedding_service),
) -> ThinkingPathAnalyzeResponse:
    """
    Analyze conversation and generate thinking path nodes.

    This endpoint triggers batch analysis of chat messages to generate
    a thinking path visualization. The analysis runs asynchronously
    and broadcasts results via WebSocket.

    Use this when:
    - Enabling auto-generation for the first time (analyze existing messages)
    - Manually triggering analysis for specific messages
    - Catching up on missed messages
    """
    try:
        # Get chat history
        chat_repo = SQLAlchemyChatRepository(session)
        messages = await chat_repo.get_history(project_id, limit=100)

        if not messages:
            return ThinkingPathAnalyzeResponse(
                nodes_created=0,
                edges_created=0,
                duplicate_count=0,
            )

        # Create service
        service = ThinkingPathService(embedding_service=embedding_service)

        # Run batch analysis
        result = await service.analyze_conversation_batch(
            project_id=str(project_id),
            messages=messages,
            start_index=request.start_index,
        )

        return ThinkingPathAnalyzeResponse(
            nodes_created=len(result.nodes),
            edges_created=len(result.edges),
            duplicate_count=len(result.duplicate_mappings),
            error=result.error,
        )

    except Exception as e:
        logger.error(f"[ThinkingPath API] Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/thinking-path/trigger/{message_id}")
async def trigger_analysis_for_message(
    project_id: UUID,
    message_id: UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    embedding_service: OpenRouterEmbeddingService = Depends(get_embedding_service),
) -> dict:
    """
    Trigger thinking path analysis for a specific message.

    This is called internally after a chat message is saved.
    The analysis runs in the background and broadcasts results via WebSocket.
    """
    try:
        # Get the specific message and recent history
        chat_repo = SQLAlchemyChatRepository(session)
        messages = await chat_repo.get_history(project_id, limit=20)

        # Find the target message
        target_message = None
        for msg in messages:
            if msg.id == message_id:
                target_message = msg
                break

        if not target_message:
            raise HTTPException(status_code=404, detail="Message not found")

        # Get existing canvas nodes for duplicate detection
        # Simplified: in production, you'd get from canvas repository
        existing_nodes = []

        # Create service and process
        service = ThinkingPathService(embedding_service=embedding_service)

        # Run analysis in background
        background_tasks.add_task(
            _process_message_background,
            service=service,
            project_id=str(project_id),
            message=target_message,
            existing_nodes=existing_nodes,
            existing_messages=messages,
        )

        return {
            "status": "processing",
            "message_id": str(message_id),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ThinkingPath API] Trigger failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _process_message_background(
    service: ThinkingPathService,
    project_id: str,
    message: ChatMessage,
    existing_nodes: list,
    existing_messages: list,
) -> None:
    """Background task to process a message for thinking path."""
    try:
        await service.process_new_message(
            project_id=project_id,
            message=message,
            existing_nodes=existing_nodes,
            existing_messages=existing_messages,
        )
    except Exception as e:
        logger.error(f"[ThinkingPath] Background processing failed: {e}", exc_info=True)


@router.delete("/projects/{project_id}/thinking-path/cache")
async def clear_cache(
    project_id: UUID,
    embedding_service: OpenRouterEmbeddingService = Depends(get_embedding_service),
) -> dict:
    """
    Clear the thinking path embedding cache for a project.

    Useful when nodes are deleted or content is significantly changed.
    """
    service = ThinkingPathService(embedding_service=embedding_service)
    service.clear_cache(str(project_id))

    return {"status": "cache_cleared", "project_id": str(project_id)}
