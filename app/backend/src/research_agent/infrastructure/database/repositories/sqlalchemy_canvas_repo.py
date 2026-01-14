"""SQLAlchemy implementation of CanvasRepository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.canvas import Canvas
from research_agent.domain.repositories.canvas_repo import CanvasRepository
from research_agent.infrastructure.database.models import CanvasModel
from research_agent.shared.exceptions import ConflictError
from research_agent.shared.utils.logger import logger


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
            canvas_data = canvas.to_dict()
            # Debug: log fileMetadata for first node
            if canvas_data.get("nodes"):
                first_node = canvas_data["nodes"][0]
                logger.info(
                    f"[Canvas Save] First node fileMetadata: {first_node.get('fileMetadata')}"
                )
            existing.data = canvas_data
            existing.version = existing.version + 1
            if canvas.user_id:
                existing.user_id = canvas.user_id
            canvas.version = existing.version
        else:
            # Create new
            canvas_data = canvas.to_dict()
            # Debug: log fileMetadata for first node
            if canvas_data.get("nodes"):
                first_node = canvas_data["nodes"][0]
                logger.info(
                    f"[Canvas Save] First node fileMetadata: {first_node.get('fileMetadata')}"
                )
            model = CanvasModel(
                id=canvas.id,
                project_id=canvas.project_id,
                user_id=canvas.user_id,
                data=canvas_data,
                version=1,
            )
            self._session.add(model)
            canvas.version = 1

        await self._session.flush()
        return canvas

    async def save_with_version(
        self, canvas: Canvas, expected_version: Optional[int] = None
    ) -> Canvas:
        """Save canvas data with version check (optimistic locking)."""
        # Use SELECT FOR UPDATE NOWAIT to lock the row without waiting
        # NOWAIT will raise an error immediately if the row is already locked,
        # instead of waiting indefinitely (which could cause 30+ second delays)
        stmt = (
            select(CanvasModel)
            .where(CanvasModel.project_id == canvas.project_id)
            .with_for_update(nowait=True)
        )
        try:
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()
        except (OperationalError, DBAPIError) as e:
            # PostgreSQL error code 55P03: lock_not_available
            # asyncpg raises LockNotAvailableError which SQLAlchemy wraps as DBAPIError
            error_str = str(e)
            if (
                "could not obtain lock" in error_str
                or "55P03" in error_str
                or "LockNotAvailableError" in error_str
            ):
                logger.warning(
                    f"[Canvas] Lock conflict for project {canvas.project_id}, "
                    "another transaction is modifying this canvas"
                )
                raise ConflictError(
                    "Canvas",
                    str(canvas.project_id),
                    "Canvas is being modified by another request, please retry",
                )
            raise

        if existing:
            # Check version if provided
            if expected_version is not None and existing.version != expected_version:
                raise ConflictError(
                    "Canvas",
                    str(canvas.project_id),
                    f"Version mismatch: expected {expected_version}, got {existing.version}",
                )
            # Update existing
            existing.data = canvas.to_dict()
            existing.version = existing.version + 1
            if canvas.user_id:
                existing.user_id = canvas.user_id
            canvas.version = existing.version
        else:
            # Create new
            if expected_version is not None and expected_version != 0:
                raise ConflictError(
                    "Canvas",
                    str(canvas.project_id),
                    f"Canvas does not exist but expected version {expected_version}",
                )
            model = CanvasModel(
                id=canvas.id,
                project_id=canvas.project_id,
                user_id=canvas.user_id,
                data=canvas.to_dict(),
                version=1,
            )
            self._session.add(model)
            canvas.version = 1

        await self._session.flush()
        return canvas

    async def find_by_project(
        self, project_id: UUID, user_id: Optional[str] = None
    ) -> Optional[Canvas]:
        """Find canvas by project ID."""
        query = select(CanvasModel).where(CanvasModel.project_id == project_id)
        if user_id:
            query = query.where(CanvasModel.user_id == user_id)

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()

        if model:
            # Debug: log raw data from database
            if model.data.get("nodes"):
                first_node = model.data["nodes"][0]
                logger.info(
                    f"[Canvas Load] Raw DB first node fileMetadata: {first_node.get('fileMetadata')}"
                )
            canvas = Canvas.from_dict(model.data, project_id)
            # Debug: log after parsing
            if canvas.nodes:
                logger.info(
                    f"[Canvas Load] Parsed first node file_metadata: {canvas.nodes[0].file_metadata}"
                )
            canvas.id = model.id
            canvas.user_id = model.user_id
            canvas.version = model.version
            canvas.updated_at = model.updated_at
            return canvas

        return None

    async def delete_by_project(self, project_id: UUID, user_id: Optional[str] = None) -> bool:
        """Delete canvas for a project."""
        query = select(CanvasModel).where(CanvasModel.project_id == project_id)
        if user_id:
            query = query.where(CanvasModel.user_id == user_id)

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()

        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False
