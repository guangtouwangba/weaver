"""Canvas repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from research_agent.domain.entities.canvas import Canvas


class CanvasRepository(ABC):
    """Abstract canvas repository interface."""

    @abstractmethod
    async def save(self, canvas: Canvas) -> Canvas:
        """Save canvas data."""
        pass

    @abstractmethod
    async def save_with_version(
        self, canvas: Canvas, expected_version: int | None = None
    ) -> Canvas:
        """Save canvas data with version check (optimistic locking)."""
        pass

    @abstractmethod
    async def find_by_project(self, project_id: UUID) -> Canvas | None:
        """Find canvas by project ID."""
        pass

    @abstractmethod
    async def delete_by_project(self, project_id: UUID) -> bool:
        """Delete canvas for a project."""
        pass

