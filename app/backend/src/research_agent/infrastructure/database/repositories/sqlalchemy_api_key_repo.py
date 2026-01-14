"""SQLAlchemy implementation of API Key repository."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.database.models import ApiKeyModel


class SQLAlchemyApiKeyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, api_key: ApiKeyModel) -> ApiKeyModel:
        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)
        return api_key

    async def get_by_hash(self, key_hash: str) -> ApiKeyModel | None:
        stmt = select(ApiKeyModel).where(ApiKeyModel.key_hash == key_hash)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_valid_by_hash(self, key_hash: str) -> ApiKeyModel | None:
        stmt = select(ApiKeyModel).where(
            ApiKeyModel.key_hash == key_hash, ApiKeyModel.revoked_at.is_(None)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_by_user(self, user_id: str) -> Sequence[ApiKeyModel]:
        stmt = (
            select(ApiKeyModel)
            .where(ApiKeyModel.user_id == user_id, ApiKeyModel.revoked_at.is_(None))
            .order_by(ApiKeyModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_last_used(self, key_id: UUID) -> None:
        api_key = await self.session.get(ApiKeyModel, key_id)
        if api_key:
            api_key.last_used_at = datetime.utcnow()
            await self.session.commit()

    async def revoke(self, key_id: UUID) -> None:
        api_key = await self.session.get(ApiKeyModel, key_id)
        if api_key:
            api_key.revoked_at = datetime.utcnow()
            await self.session.commit()
