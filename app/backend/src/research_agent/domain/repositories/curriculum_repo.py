"""Curriculum repository interface."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from research_agent.domain.entities.curriculum import Curriculum


class CurriculumRepository(ABC):
    """Abstract curriculum repository interface."""

    @abstractmethod
    async def save(self, curriculum: Curriculum) -> Curriculum:
        """Save or update a curriculum."""
        pass

    @abstractmethod
    async def find_by_project(self, project_id: UUID) -> Optional[Curriculum]:
        """Find curriculum by project ID."""
        pass

    @abstractmethod
    async def delete_by_project(self, project_id: UUID) -> bool:
        """Delete curriculum by project ID. Returns True if deleted."""
        pass

