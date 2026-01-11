"""SQLAlchemy repository for Output entity."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.output import Output, OutputStatus, OutputType
from research_agent.infrastructure.database.models import OutputModel


class SQLAlchemyOutputRepository:
    """SQLAlchemy implementation of Output repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, output: Output) -> Output:
        """Create a new output."""
        model = OutputModel(
            id=output.id,
            project_id=output.project_id,
            output_type=output.output_type.value,
            source_ids=output.source_ids,
            status=output.status.value,
            title=output.title,
            data=output.data,
            error_message=output.error_message,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def find_by_id(self, output_id: UUID) -> Optional[Output]:
        """Find output by ID."""
        result = await self._session.execute(select(OutputModel).where(OutputModel.id == output_id))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_project(
        self,
        project_id: UUID,
        output_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Output], int]:
        """
        Find outputs by project ID with optional filtering.

        Returns:
            Tuple of (outputs list, total count)
        """
        # Base query
        query = select(OutputModel).where(OutputModel.project_id == project_id)

        # Apply type filter if specified
        if output_type:
            query = query.where(OutputModel.output_type == output_type)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self._session.execute(count_query)).scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(OutputModel.created_at.desc()).offset(offset).limit(limit)

        result = await self._session.execute(query)
        models = result.scalars().all()

        return [self._to_entity(m) for m in models], total

    async def update(self, output: Output) -> Output:
        """Update an existing output."""
        result = await self._session.execute(select(OutputModel).where(OutputModel.id == output.id))
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Output not found: {output.id}")

        model.status = output.status.value
        model.title = output.title
        model.data = output.data
        model.error_message = output.error_message

        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, output_id: UUID) -> bool:
        """Delete an output by ID."""
        result = await self._session.execute(select(OutputModel).where(OutputModel.id == output_id))
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self._session.delete(model)
        await self._session.commit()
        return True

    def _to_entity(self, model: OutputModel) -> Output:
        """Convert ORM model to domain entity."""
        return Output(
            id=model.id,
            project_id=model.project_id,
            output_type=OutputType(model.output_type),
            source_ids=list(model.source_ids) if model.source_ids else [],
            status=OutputStatus(model.status),
            title=model.title,
            data=model.data,
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
