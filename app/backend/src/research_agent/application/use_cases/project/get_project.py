"""Get project use case."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from research_agent.domain.repositories.project_repo import ProjectRepository
from research_agent.shared.exceptions import NotFoundError


@dataclass
class GetProjectInput:
    """Input for get project use case."""

    project_id: UUID


@dataclass
class GetProjectOutput:
    """Output for get project use case."""

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class GetProjectUseCase:
    """Use case for getting a project by ID."""

    def __init__(self, project_repo: ProjectRepository):
        self._project_repo = project_repo

    async def execute(self, input: GetProjectInput) -> GetProjectOutput:
        """Execute the use case."""
        project = await self._project_repo.find_by_id(input.project_id)

        if not project:
            raise NotFoundError("Project", str(input.project_id))

        return GetProjectOutput(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

