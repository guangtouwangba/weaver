"""Create project use case."""

from dataclasses import dataclass
from uuid import UUID

from research_agent.domain.entities.project import Project
from research_agent.domain.repositories.project_repo import ProjectRepository


@dataclass
class CreateProjectInput:
    """Input for create project use case."""

    name: str
    description: str | None = None


@dataclass
class CreateProjectOutput:
    """Output for create project use case."""

    id: UUID
    name: str
    description: str | None


class CreateProjectUseCase:
    """Use case for creating a new project."""

    def __init__(self, project_repo: ProjectRepository):
        self._project_repo = project_repo

    async def execute(self, input: CreateProjectInput) -> CreateProjectOutput:
        """Execute the use case."""
        # Create project entity
        project = Project(
            name=input.name,
            description=input.description,
        )

        # Save to repository
        saved_project = await self._project_repo.save(project)

        return CreateProjectOutput(
            id=saved_project.id,
            name=saved_project.name,
            description=saved_project.description,
        )

