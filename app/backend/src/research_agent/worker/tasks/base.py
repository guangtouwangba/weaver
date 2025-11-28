"""Base task interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession


class BaseTask(ABC):
    """Abstract base class for all background tasks."""

    @property
    @abstractmethod
    def task_type(self) -> str:
        """Return the task type identifier."""
        pass

    @abstractmethod
    async def execute(self, payload: Dict[str, Any], session: AsyncSession) -> None:
        """
        Execute the task.
        
        Args:
            payload: Task-specific data
            session: Database session for the task
            
        Raises:
            Exception: If task execution fails
        """
        pass

