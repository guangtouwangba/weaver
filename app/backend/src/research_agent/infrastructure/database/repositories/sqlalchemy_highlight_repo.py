"""SQLAlchemy implementation of HighlightRepository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.database.models import HighlightModel


class SQLAlchemyHighlightRepository:
    """SQLAlchemy implementation of highlight repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        document_id: UUID,
        page_number: int,
        start_offset: int,
        end_offset: int,
        color: str,
        note: str | None = None,
        rects: dict | None = None,
        user_id: str | None = None,
    ) -> HighlightModel:
        """Create a new highlight."""
        highlight = HighlightModel(
            document_id=document_id,
            page_number=page_number,
            start_offset=start_offset,
            end_offset=end_offset,
            color=color,
            note=note,
            rects=rects,
            user_id=user_id,
        )
        self._session.add(highlight)
        await self._session.flush()
        await self._session.refresh(highlight)
        return highlight

    async def find_by_id(self, highlight_id: UUID) -> HighlightModel | None:
        """Find highlight by ID."""
        return await self._session.get(HighlightModel, highlight_id)

    async def find_by_document(
        self, document_id: UUID, user_id: str | None = None
    ) -> list[HighlightModel]:
        """Find all highlights for a document."""
        query = select(HighlightModel).where(HighlightModel.document_id == document_id)
        if user_id:
            query = query.where(HighlightModel.user_id == user_id)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        highlight_id: UUID,
        color: str | None = None,
        note: str | None = None,
    ) -> HighlightModel | None:
        """Update a highlight."""
        highlight = await self.find_by_id(highlight_id)
        if not highlight:
            return None

        if color is not None:
            highlight.color = color
        if note is not None:
            highlight.note = note

        await self._session.flush()
        await self._session.refresh(highlight)
        return highlight

    async def delete(self, highlight_id: UUID) -> bool:
        """Delete a highlight."""
        highlight = await self.find_by_id(highlight_id)
        if not highlight:
            return False

        await self._session.delete(highlight)
        await self._session.flush()
        return True
