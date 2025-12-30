"""SQLAlchemy implementation of Tag repository."""

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.database.models import TagModel


class SQLAlchemyTagRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tag: TagModel) -> TagModel:
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def get_by_id(self, tag_id: UUID) -> Optional[TagModel]:
        stmt = select(TagModel).where(TagModel.id == tag_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_name(self, name: str, user_id: Optional[str] = None) -> Optional[TagModel]:
        stmt = select(TagModel).where(TagModel.name == name)
        if user_id:
            stmt = stmt.where(TagModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_all(self, user_id: Optional[str] = None) -> Sequence[TagModel]:
        stmt = select(TagModel)
        if user_id:
            stmt = stmt.where(TagModel.user_id == user_id)
        stmt = stmt.order_by(TagModel.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete(self, tag_id: UUID) -> None:
        tag = await self.get_by_id(tag_id)
        if tag:
            await self.session.delete(tag)
            await self.session.commit()
