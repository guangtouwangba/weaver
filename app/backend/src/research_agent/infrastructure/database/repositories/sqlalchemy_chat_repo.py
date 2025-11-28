"""SQLAlchemy implementation of chat repository."""

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.chat import ChatMessage
from research_agent.infrastructure.database.models import ChatMessageModel


class SQLAlchemyChatRepository:
    """SQLAlchemy implementation of chat repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, message: ChatMessage) -> None:
        """Save a chat message."""
        model = ChatMessageModel(
            id=message.id,
            project_id=message.project_id,
            role=message.role,
            content=message.content,
            sources=message.sources,
            created_at=message.created_at,
        )
        self._session.add(model)
        await self._session.commit()

    async def get_history(self, project_id: UUID, limit: int = 50) -> List[ChatMessage]:
        """Get chat history for a project."""
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.project_id == project_id)
            .order_by(ChatMessageModel.created_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [
            ChatMessage(
                id=m.id,
                project_id=m.project_id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                created_at=m.created_at,
            )
            for m in models
        ]

