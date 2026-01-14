"""Task queue service for managing background jobs."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.domain.entities.task import Task, TaskStatus, TaskType
from research_agent.infrastructure.database.models import TaskQueueModel
from research_agent.shared.utils.logger import logger

settings = get_settings()

# Timeout for processing tasks (if a task is processing for longer than this, it's considered stuck)
# Set to 2 minutes to handle development server reloads quickly
TASK_PROCESSING_TIMEOUT_MINUTES = 2


class TaskQueueService:
    """Service for managing the task queue."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def push(
        self,
        task_type: TaskType,
        payload: dict[str, Any],
        priority: int = 0,
        max_attempts: int = 3,
        environment: str | None = None,
    ) -> Task:
        """
        Push a new task to the queue.

        Args:
            task_type: Type of task to execute
            payload: Task-specific data
            priority: Higher priority tasks are processed first
            max_attempts: Maximum number of retry attempts
            environment: Environment name (defaults to current environment from settings)

        Returns:
            Created task entity
        """
        # ✅ Use current environment if not specified
        task_environment = environment or settings.environment

        task = Task(
            task_type=task_type,
            payload=payload,
            priority=priority,
            max_attempts=max_attempts,
        )

        model = TaskQueueModel(
            id=task.id,
            task_type=task.task_type.value,
            payload=task.payload,
            status=task.status.value,
            priority=task.priority,
            attempts=task.attempts,
            max_attempts=task.max_attempts,
            environment=task_environment,  # ✅ Set environment for isolation
            scheduled_at=task.scheduled_at,
        )

        self._session.add(model)
        await self._session.flush()

        logger.info(
            f"Pushed task {task.id} of type {task_type.value} to environment '{task_environment}'"
        )
        return task

    async def pop(self, environment: str | None = None) -> Task | None:
        """
        Pop the next pending task from the queue.

        Uses SELECT FOR UPDATE SKIP LOCKED to ensure atomic task acquisition
        in a multi-worker environment.

        Args:
            environment: Environment name to filter tasks (defaults to current environment)
                        Only tasks from the same environment will be processed.

        Returns:
            Next pending task or None if queue is empty
        """
        # ✅ Only get tasks from current environment
        task_environment = environment or settings.environment

        # Find the next pending task with highest priority from current environment
        stmt = (
            select(TaskQueueModel)
            .where(TaskQueueModel.status == TaskStatus.PENDING.value)
            .where(TaskQueueModel.environment == task_environment)  # ✅ Environment isolation
            .where(TaskQueueModel.scheduled_at <= datetime.utcnow())
            .order_by(TaskQueueModel.priority.desc(), TaskQueueModel.scheduled_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        # Mark as processing
        model.status = TaskStatus.PROCESSING.value
        model.started_at = datetime.utcnow()
        model.attempts += 1
        model.updated_at = datetime.utcnow()

        await self._session.flush()

        logger.debug(f"Popped task {model.id} from environment '{task_environment}'")

        return self._to_entity(model)

    async def complete(self, task_id: UUID) -> None:
        """Mark a task as completed."""
        stmt = (
            update(TaskQueueModel)
            .where(TaskQueueModel.id == task_id)
            .values(
                status=TaskStatus.COMPLETED.value,
                completed_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        await self._session.execute(stmt)
        logger.info(f"Task {task_id} completed")

    async def fail(self, task_id: UUID, error_message: str) -> None:
        """
        Mark a task as failed.

        If attempts < max_attempts, the task will be reset to pending for retry.
        """
        # First get the current task state
        stmt = select(TaskQueueModel).where(TaskQueueModel.id == task_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            logger.warning(f"Task {task_id} not found for failure marking")
            return

        if model.attempts >= model.max_attempts:
            new_status = TaskStatus.FAILED.value
            logger.error(
                f"Task {task_id} failed permanently after {model.attempts} attempts: {error_message}"
            )
        else:
            new_status = TaskStatus.PENDING.value
            logger.warning(
                f"Task {task_id} failed (attempt {model.attempts}/{model.max_attempts}), will retry: {error_message}"
            )

        model.status = new_status
        model.error_message = error_message
        model.updated_at = datetime.utcnow()

        await self._session.flush()

    async def get_by_id(self, task_id: UUID) -> Task | None:
        """Get a task by ID."""
        stmt = select(TaskQueueModel).where(TaskQueueModel.id == task_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_pending_count(self, environment: str | None = None) -> int:
        """Get the number of pending tasks in the current environment."""
        from sqlalchemy import func

        task_environment = environment or settings.environment

        stmt = (
            select(func.count())
            .select_from(TaskQueueModel)
            .where(TaskQueueModel.status == TaskStatus.PENDING.value)
            .where(TaskQueueModel.environment == task_environment)  # ✅ Environment isolation
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_tasks_by_status(
        self,
        status: TaskStatus,
        limit: int = 100,
        environment: str | None = None,
    ) -> list[Task]:
        """Get tasks by status in the current environment."""
        task_environment = environment or settings.environment

        stmt = (
            select(TaskQueueModel)
            .where(TaskQueueModel.status == status.value)
            .where(TaskQueueModel.environment == task_environment)  # ✅ Environment isolation
            .order_by(TaskQueueModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(m) for m in models]

    async def recover_stuck_tasks(self, environment: str | None = None) -> int:
        """
        Recover tasks that were stuck in 'processing' state.

        This happens when the worker is interrupted (e.g., server restart/reload).
        Tasks that have been processing for longer than TASK_PROCESSING_TIMEOUT_MINUTES
        are reset to 'pending' to be retried.

        Args:
            environment: Environment name to filter tasks (defaults to current environment)

        Returns:
            Number of tasks recovered
        """
        task_environment = environment or settings.environment
        timeout_threshold = datetime.utcnow() - timedelta(minutes=TASK_PROCESSING_TIMEOUT_MINUTES)

        # Find stuck tasks: processing status AND started more than timeout ago
        stmt = (
            select(TaskQueueModel)
            .where(TaskQueueModel.status == TaskStatus.PROCESSING.value)
            .where(TaskQueueModel.environment == task_environment)
            .where(TaskQueueModel.started_at < timeout_threshold)
        )

        result = await self._session.execute(stmt)
        stuck_tasks = result.scalars().all()

        recovered_count = 0
        for task in stuck_tasks:
            if task.attempts >= task.max_attempts:
                # Mark as failed if max attempts reached
                task.status = TaskStatus.FAILED.value
                task.error_message = (
                    "Task stuck in processing state (worker interrupted), max attempts reached"
                )
                logger.warning(f"⚠️  Task {task.id} marked as FAILED (stuck, max attempts reached)")
            else:
                # Reset to pending for retry
                task.status = TaskStatus.PENDING.value
                task.error_message = (
                    "Task stuck in processing state (worker interrupted), will retry"
                )
                logger.info(
                    f"🔄 Recovered stuck task {task.id} (type={task.task_type}, "
                    f"attempts={task.attempts}/{task.max_attempts})"
                )
            task.updated_at = datetime.utcnow()
            recovered_count += 1

        if recovered_count > 0:
            await self._session.flush()
            logger.info(
                f"✅ Recovered {recovered_count} stuck tasks in environment '{task_environment}'"
            )

        return recovered_count

    def _to_entity(self, model: TaskQueueModel) -> Task:
        """Convert ORM model to domain entity."""
        return Task(
            id=model.id,
            task_type=TaskType(model.task_type),
            payload=model.payload,
            status=TaskStatus(model.status),
            priority=model.priority,
            attempts=model.attempts,
            max_attempts=model.max_attempts,
            error_message=model.error_message,
            scheduled_at=model.scheduled_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
