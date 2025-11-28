"""Background worker that processes tasks from the queue."""

import asyncio
from typing import Callable, Optional

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

    async def start(self) -> None:
        """Start the background worker."""
        if self._running:
            logger.warning("Worker is already running")
            return
        
        self._running = True
        self._shutdown_event = asyncio.Event()
        
        logger.info("Background worker started")
        logger.info(f"Poll interval: {self._poll_interval}s, Max concurrent: {self._max_concurrent_tasks}")
        logger.info(f"Registered task types: {self._dispatcher.get_registered_types()}")
        
        while self._running:
            try:
                await self._poll_and_process()
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
            
            # Wait for poll interval or shutdown signal
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self._poll_interval
                )
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
                    asyncio.gather(*self._current_tasks, return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for tasks, some tasks may be interrupted")

    async def _poll_and_process(self) -> None:
        """Poll the queue and process available tasks."""
        # Check if we can take more tasks
        if len(self._current_tasks) >= self._max_concurrent_tasks:
            return
        
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

    async def _process_task(self, task) -> None:
        """Process a single task."""
        logger.info(f"Processing task {task.id} ({task.task_type.value})")
        
        async with self._session_factory() as session:
            service = TaskQueueService(session)
            
            try:
                # Execute the task
                await self._dispatcher.dispatch(task, session)
                
                # Mark as completed
                await service.complete(task.id)
                await session.commit()
                
                logger.info(f"Task {task.id} completed successfully")
                
            except Exception as e:
                await session.rollback()
                
                # Mark as failed
                async with self._session_factory() as fail_session:
                    fail_service = TaskQueueService(fail_session)
                    await fail_service.fail(task.id, str(e))
                    await fail_session.commit()
                
                logger.error(f"Task {task.id} failed: {e}", exc_info=True)

