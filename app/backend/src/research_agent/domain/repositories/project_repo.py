"""Project repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from research_agent.domain.entities.project import Project


class ProjectRepository(ABC):
    """Abstract project repository interface."""

    @abstractmethod
    async def save(self, project: Project) -> Project:
        """Save a project."""
        pass

    @abstractmethod
    async def find_by_id(self, project_id: UUID) -> Optional[Project]:
        """Find project by ID."""
        pass

    @abstractmethod
    async def find_all(self) -> List[Project]:
        """Find all projects."""
        pass

    @abstractmethod
    async def delete(self, project_id: UUID) -> bool:
        """Delete a project."""
        pass

