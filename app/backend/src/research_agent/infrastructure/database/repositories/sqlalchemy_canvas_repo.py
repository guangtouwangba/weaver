"""SQLAlchemy implementation of CanvasRepository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.canvas import Canvas
from research_agent.domain.repositories.canvas_repo import CanvasRepository
from research_agent.infrastructure.database.models import CanvasModel


class SQLAlchemyCanvasRepository(CanvasRepository):
    """SQLAlchemy implementation of canvas repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, canvas: Canvas) -> Canvas:
        """Save canvas data."""
        # Check if exists for this project
        result = await self._session.execute(
            select(CanvasModel).where(CanvasModel.project_id == canvas.project_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.data = canvas.to_dict()
        else:
            # Create new
            model = CanvasModel(
                id=canvas.id,
                project_id=canvas.project_id,
                data=canvas.to_dict(),
            )
            self._session.add(model)

        await self._session.flush()
        return canvas

    async def find_by_project(self, project_id: UUID) -> Optional[Canvas]:
        """Find canvas by project ID."""
        result = await self._session.execute(
            select(CanvasModel).where(CanvasModel.project_id == project_id)
        )
        model = result.scalar_one_or_none()

        if model:
            canvas = Canvas.from_dict(model.data, project_id)
            canvas.id = model.id
            canvas.updated_at = model.updated_at
            return canvas

        return None

    async def delete_by_project(self, project_id: UUID) -> bool:
        """Delete canvas for a project."""
        result = await self._session.execute(
            select(CanvasModel).where(CanvasModel.project_id == project_id)
        )
        model = result.scalar_one_or_none()

        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True

        return False

