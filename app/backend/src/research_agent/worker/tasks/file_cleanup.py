"""File cleanup task for processing pending file deletions.

This task is designed to be run periodically (e.g., via cron or scheduled task)
to clean up files that failed to delete during the async deletion process.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.application.services.async_cleanup_service import (
    cleanup_file_async,
)
from research_agent.config import get_settings
from research_agent.infrastructure.database.repositories.sqlalchemy_pending_cleanup_repo import (
    SQLAlchemyPendingCleanupRepository,
)
from research_agent.infrastructure.storage.local import LocalStorageService
from research_agent.infrastructure.storage.supabase_storage import get_supabase_storage
from research_agent.shared.utils.logger import logger
from research_agent.worker.tasks.base import BaseTask


class FileCleanupTask(BaseTask):
    """Task to process pending file cleanups."""

    @property
    def task_type(self) -> str:
        return "file_cleanup"

    async def execute(self, payload: dict[str, Any], session: AsyncSession) -> None:
        """
        Execute the file cleanup task.

        Payload options:
        - batch_size (int): Maximum number of cleanups to process (default: 100)
        - single_file (str): If provided, only clean up this specific file path

        Args:
            payload: Task-specific data
            session: Database session for the task
        """
        settings = get_settings()
        local_storage = LocalStorageService(settings.upload_dir)
        supabase_storage = get_supabase_storage()

        batch_size = payload.get("batch_size", 100)
        single_file = payload.get("single_file")

        cleanup_repo = SQLAlchemyPendingCleanupRepository(session)

        if single_file:
            # Clean up a specific file
            logger.info(f"[FileCleanupTask] Processing single file: {single_file}")
            await self._cleanup_single_file(
                single_file, local_storage, supabase_storage, cleanup_repo
            )
        else:
            # Process batch of pending cleanups
            await self._process_batch(
                batch_size, local_storage, supabase_storage, cleanup_repo, session
            )

    async def _cleanup_single_file(
        self,
        file_path: str,
        local_storage: LocalStorageService,
        supabase_storage,
        cleanup_repo: SQLAlchemyPendingCleanupRepository,
    ) -> None:
        """Clean up a single file."""
        success = await cleanup_file_async(
            file_path=file_path,
            local_storage=local_storage,
            supabase_storage=supabase_storage,
            cleanup_id=None,
        )

        if success:
            # Remove from pending cleanups
            await cleanup_repo.remove_by_file_path(file_path)
            logger.info(f"[FileCleanupTask] Successfully cleaned up: {file_path}")
        else:
            logger.warning(f"[FileCleanupTask] Failed to clean up: {file_path}")

    async def _process_batch(
        self,
        batch_size: int,
        local_storage: LocalStorageService,
        supabase_storage,
        cleanup_repo: SQLAlchemyPendingCleanupRepository,
        session: AsyncSession,
    ) -> None:
        """Process a batch of pending cleanups."""
        pending = await cleanup_repo.find_pending(limit=batch_size)
        logger.info(f"[FileCleanupTask] Found {len(pending)} pending cleanups")

        success_count = 0
        fail_count = 0

        for cleanup in pending:
            try:
                success = await cleanup_file_async(
                    file_path=cleanup.file_path,
                    local_storage=local_storage,
                    supabase_storage=supabase_storage,
                    cleanup_id=cleanup.id,
                )

                if success:
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                logger.error(
                    f"[FileCleanupTask] Error cleaning up {cleanup.file_path}: {e}"
                )
                await cleanup_repo.increment_attempt(cleanup.id, error=str(e))
                fail_count += 1

        # Commit the session to persist changes
        await session.commit()

        logger.info(
            f"[FileCleanupTask] Batch complete: {success_count} success, {fail_count} failed"
        )
