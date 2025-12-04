"""Task dispatcher for routing tasks to handlers."""

from typing import Any, Dict, Type

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.task import Task, TaskType
from research_agent.shared.utils.logger import logger
from research_agent.worker.tasks.base import BaseTask


class TaskDispatcher:
    """Dispatcher that routes tasks to appropriate handlers."""

    def __init__(self):
        self._handlers: Dict[str, Type[BaseTask]] = {}

    def register(self, task_type: TaskType, handler_class: Type[BaseTask]) -> None:
        """
        Register a handler for a task type.

        Args:
            task_type: The type of task to handle
            handler_class: The class that handles this task type
        """
        self._handlers[task_type.value] = handler_class
        logger.info(f"Registered handler {handler_class.__name__} for task type {task_type.value}")

    async def dispatch(self, task: Task, session: AsyncSession) -> None:
        """
        Dispatch a task to its handler.

        Args:
            task: The task to dispatch
            session: Database session for the task

        Raises:
            ValueError: If no handler is registered for the task type
            Exception: If task execution fails
        """
        handler_class = self._handlers.get(task.task_type.value)

        if not handler_class:
            error_msg = f"No handler registered for task type: {task.task_type.value}"
            logger.error(
                f"❌ Dispatch error - task_id={task.id}, task_type={task.task_type.value}, "
                f"registered_types={list(self._handlers.keys())}"
            )
            raise ValueError(error_msg)

        handler = handler_class()
        logger.info(
            f"📤 Dispatching task - task_id={task.id}, task_type={task.task_type.value}, "
            f"handler={handler_class.__name__}, payload_keys={list(task.payload.keys())}"
        )

        try:
            await handler.execute(task.payload, session)
            logger.debug(f"✅ Task dispatched successfully - task_id={task.id}")
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            logger.error(
                f"❌ Task dispatch execution failed - task_id={task.id}, "
                f"task_type={task.task_type.value}, handler={handler_class.__name__}, "
                f"error_type={error_type}, error={error_message}, payload={task.payload}",
                exc_info=True,
            )
            raise

    def get_registered_types(self) -> list[str]:
        """Get list of registered task types."""
        return list(self._handlers.keys())
