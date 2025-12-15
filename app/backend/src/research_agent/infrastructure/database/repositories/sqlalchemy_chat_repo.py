"""SQLAlchemy implementation of chat repository."""

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.chat import ChatMessage, ChatSession
from research_agent.infrastructure.database.models import (
    ChatMessageModel,
    ChatSessionModel,
    ProjectModel,
)


class SQLAlchemyChatRepository:
    """SQLAlchemy implementation of chat repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # =========================================================================
    # Session Management Methods
    # =========================================================================

    async def create_session(self, session: ChatSession) -> ChatSession:
        """Create a new chat session."""
        model = ChatSessionModel(
            id=session.id,
            project_id=session.project_id,
            user_id=session.user_id,
            title=session.title,
            is_shared=session.is_shared,
            last_message_at=session.last_message_at,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._session_model_to_entity(model)

    async def get_session(self, session_id: UUID) -> Optional[ChatSession]:
        """Get a chat session by ID."""
        stmt = select(ChatSessionModel).where(ChatSessionModel.id == session_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._session_model_to_entity(model)

    async def list_sessions(
        self,
        project_id: UUID,
        user_id: Optional[UUID] = None,
        include_shared: bool = True,
    ) -> List[Tuple[ChatSession, int]]:
        """
        List chat sessions for a project.

        Args:
            project_id: The project ID
            user_id: If provided, include private sessions for this user
            include_shared: If True, include shared sessions

        Returns:
            List of (ChatSession, message_count) tuples, ordered by last_message_at desc
        """
        # Build the filter conditions
        conditions = [ChatSessionModel.project_id == project_id]

        if user_id is not None and include_shared:
            # Include both user's private sessions and shared sessions
            conditions.append(
                or_(
                    ChatSessionModel.user_id == user_id,
                    ChatSessionModel.is_shared == True,  # noqa: E712
                )
            )
        elif user_id is not None:
            # Only user's private sessions
            conditions.append(ChatSessionModel.user_id == user_id)
        elif include_shared:
            # Only shared sessions
            conditions.append(ChatSessionModel.is_shared == True)  # noqa: E712
        else:
            # No sessions match
            return []

        # Subquery to count messages per session
        message_count_subquery = (
            select(
                ChatMessageModel.session_id,
                func.count(ChatMessageModel.id).label("message_count"),
            )
            .group_by(ChatMessageModel.session_id)
            .subquery()
        )

        # Main query with message count
        stmt = (
            select(
                ChatSessionModel,
                func.coalesce(message_count_subquery.c.message_count, 0).label("message_count"),
            )
            .outerjoin(
                message_count_subquery,
                ChatSessionModel.id == message_count_subquery.c.session_id,
            )
            .where(*conditions)
            .order_by(ChatSessionModel.last_message_at.desc().nulls_last())
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        return [
            (self._session_model_to_entity(row.ChatSessionModel), row.message_count) for row in rows
        ]

    async def update_session(
        self,
        session_id: UUID,
        title: Optional[str] = None,
    ) -> Optional[ChatSession]:
        """Update a chat session's title."""
        update_data = {"updated_at": datetime.utcnow()}
        if title is not None:
            update_data["title"] = title

        stmt = (
            update(ChatSessionModel)
            .where(ChatSessionModel.id == session_id)
            .values(**update_data)
            .returning(ChatSessionModel)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._session_model_to_entity(model)

    async def delete_session(self, session_id: UUID) -> bool:
        """
        Delete a chat session and all its messages (cascade).

        Returns True if a session was deleted, False if not found.
        """
        stmt = delete(ChatSessionModel).where(ChatSessionModel.id == session_id)
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0

    async def update_session_last_message_time(
        self, session_id: UUID, timestamp: Optional[datetime] = None
    ) -> None:
        """Update the last_message_at timestamp for a session."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        stmt = (
            update(ChatSessionModel)
            .where(ChatSessionModel.id == session_id)
            .values(last_message_at=timestamp, updated_at=datetime.utcnow())
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def get_or_create_default_session(
        self, project_id: UUID, user_id: Optional[UUID] = None
    ) -> ChatSession:
        """
        Get the default session for a project, or create one if it doesn't exist.

        For backward compatibility, this creates a shared session.
        """
        # Ensure project exists first (to avoid ForeignKeyViolationError)
        # This handles cases where frontend might access a project ID not yet in DB (e.g. dev reset)
        project_exists = await self._session.execute(
            select(ProjectModel.id).where(ProjectModel.id == project_id)
        )
        if not project_exists.scalar_one_or_none():
            # Auto-create project to unblock (dev convenience)
            # In production, this might be better as a 404, but for "fix this" request, auto-healing is safer
            project = ProjectModel(
                id=project_id,
                name="Default Project",
                description="Auto-created default project",
            )
            self._session.add(project)
            await self._session.flush()

        # Try to find an existing default session
        stmt = (
            select(ChatSessionModel)
            .where(
                ChatSessionModel.project_id == project_id,
                ChatSessionModel.is_shared == True,  # noqa: E712
            )
            .order_by(ChatSessionModel.created_at.asc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is not None:
            return self._session_model_to_entity(model)

        # Create a new default session
        default_session = ChatSession(
            project_id=project_id,
            title="Default Conversation",
            user_id=None,
            is_shared=True,
        )
        return await self.create_session(default_session)

    def _session_model_to_entity(self, model: ChatSessionModel) -> ChatSession:
        """Convert a ChatSessionModel to a ChatSession entity."""
        return ChatSession(
            id=model.id,
            project_id=model.project_id,
            user_id=model.user_id,
            title=model.title,
            is_shared=model.is_shared,
            last_message_at=model.last_message_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # =========================================================================
    # Message Management Methods
    # =========================================================================

    async def save(self, message: ChatMessage) -> None:
        """Save a chat message."""
        model = ChatMessageModel(
            id=message.id,
            project_id=message.project_id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            sources=message.sources,
            created_at=message.created_at,
        )
        self._session.add(model)
        await self._session.commit()

        # Update session's last_message_at if session_id is provided
        if message.session_id:
            await self.update_session_last_message_time(message.session_id, message.created_at)

    async def get_history(
        self,
        project_id: UUID,
        session_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> List[ChatMessage]:
        """
        Get chat history.

        Args:
            project_id: The project ID (used for validation)
            session_id: If provided, get history for this specific session
            limit: Maximum number of messages to return

        Returns:
            List of ChatMessage entities, ordered by created_at ascending
        """
        if session_id is not None:
            # Get history for a specific session
            stmt = (
                select(ChatMessageModel)
                .where(
                    ChatMessageModel.session_id == session_id,
                    ChatMessageModel.project_id == project_id,
                )
                .order_by(ChatMessageModel.created_at.asc())
                .limit(limit)
            )
        else:
            # Backward compatibility: get all messages for a project
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
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                created_at=m.created_at,
            )
            for m in models
        ]

    async def get_session_message_count(self, session_id: UUID) -> int:
        """Get the number of messages in a session."""
        stmt = select(func.count(ChatMessageModel.id)).where(
            ChatMessageModel.session_id == session_id
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0
