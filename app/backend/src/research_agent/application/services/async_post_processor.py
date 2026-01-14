"""Async Post-Processor for fire-and-forget background tasks.

Decouples post-processing from the main response stream to improve latency.
Tasks are scheduled to run in the background without blocking the response.

Supported tasks:
- Memory storage with embedding generation
- WebSocket notifications
- Analytics/logging
"""

import asyncio
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from research_agent.shared.utils.logger import logger


class PostProcessTaskType(str, Enum):
    """Types of post-processing tasks."""

    MEMORY_STORAGE = "memory_storage"
    WEBSOCKET_NOTIFY = "websocket_notify"
    ANALYTICS = "analytics"
    CUSTOM = "custom"


class TaskPriority(int, Enum):
    """Task priority levels (lower = higher priority)."""

    HIGH = 1
    NORMAL = 5
    LOW = 10


@dataclass
class PostProcessTask:
    """A post-processing task to be executed."""

    task_type: PostProcessTaskType
    task_id: str
    payload: dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    max_retries: int = 2
    timeout_seconds: float = 30.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "task_type": self.task_type.value,
            "task_id": self.task_id,
            "payload": self.payload,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class TaskResult:
    """Result of a post-processing task execution."""

    task_id: str
    task_type: PostProcessTaskType
    success: bool
    duration_ms: float
    error: str | None = None
    retries_used: int = 0


class TaskHandler(ABC):
    """Abstract base class for task handlers."""

    @abstractmethod
    async def execute(self, payload: dict[str, Any]) -> bool:
        """Execute the task with the given payload.

        Args:
            payload: Task payload data

        Returns:
            True if successful, False otherwise
        """
        pass

    @property
    @abstractmethod
    def task_type(self) -> PostProcessTaskType:
        """Return the task type this handler handles."""
        pass


class AsyncPostProcessor:
    """Async post-processor for fire-and-forget tasks.

    Manages background task execution without blocking the main response.
    """

    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        enable_logging: bool = True,
    ):
        """Initialize the post-processor.

        Args:
            max_concurrent_tasks: Maximum concurrent background tasks
            enable_logging: Whether to log task execution
        """
        self._max_concurrent = max_concurrent_tasks
        self._enable_logging = enable_logging
        self._handlers: dict[PostProcessTaskType, TaskHandler] = {}
        self._custom_handlers: dict[str, Callable[..., Coroutine]] = {}
        self._active_tasks: dict[str, asyncio.Task] = {}
        self._results: list[TaskResult] = []
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)

    def register_handler(self, handler: TaskHandler) -> None:
        """Register a task handler.

        Args:
            handler: The handler to register
        """
        self._handlers[handler.task_type] = handler
        if self._enable_logging:
            logger.debug(f"[AsyncPostProcessor] Registered handler for {handler.task_type.value}")

    def register_custom_handler(
        self,
        name: str,
        handler: Callable[..., Coroutine],
    ) -> None:
        """Register a custom async function as a handler.

        Args:
            name: Name for the custom handler
            handler: Async function to execute
        """
        self._custom_handlers[name] = handler
        if self._enable_logging:
            logger.debug(f"[AsyncPostProcessor] Registered custom handler: {name}")

    def schedule(
        self,
        tasks: list[PostProcessTask],
        context_id: str | None = None,
    ) -> list[str]:
        """Schedule tasks for background execution.

        This method returns immediately without waiting for tasks to complete.

        Args:
            tasks: List of tasks to schedule
            context_id: Optional context identifier for grouping

        Returns:
            List of task IDs that were scheduled
        """
        scheduled_ids = []

        # Sort by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority.value)

        for task in sorted_tasks:
            task_key = f"{context_id}:{task.task_id}" if context_id else task.task_id

            # Create background task
            asyncio_task = asyncio.create_task(
                self._run_task_with_retry(task),
                name=task_key,
            )

            # Track active task
            self._active_tasks[task_key] = asyncio_task

            # Clean up when done
            asyncio_task.add_done_callback(lambda t, key=task_key: self._on_task_complete(key, t))

            scheduled_ids.append(task.task_id)

        if self._enable_logging and scheduled_ids:
            logger.info(
                f"[AsyncPostProcessor] Scheduled {len(scheduled_ids)} tasks (context={context_id})"
            )

        return scheduled_ids

    async def _run_task_with_retry(self, task: PostProcessTask) -> TaskResult:
        """Run a task with retry logic.

        Args:
            task: The task to execute

        Returns:
            TaskResult with execution details
        """
        start_time = datetime.utcnow()
        retries = 0
        last_error: str | None = None

        async with self._semaphore:
            while retries <= task.max_retries:
                try:
                    success = await asyncio.wait_for(
                        self._execute_task(task),
                        timeout=task.timeout_seconds,
                    )

                    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                    result = TaskResult(
                        task_id=task.task_id,
                        task_type=task.task_type,
                        success=success,
                        duration_ms=duration_ms,
                        retries_used=retries,
                    )

                    if self._enable_logging:
                        logger.info(
                            f"[AsyncPostProcessor] Task {task.task_id} completed: "
                            f"success={success}, duration={duration_ms:.1f}ms, "
                            f"retries={retries}"
                        )

                    self._results.append(result)
                    return result

                except TimeoutError:
                    last_error = f"Timeout after {task.timeout_seconds}s"
                    retries += 1
                    if self._enable_logging:
                        logger.warning(
                            f"[AsyncPostProcessor] Task {task.task_id} timeout, "
                            f"retry {retries}/{task.max_retries}"
                        )

                except Exception as e:
                    last_error = f"{type(e).__name__}: {str(e)}"
                    retries += 1
                    if self._enable_logging:
                        logger.warning(
                            f"[AsyncPostProcessor] Task {task.task_id} error: {e}, "
                            f"retry {retries}/{task.max_retries}"
                        )
                        logger.debug(traceback.format_exc())

        # All retries exhausted
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        result = TaskResult(
            task_id=task.task_id,
            task_type=task.task_type,
            success=False,
            duration_ms=duration_ms,
            error=last_error,
            retries_used=retries,
        )

        if self._enable_logging:
            logger.error(
                f"[AsyncPostProcessor] Task {task.task_id} failed after "
                f"{retries} retries: {last_error}"
            )

        self._results.append(result)
        return result

    async def _execute_task(self, task: PostProcessTask) -> bool:
        """Execute a single task.

        Args:
            task: The task to execute

        Returns:
            True if successful
        """
        # Try registered handler first
        handler = self._handlers.get(task.task_type)
        if handler:
            return await handler.execute(task.payload)

        # Try custom handler
        if task.task_type == PostProcessTaskType.CUSTOM:
            handler_name = task.payload.get("handler_name")
            custom_handler = self._custom_handlers.get(handler_name)
            if custom_handler:
                await custom_handler(**task.payload.get("args", {}))
                return True

        logger.warning(f"[AsyncPostProcessor] No handler for task type {task.task_type.value}")
        return False

    def _on_task_complete(self, task_key: str, task: asyncio.Task) -> None:
        """Callback when a task completes.

        Args:
            task_key: The task key
            task: The asyncio task
        """
        # Remove from active tasks
        self._active_tasks.pop(task_key, None)

        # Log any unhandled exceptions
        if task.exception() and self._enable_logging:
            logger.error(
                f"[AsyncPostProcessor] Unhandled exception in task {task_key}: {task.exception()}"
            )

    async def wait_all(self, timeout: float | None = None) -> list[TaskResult]:
        """Wait for all active tasks to complete.

        Args:
            timeout: Maximum time to wait (None for no limit)

        Returns:
            List of task results
        """
        if not self._active_tasks:
            return self._results.copy()

        tasks = list(self._active_tasks.values())

        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout,
            )
        except TimeoutError:
            if self._enable_logging:
                logger.warning(
                    f"[AsyncPostProcessor] wait_all timed out with "
                    f"{len(self._active_tasks)} tasks remaining"
                )

        return self._results.copy()

    def get_active_count(self) -> int:
        """Get the number of active tasks."""
        return len(self._active_tasks)

    def get_results(self) -> list[TaskResult]:
        """Get all task results."""
        return self._results.copy()

    def clear_results(self) -> None:
        """Clear stored results."""
        self._results.clear()


# ============================================================================
# Built-in Task Handlers
# ============================================================================


class MemoryStorageHandler(TaskHandler):
    """Handler for memory storage tasks."""

    def __init__(self, memory_service: Any):
        """Initialize with memory service.

        Args:
            memory_service: The memory service to use
        """
        self._memory_service = memory_service

    @property
    def task_type(self) -> PostProcessTaskType:
        return PostProcessTaskType.MEMORY_STORAGE

    async def execute(self, payload: dict[str, Any]) -> bool:
        """Store a memory entry."""
        try:
            await self._memory_service.store(
                project_id=payload["project_id"],
                question=payload["question"],
                answer=payload["answer"],
                session_id=payload.get("session_id"),
            )
            return True
        except Exception as e:
            logger.error(f"[MemoryStorageHandler] Failed to store memory: {e}")
            return False


class WebSocketNotifyHandler(TaskHandler):
    """Handler for WebSocket notification tasks."""

    def __init__(self, notification_service: Any):
        """Initialize with notification service.

        Args:
            notification_service: The WebSocket notification service
        """
        self._notification_service = notification_service

    @property
    def task_type(self) -> PostProcessTaskType:
        return PostProcessTaskType.WEBSOCKET_NOTIFY

    async def execute(self, payload: dict[str, Any]) -> bool:
        """Send a WebSocket notification."""
        try:
            await self._notification_service.notify(
                project_id=payload["project_id"],
                event_type=payload["event_type"],
                data=payload.get("data", {}),
            )
            return True
        except Exception as e:
            logger.error(f"[WebSocketNotifyHandler] Failed to send notification: {e}")
            return False


# ============================================================================
# Factory and helpers
# ============================================================================


def create_post_processor(
    memory_service: Any = None,
    notification_service: Any = None,
    max_concurrent: int = 10,
) -> AsyncPostProcessor:
    """Create a post-processor with registered handlers.

    Args:
        memory_service: Optional memory service
        notification_service: Optional WebSocket notification service
        max_concurrent: Maximum concurrent tasks

    Returns:
        Configured AsyncPostProcessor
    """
    processor = AsyncPostProcessor(max_concurrent_tasks=max_concurrent)

    if memory_service:
        processor.register_handler(MemoryStorageHandler(memory_service))

    if notification_service:
        processor.register_handler(WebSocketNotifyHandler(notification_service))

    return processor


def create_memory_task(
    project_id: UUID,
    question: str,
    answer: str,
    session_id: UUID | None = None,
    priority: TaskPriority = TaskPriority.NORMAL,
) -> PostProcessTask:
    """Create a memory storage task.

    Args:
        project_id: Project ID
        question: User question
        answer: AI response
        session_id: Optional session ID
        priority: Task priority

    Returns:
        PostProcessTask for memory storage
    """
    return PostProcessTask(
        task_type=PostProcessTaskType.MEMORY_STORAGE,
        task_id=f"memory_{project_id}_{datetime.utcnow().timestamp()}",
        payload={
            "project_id": str(project_id),
            "question": question,
            "answer": answer,
            "session_id": str(session_id) if session_id else None,
        },
        priority=priority,
    )
