"""System maintenance API endpoints.

This module provides endpoints for system maintenance tasks like:
- Scheduled file cleanup
- Database maintenance
- Health checks
"""


from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db
from research_agent.config import get_settings
from research_agent.domain.entities.task import TaskStatus, TaskType
from research_agent.infrastructure.database.repositories.sqlalchemy_pending_cleanup_repo import (
    SQLAlchemyPendingCleanupRepository,
)
from research_agent.shared.utils.logger import logger
from research_agent.worker.service import TaskQueueService

router = APIRouter(prefix="/maintenance", tags=["maintenance"])
settings = get_settings()


class CleanupRequest(BaseModel):
    """Request model for cleanup operations."""

    batch_size: int = 100


class CleanupStatus(BaseModel):
    """Response model for cleanup status."""

    pending_count: int
    message: str
    task_id: str | None = None


class PendingCleanupInfo(BaseModel):
    """Info about a pending cleanup record."""

    id: str
    file_path: str
    storage_type: str
    attempts: int
    max_attempts: int
    last_error: str | None
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
    task = await task_service.push(
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


class TaskQueueStatus(BaseModel):
    """Response model for task queue status."""

    environment: str
    pending_count: int
    processing_count: int
    completed_count: int
    failed_count: int
    total_count: int
    message: str


@router.get("/tasks/status", response_model=TaskQueueStatus)
async def get_task_queue_status(
    session: AsyncSession = Depends(get_db),
) -> TaskQueueStatus:
    """
    Get the current status of the task queue.

    This endpoint helps diagnose why documents might not be processing.
    Returns counts of tasks by status in the current environment.
    """
    task_service = TaskQueueService(session)

    # Get counts for each status
    pending_tasks = await task_service.get_tasks_by_status(TaskStatus.PENDING, limit=1000)
    processing_tasks = await task_service.get_tasks_by_status(TaskStatus.PROCESSING, limit=1000)
    completed_tasks = await task_service.get_tasks_by_status(TaskStatus.COMPLETED, limit=100)
    failed_tasks = await task_service.get_tasks_by_status(TaskStatus.FAILED, limit=100)

    pending_count = len(pending_tasks)
    processing_count = len(processing_tasks)
    completed_count = len(completed_tasks)
    failed_count = len(failed_tasks)
    total_count = pending_count + processing_count + completed_count + failed_count

    message = f"Task queue status for environment '{settings.environment}': "
    if pending_count > 0:
        message += f"{pending_count} pending, "
    if processing_count > 0:
        message += f"{processing_count} processing, "
    if failed_count > 0:
        message += f"{failed_count} failed, "
    message += f"{completed_count} completed (total: {total_count})"

    if pending_count > 0 and processing_count == 0:
        message += ". ⚠️  Warning: Tasks are pending but none are processing. Check if BackgroundWorker is running."

    return TaskQueueStatus(
        environment=settings.environment,
        pending_count=pending_count,
        processing_count=processing_count,
        completed_count=completed_count,
        failed_count=failed_count,
        total_count=total_count,
        message=message,
    )


class DatabaseDiagnostics(BaseModel):
    """Response model for database diagnostics."""

    database_url_prefix: str
    tables_exist: dict
    alembic_version: str | None
    message: str


@router.get("/db/diagnostics", response_model=DatabaseDiagnostics)
async def get_database_diagnostics(
    session: AsyncSession = Depends(get_db),
) -> DatabaseDiagnostics:
    """
    Check database health and table existence.

    Useful for diagnosing migration issues.
    """
    from sqlalchemy import text

    # Get database URL prefix (hide credentials)
    db_url = settings.database_url or "not set"
    if "@" in db_url:
        # Hide password: postgresql://user:pass@host -> postgresql://user:***@host
        parts = db_url.split("@")
        prefix = parts[0].rsplit(":", 1)[0] if ":" in parts[0] else parts[0]
        db_url_prefix = f"{prefix}:***@{parts[1][:50]}..."
    else:
        db_url_prefix = db_url[:50] + "..."

    # Check which tables exist
    required_tables = [
        "projects",
        "documents",
        "chunks",
        "task_queue",
        "entities",
        "relations",
        "canvases",
        "alembic_version",
    ]
    tables_exist = {}

    for table in required_tables:
        try:
            result = await session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
            tables_exist[table] = True
        except Exception as e:
            if "does not exist" in str(e):
                tables_exist[table] = False
            else:
                tables_exist[table] = f"error: {str(e)[:50]}"

    # Get alembic version
    alembic_version = None
    try:
        result = await session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
        row = result.fetchone()
        if row:
            alembic_version = row[0]
    except Exception:
        pass

    # Build message
    missing_tables = [t for t, exists in tables_exist.items() if exists is False]
    if missing_tables:
        message = f"❌ Missing tables: {', '.join(missing_tables)}. Run: alembic upgrade head"
    elif alembic_version:
        message = f"✅ All required tables exist. Alembic version: {alembic_version}"
    else:
        message = "✅ Tables exist but alembic_version not found"

    return DatabaseDiagnostics(
        database_url_prefix=db_url_prefix,
        tables_exist=tables_exist,
        alembic_version=alembic_version,
        message=message,
    )
