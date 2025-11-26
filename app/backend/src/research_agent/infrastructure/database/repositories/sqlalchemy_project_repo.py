"""SQLAlchemy implementation of ProjectRepository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.project import Project
from research_agent.domain.repositories.project_repo import ProjectRepository
from research_agent.infrastructure.database.models import ProjectModel


class SQLAlchemyProjectRepository(ProjectRepository):
    """SQLAlchemy implementation of project repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, project: Project) -> Project:
        """Save a project."""
        # Check if exists
        existing = await self._session.get(ProjectModel, project.id)

        if existing:
            # Update existing
            existing.name = project.name
            existing.description = project.description
            existing.updated_at = project.updated_at
        else:
            # Create new
            model = self._to_model(project)
            self._session.add(model)

        await self._session.flush()
        return project

    async def find_by_id(self, project_id: UUID) -> Optional[Project]:
        """Find project by ID."""
        model = await self._session.get(ProjectModel, project_id)
        return self._to_entity(model) if model else None

    async def find_all(self) -> List[Project]:
        """Find all projects."""
        result = await self._session.execute(
            select(ProjectModel).order_by(ProjectModel.updated_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def delete(self, project_id: UUID) -> bool:
        """Delete a project."""
        model = await self._session.get(ProjectModel, project_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    def _to_model(self, entity: Project) -> ProjectModel:
        """Convert entity to ORM model."""
        return ProjectModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, model: ProjectModel) -> Project:
        """Convert ORM model to entity."""
        return Project(
            id=model.id,
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

