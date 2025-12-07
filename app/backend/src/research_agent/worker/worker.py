"""Background worker that processes tasks from the queue."""

import asyncio
from typing import Callable, Optional

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.task import TaskStatus
from research_agent.shared.utils.logger import logger
from research_agent.worker.dispatcher import TaskDispatcher
from research_agent.worker.service import TaskQueueService


class BackgroundWorker:
    """
    Background worker that polls the task queue and processes tasks.

    Uses a database-backed queue for persistence and supports
    graceful shutdown.
    """

    def __init__(
        self,
        dispatcher: TaskDispatcher,
        session_factory: Callable[[], AsyncSession],
        poll_interval: float = 2.0,
        max_concurrent_tasks: int = 3,
    ):
        """
        Initialize the background worker.

        Args:
            dispatcher: Task dispatcher for routing tasks
            session_factory: Factory function to create database sessions
            poll_interval: Seconds between queue polls when idle
            max_concurrent_tasks: Maximum number of concurrent tasks
        """
        self._dispatcher = dispatcher
        self._session_factory = session_factory
        self._poll_interval = poll_interval
        self._max_concurrent_tasks = max_concurrent_tasks
        self._running = False
        self._current_tasks: set = set()
        self._shutdown_event: Optional[asyncio.Event] = None
        self._connection_error_count = 0
        self._max_connection_error_backoff = 60.0  # Max 60 seconds between retries

    async def start(self) -> None:
        """Start the background worker."""
        if self._running:
            logger.warning("Worker is already running")
            return

        self._running = True
        self._shutdown_event = asyncio.Event()

        from research_agent.config import get_settings

        env_settings = get_settings()

        logger.info("Background worker started")
        logger.info(f"Environment: {env_settings.environment}")  # ✅ Show current environment
        logger.info(
            f"Poll interval: {self._poll_interval}s, Max concurrent: {self._max_concurrent_tasks}"
        )
        logger.info(f"Registered task types: {self._dispatcher.get_registered_types()}")
        logger.info(
            f"⚠️  Worker will ONLY process tasks from environment '{env_settings.environment}'"
        )

        # Recover any stuck tasks from previous runs (e.g., after server restart/reload)
        await self._recover_stuck_tasks()

        while self._running:
            wait_time = self._poll_interval

            try:
                await self._poll_and_process()
                # Reset error count on successful poll
                self._connection_error_count = 0
            except (OperationalError, ConnectionError, TimeoutError, OSError) as e:
                # Database connection errors - use exponential backoff
                self._connection_error_count += 1
                error_type = type(e).__name__
                error_message = str(e)

                # Calculate backoff time (exponential, capped at max)
                wait_time = min(
                    self._poll_interval * (2 ** min(self._connection_error_count - 1, 5)),
                    self._max_connection_error_backoff,
                )

                # Log with appropriate level based on error count
                if self._connection_error_count <= 3:
                    logger.warning(
                        f"⚠️  Database connection error (attempt {self._connection_error_count}): "
                        f"{error_type}: {error_message[:200]}. Retrying in {wait_time:.1f}s..."
                    )
                elif self._connection_error_count % 10 == 0:
                    # Only log every 10th error to avoid spam
                    logger.error(
                        f"❌ Database connection still failing after {self._connection_error_count} attempts: "
                        f"{error_type}: {error_message[:200]}. Retrying in {wait_time:.1f}s... "
                        f"Please check DATABASE_URL configuration."
                    )
            except Exception as e:
                # Other errors - log and continue with normal poll interval
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                self._connection_error_count = 0  # Reset on non-connection errors
                wait_time = self._poll_interval

            # Wait before next poll (with backoff for connection errors)
            try:
                await asyncio.wait_for(self._shutdown_event.wait(), timeout=wait_time)
                # Shutdown was signaled
                break
            except asyncio.TimeoutError:
                # Normal timeout, continue polling
                pass

        logger.info("Background worker stopped")

    async def stop(self) -> None:
        """Stop the background worker gracefully."""
        if not self._running:
            return

        logger.info("Stopping background worker...")
        self._running = False

        if self._shutdown_event:
            self._shutdown_event.set()

        # Wait for current tasks to complete (with timeout)
        if self._current_tasks:
            logger.info(f"Waiting for {len(self._current_tasks)} tasks to complete...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._current_tasks, return_exceptions=True), timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for tasks, some tasks may be interrupted")

    async def _recover_stuck_tasks(self) -> None:
        """Recover tasks that were stuck in 'processing' state from previous runs."""
        try:
            async with self._session_factory() as session:
                service = TaskQueueService(session)
                recovered = await service.recover_stuck_tasks()
                if recovered > 0:
                    await session.commit()
                    logger.info(f"🔄 Worker startup: recovered {recovered} stuck task(s)")
        except Exception as e:
            logger.warning(f"⚠️  Failed to recover stuck tasks: {e}")

    async def _poll_and_process(self) -> None:
        """Poll the queue and process available tasks."""
        # Check if we can take more tasks
        if len(self._current_tasks) >= self._max_concurrent_tasks:
            return

        try:
            async with self._session_factory() as session:
                service = TaskQueueService(session)

                # Try to get a task
                task = await service.pop()

                if task:
                    await session.commit()

                    # Process task in background
                    task_coro = self._process_task(task)
                    task_future = asyncio.create_task(task_coro)
                    self._current_tasks.add(task_future)
                    task_future.add_done_callback(self._current_tasks.discard)
        except (OperationalError, ConnectionError, TimeoutError, OSError) as e:
            # Re-raise connection errors to be handled by the main loop
            raise
        except Exception as e:
            # Other errors - log and continue
            logger.error(f"Error in _poll_and_process: {e}", exc_info=True)
            raise

    async def _process_task(self, task) -> None:
        """Process a single task."""
        logger.info(
            f"🔄 Processing task - task_id={task.id}, task_type={task.task_type.value}, "
            f"attempts={task.attempts}/{task.max_attempts}, payload_keys={list(task.payload.keys())}"
        )

        async with self._session_factory() as session:
            service = TaskQueueService(session)

            try:
                # Execute the task
                await self._dispatcher.dispatch(task, session)

                # Mark as completed
                await service.complete(task.id)
                await session.commit()

                logger.info(
                    f"✅ Task completed successfully - task_id={task.id}, "
                    f"task_type={task.task_type.value}"
                )

            except Exception as e:
                error_type = type(e).__name__
                error_message = str(e)

                logger.error(
                    f"❌ Task execution failed - task_id={task.id}, "
                    f"task_type={task.task_type.value}, error_type={error_type}, "
                    f"error={error_message}, attempts={task.attempts}/{task.max_attempts}, "
                    f"payload={task.payload}",
                    exc_info=True,
                )

                try:
                    await session.rollback()
                    logger.debug(f"✅ Session rolled back for task {task.id}")
                except Exception as rollback_error:
                    logger.error(
                        f"❌ Failed to rollback session - task_id={task.id}, "
                        f"rollback_error={rollback_error}",
                        exc_info=True,
                    )

                # Mark as failed
                try:
                    async with self._session_factory() as fail_session:
                        fail_service = TaskQueueService(fail_session)
                        await fail_service.fail(task.id, str(e))
                        await fail_session.commit()
                        logger.info(
                            f"✅ Task marked as failed - task_id={task.id}, "
                            f"error_message={error_message[:200]}"
                        )
                except Exception as fail_error:
                    logger.error(
                        f"❌ CRITICAL: Failed to mark task as failed - task_id={task.id}, "
                        f"original_error={error_message}, fail_error={fail_error}",
                        exc_info=True,
                    )
