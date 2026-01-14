"""SQLAlchemy implementation of URL Content repository."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.database.models import UrlContentModel


class SQLAlchemyUrlContentRepository:
    """Repository for URL content persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, item: UrlContentModel) -> UrlContentModel:
        """Create a new URL content record."""
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def get_by_id(self, item_id: UUID) -> UrlContentModel | None:
        """Get URL content by ID."""
        stmt = select(UrlContentModel).where(UrlContentModel.id == item_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_url(self, url: str) -> UrlContentModel | None:
        """Get URL content by original URL (for deduplication)."""
        stmt = select(UrlContentModel).where(UrlContentModel.url == url)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_normalized_url(self, normalized_url: str) -> UrlContentModel | None:
        """Get URL content by normalized URL (for deduplication with variants)."""
        stmt = select(UrlContentModel).where(
            UrlContentModel.normalized_url == normalized_url
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_items(
        self,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
        platform: str | None = None,
        user_id: str | None = None,
        project_id: UUID | None = None,
    ) -> Sequence[UrlContentModel]:
        """List URL content with optional filters."""
        stmt = select(UrlContentModel)

        if status:
            stmt = stmt.where(UrlContentModel.status == status)

        if platform:
            stmt = stmt.where(UrlContentModel.platform == platform)

        if user_id:
            stmt = stmt.where(UrlContentModel.user_id == user_id)

        if project_id:
            stmt = stmt.where(UrlContentModel.project_id == project_id)

        # Order by creation time, newest first
        stmt = stmt.order_by(desc(UrlContentModel.created_at))
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_by_project(
        self,
        project_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[UrlContentModel]:
        """List URL contents for a specific project."""
        stmt = (
            select(UrlContentModel)
            .where(UrlContentModel.project_id == project_id)
            .order_by(desc(UrlContentModel.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, item: UrlContentModel) -> UrlContentModel:
        """Update an existing URL content record."""
        item.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def update_status(
        self,
        item_id: UUID,
        status: str,
        error_message: str | None = None,
        extracted_at: datetime | None = None,
    ) -> UrlContentModel | None:
        """Update the status of a URL content record."""
        item = await self.get_by_id(item_id)
        if item:
            item.status = status
            item.error_message = error_message
            if extracted_at:
                item.extracted_at = extracted_at
            return await self.update(item)
        return None

    async def update_content(
        self,
        item_id: UUID,
        title: str | None = None,
        content: str | None = None,
        thumbnail_url: str | None = None,
        meta_data: dict | None = None,
    ) -> UrlContentModel | None:
        """Update the extracted content of a URL content record."""
        item = await self.get_by_id(item_id)
        if item:
            if title is not None:
                item.title = title
            if content is not None:
                item.content = content
            if thumbnail_url is not None:
                item.thumbnail_url = thumbnail_url
            if meta_data is not None:
                item.meta_data = {**item.meta_data, **meta_data}
            return await self.update(item)
        return None

    async def delete(self, item_id: UUID) -> bool:
        """Delete a URL content record."""
        item = await self.get_by_id(item_id)
        if item:
            await self.session.delete(item)
            await self.session.commit()
            return True
        return False

