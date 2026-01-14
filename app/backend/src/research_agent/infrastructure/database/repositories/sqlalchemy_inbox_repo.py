"""SQLAlchemy implementation of Inbox repository."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from research_agent.infrastructure.database.models import InboxItemModel, TagModel


class SQLAlchemyInboxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, item: InboxItemModel) -> InboxItemModel:
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item, attribute_names=["tags"])
        return item

    async def get_by_id(self, item_id: UUID) -> InboxItemModel | None:
        stmt = (
            select(InboxItemModel)
            .where(InboxItemModel.id == item_id)
            .options(selectinload(InboxItemModel.tags))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_items(
        self,
        skip: int = 0,
        limit: int = 20,
        is_processed: bool | None = None,
        item_type: str | None = None,
        tag_id: UUID | None = None,
        search_query: str | None = None,
    ) -> Sequence[InboxItemModel]:
        stmt = select(InboxItemModel).options(selectinload(InboxItemModel.tags))

        # Filters
        if is_processed is not None:
            stmt = stmt.where(InboxItemModel.is_processed == is_processed)

        if item_type:
            stmt = stmt.where(InboxItemModel.type == item_type)

        if tag_id:
            stmt = stmt.join(InboxItemModel.tags).where(TagModel.id == tag_id)

        if search_query:
            stmt = stmt.where(
                (InboxItemModel.title.ilike(f"%{search_query}%"))
                | (InboxItemModel.content.ilike(f"%{search_query}%"))
            )

        # Ordering: Newest first
        stmt = stmt.order_by(desc(InboxItemModel.collected_at))

        # Pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, item: InboxItemModel) -> InboxItemModel:
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete(self, item_id: UUID) -> None:
        item = await self.get_by_id(item_id)
        if item:
            await self.session.delete(item)
            await self.session.commit()
