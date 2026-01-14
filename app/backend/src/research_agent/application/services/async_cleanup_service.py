"""Async file cleanup service.

This service handles asynchronous deletion of files from storage.
It uses a fire-and-forget pattern with a fallback queue for failed deletions.

Design Pattern: Fire-and-Forget + Scheduled Cleanup
- On document delete: Record pending cleanup, then fire async task
- Async task: Delete files, then remove from pending_cleanups
- Scheduled job: Periodically retry failed cleanups
"""

import asyncio
from uuid import UUID

from research_agent.infrastructure.database.repositories.sqlalchemy_pending_cleanup_repo import (
    SQLAlchemyPendingCleanupRepository,
)
from research_agent.infrastructure.database.session import get_async_session
from research_agent.infrastructure.storage.local import LocalStorageService
from research_agent.infrastructure.storage.supabase_storage import (
    SupabaseStorageService,
    get_supabase_storage,
)
from research_agent.shared.utils.logger import logger


async def cleanup_file_async(
    file_path: str,
    local_storage: LocalStorageService | None = None,
    supabase_storage: SupabaseStorageService | None = None,
    cleanup_id: UUID | None = None,
) -> bool:
    """
    Asynchronously clean up a file from storage.

    Args:
        file_path: Path to the file to delete
        local_storage: Local storage service instance
        supabase_storage: Supabase storage service instance
        cleanup_id: ID of the pending cleanup record (for removal on success)

    Returns:
        True if cleanup succeeded, False otherwise
    """
    success = True
    errors = []

    # Try to delete from Supabase Storage
    if supabase_storage and file_path:
        storage_path = file_path
        # Convert local path to Supabase path if needed
        if "projects/" in storage_path and not storage_path.startswith("projects/"):
            idx = storage_path.find("projects/")
            storage_path = storage_path[idx:]

        if storage_path.startswith("projects/"):
            try:
                logger.info(f"[AsyncCleanup] Deleting from Supabase: {storage_path}")
                await supabase_storage.delete_file(storage_path)
                logger.info(f"[AsyncCleanup] Deleted from Supabase: {storage_path}")
            except Exception as e:
                logger.warning(f"[AsyncCleanup] Failed to delete from Supabase: {e}")
                errors.append(f"Supabase: {e}")
                success = False

    # Try to delete from local storage
    if local_storage and file_path:
        try:
            logger.info(f"[AsyncCleanup] Deleting from local: {file_path}")
            await local_storage.delete(file_path)
            logger.info(f"[AsyncCleanup] Deleted from local: {file_path}")
        except Exception as e:
            logger.warning(f"[AsyncCleanup] Failed to delete from local: {e}")
            errors.append(f"Local: {e}")
            success = False

    # Remove from pending_cleanups if successful
    if success and cleanup_id:
        try:
            async with get_async_session() as session:
                cleanup_repo = SQLAlchemyPendingCleanupRepository(session)
                await cleanup_repo.remove(cleanup_id)
                await session.commit()
                logger.info(f"[AsyncCleanup] Removed pending cleanup: {cleanup_id}")
        except Exception as e:
            logger.warning(f"[AsyncCleanup] Failed to remove pending cleanup: {e}")

    # Update pending_cleanups if failed
    if not success and cleanup_id:
        try:
            async with get_async_session() as session:
                cleanup_repo = SQLAlchemyPendingCleanupRepository(session)
                await cleanup_repo.increment_attempt(
                    cleanup_id, error="; ".join(errors)
                )
                await session.commit()
                logger.info(f"[AsyncCleanup] Updated pending cleanup attempt: {cleanup_id}")
        except Exception as e:
            logger.warning(f"[AsyncCleanup] Failed to update pending cleanup: {e}")

    return success


def fire_and_forget_cleanup(
    file_path: str,
    local_storage: LocalStorageService | None = None,
    supabase_storage: SupabaseStorageService | None = None,
    cleanup_id: UUID | None = None,
) -> None:
    """
    Fire-and-forget file cleanup.

    This schedules an async task without waiting for it to complete.
    The caller can return immediately while cleanup happens in the background.

    Args:
        file_path: Path to the file to delete
        local_storage: Local storage service instance
        supabase_storage: Supabase storage service instance
        cleanup_id: ID of the pending cleanup record
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, create a task
            asyncio.create_task(
                cleanup_file_async(
                    file_path=file_path,
                    local_storage=local_storage,
                    supabase_storage=supabase_storage,
                    cleanup_id=cleanup_id,
                )
            )
        else:
            # We're not in an async context, run the coroutine
            loop.run_until_complete(
                cleanup_file_async(
                    file_path=file_path,
                    local_storage=local_storage,
                    supabase_storage=supabase_storage,
                    cleanup_id=cleanup_id,
                )
            )
    except RuntimeError:
        # No event loop, create one
        asyncio.run(
            cleanup_file_async(
                file_path=file_path,
                local_storage=local_storage,
                supabase_storage=supabase_storage,
                cleanup_id=cleanup_id,
            )
        )


async def process_pending_cleanups(
    local_storage: LocalStorageService,
    batch_size: int = 100,
) -> int:
    """
    Process pending cleanups from the database.

    This is meant to be called by a scheduled job (e.g., cron).

    Args:
        local_storage: Local storage service instance
        batch_size: Maximum number of cleanups to process in one batch

    Returns:
        Number of successfully processed cleanups
    """
    supabase_storage = get_supabase_storage()
    processed = 0

    try:
        async with get_async_session() as session:
            cleanup_repo = SQLAlchemyPendingCleanupRepository(session)
            pending = await cleanup_repo.find_pending(limit=batch_size)

            logger.info(f"[ScheduledCleanup] Found {len(pending)} pending cleanups")

            for cleanup in pending:
                success = await cleanup_file_async(
                    file_path=cleanup.file_path,
                    local_storage=local_storage,
                    supabase_storage=supabase_storage,
                    cleanup_id=cleanup.id,
                )
                if success:
                    processed += 1

            await session.commit()

    except Exception as e:
        logger.error(f"[ScheduledCleanup] Error processing pending cleanups: {e}")

    logger.info(f"[ScheduledCleanup] Processed {processed} cleanups successfully")
    return processed
