"""ARQ Worker Configuration for Redis-based task queue.

ARQ is a lightweight async task queue built on Redis.
This module configures the worker settings and task definitions.
"""

from typing import Any, Dict, Optional

from arq import cron
from arq.connections import RedisSettings

from research_agent.config import get_settings

settings = get_settings()


def get_redis_settings() -> RedisSettings:
    """
    Get Redis connection settings from environment.

    Supports both standard Redis URL and Upstash Redis.
    """
    redis_url = settings.redis_url

    if not redis_url:
        # Default to local Redis for development
        return RedisSettings(host="localhost", port=6379)

    # Parse Redis URL: redis://user:password@host:port/db
    # Upstash format: redis://default:xxx@xxx.upstash.io:6379
    from urllib.parse import urlparse

    parsed = urlparse(redis_url)

    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=int(parsed.path.lstrip("/") or 0) if parsed.path else 0,
        # Use SSL for cloud Redis (Upstash, etc.)
        ssl=parsed.scheme == "rediss" or "upstash" in (parsed.hostname or ""),
        ssl_cert_reqs="none" if "upstash" in (parsed.hostname or "") else "required",
    )


# =============================================================================
# Task Functions
# =============================================================================
# ARQ tasks are simple async functions that receive a context dict as first arg


async def process_document(ctx: Dict[str, Any], payload: Dict[str, Any]) -> None:
    """
    Process an uploaded document through the full pipeline.

    Pipeline:
    1. Download file (if from Supabase Storage)
    2. Extract text from PDF
    3. Generate summary and page mapping
    4. Chunk text
    5. Generate embeddings (optional for long_context mode)
    6. Update document status to READY

    Args:
        ctx: ARQ context (contains redis connection, job info, etc.)
        payload: Task payload containing:
            - document_id: UUID of the document
            - project_id: UUID of the project
            - file_path: Path to the file
    """
    import asyncio
    from uuid import UUID

    from research_agent.api.services.notification import document_notification_service
    from research_agent.domain.models.document import DocumentStatus
    from research_agent.infrastructure.database.models import DocumentModel
    from research_agent.infrastructure.database.session import get_async_session
    from research_agent.shared.utils.logger import logger
    from research_agent.worker.tasks.document_processor import DocumentProcessorTask

    logger.info(f"📥 ARQ: Starting document processing - payload={payload}")

    document_id = payload.get("document_id")
    project_id = payload.get("project_id")
    task = DocumentProcessorTask()

    async with get_async_session() as session:
        try:
            await task.execute(payload, session)
            logger.info(f"✅ ARQ: Document processing completed - document_id={document_id}")
        except asyncio.CancelledError:
            # Handle timeout cancellation - update document status to ERROR
            logger.error(f"⏱️ ARQ: Document processing timed out - document_id={document_id}")
            try:
                async with get_async_session() as error_session:
                    doc = await error_session.get(DocumentModel, UUID(document_id))
                    if doc:
                        doc.status = DocumentStatus.ERROR
                        doc.error_message = "处理超时，请稍后重试或联系支持"
                        await error_session.commit()
                        logger.info(f"✅ Updated document {document_id} status to ERROR (timeout)")

                        # Notify frontend
                        await document_notification_service.notify_document_status(
                            project_id=str(project_id),
                            document_id=str(document_id),
                            status="error",
                            error="处理超时，请稍后重试",
                        )
            except Exception as update_err:
                logger.error(f"❌ Failed to update document status after timeout: {update_err}")
            raise  # Re-raise to let ARQ know the job failed
        except Exception as e:
            logger.error(f"❌ ARQ: Document processing failed - {e}", exc_info=True)
            raise  # Re-raise to let ARQ handle retry


async def cleanup_files(ctx: Dict[str, Any], payload: Dict[str, Any]) -> None:
    """
    Clean up orphaned files from storage.

    Args:
        ctx: ARQ context
        payload: Task payload containing file paths to clean
    """
    from research_agent.infrastructure.database.session import get_async_session
    from research_agent.shared.utils.logger import logger
    from research_agent.worker.tasks.file_cleanup import FileCleanupTask

    logger.info(f"📥 ARQ: Starting file cleanup - payload={payload}")

    task = FileCleanupTask()

    async with get_async_session() as session:
        try:
            await task.execute(payload, session)
            logger.info("✅ ARQ: File cleanup completed")
        except Exception as e:
            logger.error(f"❌ ARQ: File cleanup failed - {e}", exc_info=True)
            raise


async def cleanup_canvas(ctx: Dict[str, Any], payload: Dict[str, Any]) -> None:
    """
    Clean up orphaned canvas nodes.

    Args:
        ctx: ARQ context
        payload: Task payload containing cleanup criteria
    """
    from research_agent.infrastructure.database.session import get_async_session
    from research_agent.shared.utils.logger import logger
    from research_agent.worker.tasks.canvas_cleanup import CanvasCleanupTask

    logger.info(f"📥 ARQ: Starting canvas cleanup - payload={payload}")

    task = CanvasCleanupTask()

    async with get_async_session() as session:
        try:
            await task.execute(payload, session)
            logger.info("✅ ARQ: Canvas cleanup completed")
        except Exception as e:
            logger.error(f"❌ ARQ: Canvas cleanup failed - {e}", exc_info=True)
            raise


async def generate_thumbnail(ctx: Dict[str, Any], payload: Dict[str, Any]) -> None:
    """
    Generate PDF thumbnail image.

    Args:
        ctx: ARQ context
        payload: Task payload containing:
            - document_id: UUID of the document
            - project_id: UUID of the project
            - file_path: Path to the PDF file
    """
    from research_agent.infrastructure.database.session import get_async_session
    from research_agent.shared.utils.logger import logger
    from research_agent.worker.tasks.thumbnail_generator import ThumbnailGeneratorTask

    logger.info(f"📥 ARQ: Starting thumbnail generation - payload={payload}")

    task = ThumbnailGeneratorTask()

    async with get_async_session() as session:
        try:
            await task.execute(payload, session)
            logger.info(
                f"✅ ARQ: Thumbnail generation completed - document_id={payload.get('document_id')}"
            )
        except Exception as e:
            logger.error(f"❌ ARQ: Thumbnail generation failed - {e}", exc_info=True)
            raise


async def process_url(ctx: Dict[str, Any], payload: Dict[str, Any]) -> None:
    """
    Extract content from a URL.

    Args:
        ctx: ARQ context
        payload: Task payload containing:
            - url_content_id: UUID of the UrlContent record
            - url: The URL to extract content from
    """
    from research_agent.infrastructure.database.session import get_async_session
    from research_agent.shared.utils.logger import logger
    from research_agent.worker.tasks.url_processor import URLProcessorTask

    logger.info(f"📥 ARQ: Starting URL extraction - payload={payload}")

    task = URLProcessorTask()

    async with get_async_session() as session:
        try:
            await task.execute(payload, session)
            logger.info(
                f"✅ ARQ: URL extraction completed - url_content_id={payload.get('url_content_id')}"
            )
        except Exception as e:
            logger.error(f"❌ ARQ: URL extraction failed - {e}", exc_info=True)
            raise


# =============================================================================
# Scheduled Tasks (Cron Jobs)
# =============================================================================


async def scheduled_cleanup(ctx: Dict[str, Any]) -> None:
    """
    Scheduled task to clean up failed file cleanups.
    Runs every hour to retry any failed cleanup operations.
    """
    from research_agent.shared.utils.logger import logger

    logger.info("🕐 Running scheduled cleanup...")

    # TODO: Implement cleanup of pending_cleanups table entries
    # This replaces the old database-based cleanup retry mechanism

    logger.info("✅ Scheduled cleanup completed")


# =============================================================================
# Worker Settings
# =============================================================================


class WorkerSettings:
    """
    ARQ Worker configuration.

    This class is passed to arq.Worker to configure the worker behavior.
    """

    # Redis connection
    redis_settings = get_redis_settings()

    # Task functions to register
    functions = [
        process_document,
        cleanup_files,
        cleanup_canvas,
        generate_thumbnail,
        process_url,
    ]

    # Scheduled tasks (cron jobs)
    cron_jobs = [
        cron(scheduled_cleanup, hour={0, 6, 12, 18}, minute=0),  # Run every 6 hours
    ]

    # Worker settings
    max_jobs = 3  # Maximum concurrent jobs
    job_timeout = 1800  # 30 minutes timeout (large PDFs with OCR can take 20+ mins)
    max_tries = 3  # Retry failed jobs up to 3 times
    retry_jobs = True  # Enable automatic retry on failure

    # Health check interval
    health_check_interval = 30  # seconds

    # Queue name (allows multiple queues for different priorities)
    queue_name = f"arq:queue:{settings.environment}"

    # Logging
    @staticmethod
    async def on_startup(ctx: Dict[str, Any]) -> None:
        """Called when worker starts."""
        from research_agent.shared.utils.logger import logger

        logger.info(f"🚀 ARQ Worker started - environment={settings.environment}")

    @staticmethod
    async def on_shutdown(ctx: Dict[str, Any]) -> None:
        """Called when worker shuts down."""
        from research_agent.shared.utils.logger import logger

        logger.info("🛑 ARQ Worker shutting down")

    @staticmethod
    async def on_job_start(ctx: Dict[str, Any]) -> None:
        """Called when a job starts."""
        from research_agent.shared.utils.logger import logger

        job_id = ctx.get("job_id", "unknown")
        logger.debug(f"▶️  Job {job_id} starting")

    @staticmethod
    async def on_job_end(ctx: Dict[str, Any]) -> None:
        """Called when a job ends."""
        from research_agent.shared.utils.logger import logger

        job_id = ctx.get("job_id", "unknown")
        logger.debug(f"⏹️  Job {job_id} ended")


# =============================================================================
# Helper Functions for Task Enqueueing
# =============================================================================


async def get_redis_pool():
    """
    Get a Redis connection pool for enqueueing jobs.

    Usage:
        pool = await get_redis_pool()
        await pool.enqueue_job('process_document', payload)
        await pool.close()
    """
    from arq import create_pool

    return await create_pool(get_redis_settings())


async def enqueue_task(
    task_name: str,
    payload: Dict[str, Any],
    job_id: Optional[str] = None,
    defer_by: Optional[int] = None,
) -> str:
    """
    Enqueue a task to the Redis queue.

    Args:
        task_name: Name of the task function (e.g., 'process_document')
        payload: Task payload dict
        job_id: Optional custom job ID (defaults to auto-generated UUID)
        defer_by: Optional delay in seconds before job starts

    Returns:
        Job ID
    """
    from arq import create_pool

    from research_agent.shared.utils.logger import logger

    pool = await create_pool(get_redis_settings())

    try:
        job = await pool.enqueue_job(
            task_name,
            payload,
            _job_id=job_id,
            _defer_by=defer_by,
            _queue_name=f"arq:queue:{settings.environment}",
        )

        if job:
            logger.info(f"📤 Enqueued task '{task_name}' with job_id={job.job_id}")
            return job.job_id
        else:
            logger.warning(f"⚠️  Task '{task_name}' may already exist with same job_id")
            return job_id or "unknown"
    finally:
        await pool.close()
