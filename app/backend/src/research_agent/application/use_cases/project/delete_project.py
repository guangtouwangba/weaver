"""Delete project use case."""

from dataclasses import dataclass
from uuid import UUID

from research_agent.domain.repositories.project_repo import ProjectRepository
from research_agent.shared.exceptions import NotFoundError


@dataclass
class DeleteProjectInput:
    """Input for delete project use case."""

    project_id: UUID


@dataclass
class DeleteProjectOutput:
    """Output for delete project use case."""

    success: bool


class DeleteProjectUseCase:
    """Use case for deleting a project."""

    def __init__(self, project_repo: ProjectRepository):
        self._project_repo = project_repo

    async def execute(self, input: DeleteProjectInput) -> DeleteProjectOutput:
        """Execute the use case."""
        # Check if project exists
        project = await self._project_repo.find_by_id(input.project_id)
        if not project:
            raise NotFoundError("Project", str(input.project_id))

        # Delete project (cascade will handle related data)
        deleted = await self._project_repo.delete(input.project_id)

        return DeleteProjectOutput(success=deleted)

