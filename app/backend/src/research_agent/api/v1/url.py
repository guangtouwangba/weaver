"""URL extraction API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db
from research_agent.application.dto.url_content import (
    URLExtractRequest,
    URLExtractResponse,
    URLExtractStatusResponse,
)
from research_agent.domain.entities.task import TaskType
from research_agent.infrastructure.database.models import UrlContentModel
from research_agent.infrastructure.database.repositories.sqlalchemy_url_content_repo import (
    SQLAlchemyUrlContentRepository,
)
from research_agent.infrastructure.url_extractor import detect_platform, normalize_url
from research_agent.shared.utils.logger import logger
from research_agent.worker.service import TaskQueueService

router = APIRouter(prefix="/url", tags=["url"])


def get_repo(session: AsyncSession = Depends(get_db)) -> SQLAlchemyUrlContentRepository:
    """Get URL content repository."""
    return SQLAlchemyUrlContentRepository(session)


@router.post("/extract", response_model=URLExtractResponse, status_code=202)
async def extract_url(
    request: URLExtractRequest,
    repo: SQLAlchemyUrlContentRepository = Depends(get_repo),
    session: AsyncSession = Depends(get_db),
) -> URLExtractResponse:
    """
    Extract content from a URL.

    This endpoint creates a URL content record and enqueues an async task
    to extract the content. The response is returned immediately with
    status="pending". Poll the GET endpoint to check extraction progress.

    Args:
        request: URL extraction request containing the URL

    Returns:
        URLExtractResponse with pending status
    """
    url = request.url
    normalized = normalize_url(url)

    logger.info(f"[URL API] Extract request: url={url}, normalized={normalized}")

    # Check for existing extraction (deduplication)
    if not request.force:
        existing = await repo.get_by_normalized_url(normalized)
        if existing:
            # Only return cached if completed successfully
            if existing.status == "completed":
                logger.info(f"[URL API] Returning cached completed extraction: id={existing.id}")
                return URLExtractResponse.model_validate(existing)
            # If pending/processing, re-queue the task
            elif existing.status in ("pending", "processing"):
                logger.info(f"[URL API] Re-queuing extraction for pending record: id={existing.id}")
                try:
                    task_service = TaskQueueService(session)
                    task = await task_service.push(
                        task_type=TaskType.PROCESS_URL,
                        payload={
                            "url_content_id": str(existing.id),
                            "url": url,
                        },
                        priority=0,
                    )
                    await session.commit()
                    logger.info(f"[URL API] Re-queued extraction task: task_id={task.id}")
                except Exception as e:
                    logger.warning(f"[URL API] Failed to re-queue task (may already exist): {e}")
                return URLExtractResponse.model_validate(existing)
            # If failed, return the failed record (user can use force=true to retry)
            else:
                logger.info(f"[URL API] Returning cached failed extraction: id={existing.id}")
                return URLExtractResponse.model_validate(existing)

    # Detect platform
    platform, video_id = detect_platform(url)
    content_type = "video" if platform in ("youtube", "bilibili", "douyin") else "article"

    # Create new URL content record
    url_content = UrlContentModel(
        url=url,
        normalized_url=normalized,
        platform=platform,
        content_type=content_type,
        status="pending",
        meta_data={
            "video_id": video_id,
        } if video_id else {},
    )

    created = await repo.create(url_content)
    logger.info(f"[URL API] Created URL content: id={created.id}, platform={platform}")

    # Enqueue extraction task using database-backed queue
    try:
        task_service = TaskQueueService(session)
        task = await task_service.push(
            task_type=TaskType.PROCESS_URL,
            payload={
                "url_content_id": str(created.id),
                "url": url,
            },
            priority=0,
        )
        await session.commit()
        logger.info(f"[URL API] Enqueued extraction task: task_id={task.id}")
    except Exception as e:
        logger.error(f"[URL API] Failed to enqueue task: {e}", exc_info=True)
        # Update status to failed
        await repo.update_status(created.id, status="failed", error_message=str(e))
        await session.commit()
        raise HTTPException(status_code=500, detail=f"Failed to enqueue extraction task: {e}")

    return URLExtractResponse.model_validate(created)


@router.get("/extract/{url_content_id}", response_model=URLExtractResponse)
async def get_url_content(
    url_content_id: UUID,
    repo: SQLAlchemyUrlContentRepository = Depends(get_repo),
) -> URLExtractResponse:
    """
    Get URL content by ID.

    Use this endpoint to poll for extraction status.

    Args:
        url_content_id: UUID of the URL content record

    Returns:
        URLExtractResponse with current status and content
    """
    url_content = await repo.get_by_id(url_content_id)
    if not url_content:
        raise HTTPException(status_code=404, detail="URL content not found")

    return URLExtractResponse.model_validate(url_content)


@router.get("/extract/{url_content_id}/status", response_model=URLExtractStatusResponse)
async def get_url_content_status(
    url_content_id: UUID,
    repo: SQLAlchemyUrlContentRepository = Depends(get_repo),
) -> URLExtractStatusResponse:
    """
    Get lightweight status for URL content extraction.

    Optimized for polling - returns minimal data.

    Args:
        url_content_id: UUID of the URL content record

    Returns:
        URLExtractStatusResponse with status
    """
    url_content = await repo.get_by_id(url_content_id)
    if not url_content:
        raise HTTPException(status_code=404, detail="URL content not found")

    return URLExtractStatusResponse(
        id=url_content.id,
        status=url_content.status,
        error_message=url_content.error_message,
        title=url_content.title,
        thumbnail_url=url_content.thumbnail_url,
    )

