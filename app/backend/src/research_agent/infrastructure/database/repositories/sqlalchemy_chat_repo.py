"""SQLAlchemy implementation of chat repository."""

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
            user_id=message.user_id,
            role=message.role,
            content=message.content,
            sources=message.sources,
            context_refs=message.context_refs,
            created_at=message.created_at,
        )
        self._session.add(model)
        await self._session.commit()

    async def get_history(
        self,
        project_id: UUID,
        limit: int = 50,
        user_id: str | None = None,
    ) -> list[ChatMessage]:
        """
        Get chat history for a project.

        Args:
            project_id: The project ID
            limit: Maximum number of messages to return
            user_id: Optional user ID for isolation

        Returns:
            List of ChatMessage entities, ordered by created_at ascending
        """
        query = (
            select(ChatMessageModel)
            .where(ChatMessageModel.project_id == project_id)
            .order_by(ChatMessageModel.created_at.asc())
            .limit(limit)
        )

        if user_id:
            query = query.where(ChatMessageModel.user_id == user_id)

        result = await self._session.execute(query)
        models = result.scalars().all()

        return [
            ChatMessage(
                id=m.id,
                project_id=m.project_id,
                user_id=m.user_id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                context_refs=m.context_refs,
                created_at=m.created_at,
            )
            for m in models
        ]

    async def clear_history(self, project_id: UUID, user_id: str | None = None) -> int:
        """
        Clear all chat messages for a project.

        Returns:
            Number of messages deleted
        """
        from sqlalchemy import delete

        query = delete(ChatMessageModel).where(ChatMessageModel.project_id == project_id)
        if user_id:
            query = query.where(ChatMessageModel.user_id == user_id)

        result = await self._session.execute(query)
        await self._session.commit()
        return result.rowcount
