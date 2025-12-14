"""System maintenance API endpoints.

This module provides endpoints for system maintenance tasks like:
- Scheduled file cleanup
- Database maintenance
- Health checks
"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db
from research_agent.config import get_settings
from research_agent.domain.entities.task import TaskType
from research_agent.infrastructure.database.repositories.sqlalchemy_pending_cleanup_repo import (
    SQLAlchemyPendingCleanupRepository,
)
from research_agent.worker.service import TaskQueueService
from research_agent.shared.utils.logger import logger

router = APIRouter(prefix="/maintenance", tags=["maintenance"])
settings = get_settings()


class CleanupRequest(BaseModel):
    """Request model for cleanup operations."""

    batch_size: int = 100


class CleanupStatus(BaseModel):
    """Response model for cleanup status."""

    pending_count: int
    message: str
    task_id: Optional[str] = None


class PendingCleanupInfo(BaseModel):
    """Info about a pending cleanup record."""

    id: str
    file_path: str
    storage_type: str
    attempts: int
    max_attempts: int
    last_error: Optional[str]
    created_at: str


class PendingCleanupListResponse(BaseModel):
    """Response model for listing pending cleanups."""

    total: int
    items: list[PendingCleanupInfo]


@router.get("/cleanup/status", response_model=CleanupStatus)
async def get_cleanup_status(
    session: AsyncSession = Depends(get_db),
) -> CleanupStatus:
    """
    Get the current status of pending file cleanups.

    Returns the number of files waiting to be cleaned up.
    """
    cleanup_repo = SQLAlchemyPendingCleanupRepository(session)
    pending = await cleanup_repo.find_pending(limit=1000)

    return CleanupStatus(
        pending_count=len(pending),
        message=f"Found {len(pending)} pending file cleanup(s)",
    )


@router.get("/cleanup/pending", response_model=PendingCleanupListResponse)
async def list_pending_cleanups(
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> PendingCleanupListResponse:
    """
    List all pending file cleanups.

    This is useful for debugging and monitoring the cleanup queue.
    """
    cleanup_repo = SQLAlchemyPendingCleanupRepository(session)
    pending = await cleanup_repo.find_pending(limit=limit)

    items = [
        PendingCleanupInfo(
            id=str(p.id),
            file_path=p.file_path,
            storage_type=p.storage_type,
            attempts=p.attempts,
            max_attempts=p.max_attempts,
            last_error=p.last_error,
            created_at=p.created_at.isoformat() if p.created_at else "",
        )
        for p in pending
    ]

    return PendingCleanupListResponse(total=len(items), items=items)


@router.post("/cleanup/trigger", response_model=CleanupStatus)
async def trigger_cleanup(
    request: CleanupRequest = CleanupRequest(),
    session: AsyncSession = Depends(get_db),
) -> CleanupStatus:
    """
    Trigger a file cleanup task.

    This schedules a background task to clean up pending file deletions.
    Use this to manually trigger cleanup if needed, or set up a cron job
    to call this endpoint periodically.

    The cleanup task will:
    1. Find all pending cleanup records
    2. Attempt to delete files from both local and Supabase storage
    3. Remove successful cleanups from the queue
    4. Update attempt counts for failed cleanups
    """
    cleanup_repo = SQLAlchemyPendingCleanupRepository(session)
    pending = await cleanup_repo.find_pending(limit=request.batch_size)

    if len(pending) == 0:
        return CleanupStatus(
            pending_count=0,
            message="No pending cleanups found",
        )

    # Schedule the cleanup task
    task_service = TaskQueueService(session)
    task = await task_service.enqueue(
        task_type=TaskType.FILE_CLEANUP,
        payload={"batch_size": request.batch_size},
        priority=0,  # Normal priority
    )
    await session.commit()

    logger.info(f"[Maintenance] Scheduled file cleanup task: {task.id}")

    return CleanupStatus(
        pending_count=len(pending),
        message=f"Scheduled cleanup task for {len(pending)} pending file(s)",
        task_id=str(task.id),
    )
