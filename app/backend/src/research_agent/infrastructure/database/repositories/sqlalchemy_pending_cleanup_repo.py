"""SQLAlchemy implementation of PendingCleanupRepository."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.repositories.pending_cleanup_repo import (
    PendingCleanup,
    PendingCleanupRepository,
)
from research_agent.infrastructure.database.models import PendingCleanupModel


class SQLAlchemyPendingCleanupRepository(PendingCleanupRepository):
    """SQLAlchemy implementation of pending cleanup repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(
        self,
        file_path: str,
        storage_type: str = "both",
        document_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
    ) -> PendingCleanup:
        """Add a new pending cleanup record."""
        model = PendingCleanupModel(
            id=uuid4(),
            file_path=file_path,
            storage_type=storage_type,
            attempts=0,
            max_attempts=5,
            document_id=document_id,
            project_id=project_id,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def find_by_id(self, cleanup_id: UUID) -> Optional[PendingCleanup]:
        """Find pending cleanup by ID."""
        model = await self._session.get(PendingCleanupModel, cleanup_id)
        return self._to_entity(model) if model else None

    async def find_pending(self, limit: int = 100) -> List[PendingCleanup]:
        """Find pending cleanups that haven't exceeded max attempts."""
        result = await self._session.execute(
            select(PendingCleanupModel)
            .where(PendingCleanupModel.attempts < PendingCleanupModel.max_attempts)
            .order_by(PendingCleanupModel.created_at.asc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def increment_attempt(
        self, cleanup_id: UUID, error: Optional[str] = None
    ) -> bool:
        """Increment attempt count and record error if any."""
        result = await self._session.execute(
            update(PendingCleanupModel)
            .where(PendingCleanupModel.id == cleanup_id)
            .values(
                attempts=PendingCleanupModel.attempts + 1,
                last_error=error,
                last_attempt_at=datetime.utcnow(),
            )
        )
        await self._session.flush()
        return result.rowcount > 0

    async def remove(self, cleanup_id: UUID) -> bool:
        """Remove a cleanup record after successful deletion."""
        result = await self._session.execute(
            delete(PendingCleanupModel).where(PendingCleanupModel.id == cleanup_id)
        )
        await self._session.flush()
        return result.rowcount > 0

    async def remove_by_file_path(self, file_path: str) -> bool:
        """Remove all cleanup records for a file path."""
        result = await self._session.execute(
            delete(PendingCleanupModel).where(
                PendingCleanupModel.file_path == file_path
            )
        )
        await self._session.flush()
        return result.rowcount > 0

    def _to_entity(self, model: PendingCleanupModel) -> PendingCleanup:
        """Convert ORM model to entity."""
        return PendingCleanup(
            id=model.id,
            file_path=model.file_path,
            storage_type=model.storage_type,
            attempts=model.attempts,
            max_attempts=model.max_attempts,
            last_error=model.last_error,
            created_at=model.created_at,
            last_attempt_at=model.last_attempt_at,
            document_id=model.document_id,
            project_id=model.project_id,
        )
