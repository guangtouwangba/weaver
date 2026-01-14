"""Project repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from research_agent.domain.entities.project import Project


class ProjectRepository(ABC):
    """Abstract project repository interface."""

    @abstractmethod
    async def save(self, project: Project) -> Project:
        """Save a project."""
        pass

    @abstractmethod
    async def find_by_id(self, project_id: UUID) -> Project | None:
        """Find project by ID."""
        pass

    @abstractmethod
    async def find_all(self) -> list[Project]:
        """Find all projects."""
        pass

    @abstractmethod
    async def delete(self, project_id: UUID, user_id: str | None = None) -> bool:
        """Delete a project."""
        pass

    @abstractmethod
    async def migrate_user_data(self, from_user_id: str, to_user_id: str) -> int:
        """Migrate projects from one user to another."""
        pass
