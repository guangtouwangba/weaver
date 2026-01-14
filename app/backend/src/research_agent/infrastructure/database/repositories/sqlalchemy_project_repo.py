"""SQLAlchemy implementation of ProjectRepository."""

from uuid import UUID

from sqlalchemy import select, update
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
            existing.user_id = project.user_id
            existing.updated_at = project.updated_at
        else:
            # Create new
            model = self._to_model(project)
            self._session.add(model)

        await self._session.flush()
        return project

    async def find_by_id(
        self, project_id: UUID, user_id: str | None = None
    ) -> Project | None:
        """Find project by ID, optionally filtered by user.

        Args:
            project_id: The project UUID to find
            user_id: If provided, verifies the project belongs to this user

        Returns:
            Project if found (and owned by user if user_id provided), else None
        """
        model = await self._session.get(ProjectModel, project_id)
        if not model:
            return None

        # If user_id provided, verify ownership
        if user_id is not None and model.user_id != user_id:
            return None

        return self._to_entity(model)

    async def find_all(self, user_id: str | None = None) -> list[Project]:
        """Find all projects, optionally filtered by user.

        Args:
            user_id: If provided, only returns projects owned by this user

        Returns:
            List of projects
        """
        query = select(ProjectModel).order_by(ProjectModel.updated_at.desc())

        if user_id is not None:
            query = query.where(ProjectModel.user_id == user_id)

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def delete(self, project_id: UUID, user_id: str | None = None) -> bool:
        """Delete a project.

        Args:
            project_id: The project UUID to delete
            user_id: If provided, verifies the project belongs to this user

        Returns:
            True if deleted, False if not found or not owned by user
        """
        model = await self._session.get(ProjectModel, project_id)
        if not model:
            return False

        # If user_id provided, verify ownership
        if user_id is not None and model.user_id != user_id:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True

    def _to_model(self, entity: Project) -> ProjectModel:
        """Convert entity to ORM model."""
        return ProjectModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            user_id=entity.user_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def migrate_user_data(self, from_user_id: str, to_user_id: str) -> int:
        """Migrate projects from one user to another.

        Args:
            from_user_id: The user ID to migrate data from
            to_user_id: The user ID to migrate data to

        Returns:
            Number of projects migrated
        """
        stmt = (
            update(ProjectModel)
            .where(ProjectModel.user_id == from_user_id)
            .values(user_id=to_user_id)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount

    def _to_entity(self, model: ProjectModel) -> Project:
        """Convert ORM model to entity."""
        return Project(
            id=model.id,
            name=model.name,
            description=model.description,
            user_id=model.user_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
