"""List projects use case."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from research_agent.domain.repositories.project_repo import ProjectRepository


@dataclass
class ProjectItem:
    """Project item in list."""

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class ListProjectsOutput:
    """Output for list projects use case."""

    items: list[ProjectItem]
    total: int


class ListProjectsUseCase:
    """Use case for listing all projects."""

    def __init__(self, project_repo: ProjectRepository):
        self._project_repo = project_repo

    async def execute(self) -> ListProjectsOutput:
        """Execute the use case."""
        projects = await self._project_repo.find_all()

        items = [
            ProjectItem(
                id=p.id,
                name=p.name,
                description=p.description,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in projects
        ]

        return ListProjectsOutput(
            items=items,
            total=len(items),
        )

