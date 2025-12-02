"""SQLAlchemy implementation of CurriculumRepository."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.curriculum import Curriculum, CurriculumStep
from research_agent.domain.repositories.curriculum_repo import CurriculumRepository
from research_agent.infrastructure.database.models import CurriculumModel


class SQLAlchemyCurriculumRepository(CurriculumRepository):
    """SQLAlchemy implementation of curriculum repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, curriculum: Curriculum) -> Curriculum:
        """Save or update a curriculum."""
        # Check if curriculum exists
        result = await self._session.execute(
            select(CurriculumModel).where(CurriculumModel.project_id == curriculum.project_id)
        )
        existing = result.scalar_one_or_none()

        # Convert steps to dict format for JSONB
        steps_data = [
            {
                "id": step.id,
                "title": step.title,
                "source": step.source,
                "sourceType": step.source_type,
                "pageRange": step.page_range,
                "duration": step.duration,
            }
            for step in curriculum.steps
        ]

        if existing:
            # Update existing
            existing.steps = steps_data
            existing.total_duration = curriculum.total_duration
            existing.updated_at = datetime.now()
            await self._session.flush()
            return self._to_entity(existing)
        else:
            # Create new
            model = CurriculumModel(
                id=curriculum.id if curriculum.id else uuid4(),
                project_id=curriculum.project_id,
                steps=steps_data,
                total_duration=curriculum.total_duration,
            )
            self._session.add(model)
            await self._session.flush()
            return self._to_entity(model)

    async def find_by_project(self, project_id: UUID) -> Optional[Curriculum]:
        """Find curriculum by project ID."""
        result = await self._session.execute(
            select(CurriculumModel).where(CurriculumModel.project_id == project_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def delete_by_project(self, project_id: UUID) -> bool:
        """Delete curriculum by project ID."""
        result = await self._session.execute(
            delete(CurriculumModel).where(CurriculumModel.project_id == project_id)
        )
        await self._session.flush()
        return result.rowcount > 0

    def _to_entity(self, model: CurriculumModel) -> Curriculum:
        """Convert ORM model to domain entity."""
        steps = [
            CurriculumStep(
                id=step_data["id"],
                title=step_data["title"],
                source=step_data["source"],
                source_type=step_data["sourceType"],
                page_range=step_data.get("pageRange"),
                duration=step_data["duration"],
            )
            for step_data in model.steps
        ]

        return Curriculum(
            id=model.id,
            project_id=model.project_id,
            steps=steps,
            total_duration=model.total_duration,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

