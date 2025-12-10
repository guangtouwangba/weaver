"""Chat session management use cases."""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from research_agent.domain.entities.chat import ChatSession
from research_agent.infrastructure.database.repositories.sqlalchemy_chat_repo import (
    SQLAlchemyChatRepository,
)

# =============================================================================
# DTOs
# =============================================================================


@dataclass
class SessionDTO:
    """Chat session DTO."""

    id: str
    project_id: str
    title: str
    is_shared: bool
    message_count: int
    created_at: str
    updated_at: str
    last_message_at: Optional[str]


# =============================================================================
# Create Session Use Case
# =============================================================================


@dataclass
class CreateSessionInput:
    """Input for create session use case."""

    project_id: UUID
    title: str = "New Conversation"
    is_shared: bool = True
    user_id: Optional[UUID] = None  # Required if is_shared=False


@dataclass
class CreateSessionOutput:
    """Output for create session use case."""

    session: SessionDTO


class CreateSessionUseCase:
    """Use case for creating a new chat session."""

    def __init__(self, chat_repo: SQLAlchemyChatRepository):
        self._chat_repo = chat_repo

    async def execute(self, input: CreateSessionInput) -> CreateSessionOutput:
        """Execute the use case."""
        # Validate: private sessions require user_id
        user_id = None
        if not input.is_shared:
            if input.user_id is None:
                raise ValueError("user_id is required for private sessions")
            user_id = input.user_id

        session = ChatSession(
            project_id=input.project_id,
            title=input.title,
            is_shared=input.is_shared,
            user_id=user_id,
        )

        created_session = await self._chat_repo.create_session(session)

        return CreateSessionOutput(session=_session_to_dto(created_session, message_count=0))


# =============================================================================
# List Sessions Use Case
# =============================================================================


@dataclass
class ListSessionsInput:
    """Input for list sessions use case."""

    project_id: UUID
    user_id: Optional[UUID] = None
    include_shared: bool = True


@dataclass
class ListSessionsOutput:
    """Output for list sessions use case."""

    sessions: List[SessionDTO]
    total: int


class ListSessionsUseCase:
    """Use case for listing chat sessions."""

    def __init__(self, chat_repo: SQLAlchemyChatRepository):
        self._chat_repo = chat_repo

    async def execute(self, input: ListSessionsInput) -> ListSessionsOutput:
        """Execute the use case."""
        sessions_with_counts = await self._chat_repo.list_sessions(
            project_id=input.project_id,
            user_id=input.user_id,
            include_shared=input.include_shared,
        )

        return ListSessionsOutput(
            sessions=[
                _session_to_dto(session, message_count)
                for session, message_count in sessions_with_counts
            ],
            total=len(sessions_with_counts),
        )


# =============================================================================
# Update Session Use Case
# =============================================================================


@dataclass
class UpdateSessionInput:
    """Input for update session use case."""

    session_id: UUID
    title: str


@dataclass
class UpdateSessionOutput:
    """Output for update session use case."""

    session: Optional[SessionDTO]
    success: bool


class UpdateSessionUseCase:
    """Use case for updating a chat session."""

    def __init__(self, chat_repo: SQLAlchemyChatRepository):
        self._chat_repo = chat_repo

    async def execute(self, input: UpdateSessionInput) -> UpdateSessionOutput:
        """Execute the use case."""
        updated_session = await self._chat_repo.update_session(
            session_id=input.session_id,
            title=input.title,
        )

        if updated_session is None:
            return UpdateSessionOutput(session=None, success=False)

        # Get message count
        message_count = await self._chat_repo.get_session_message_count(input.session_id)

        return UpdateSessionOutput(
            session=_session_to_dto(updated_session, message_count),
            success=True,
        )


# =============================================================================
# Delete Session Use Case
# =============================================================================


@dataclass
class DeleteSessionInput:
    """Input for delete session use case."""

    session_id: UUID


@dataclass
class DeleteSessionOutput:
    """Output for delete session use case."""

    success: bool


class DeleteSessionUseCase:
    """Use case for deleting a chat session."""

    def __init__(self, chat_repo: SQLAlchemyChatRepository):
        self._chat_repo = chat_repo

    async def execute(self, input: DeleteSessionInput) -> DeleteSessionOutput:
        """Execute the use case."""
        success = await self._chat_repo.delete_session(input.session_id)
        return DeleteSessionOutput(success=success)


# =============================================================================
# Get or Create Default Session Use Case
# =============================================================================


@dataclass
class GetOrCreateDefaultSessionInput:
    """Input for get or create default session use case."""

    project_id: UUID
    user_id: Optional[UUID] = None


@dataclass
class GetOrCreateDefaultSessionOutput:
    """Output for get or create default session use case."""

    session: SessionDTO
    created: bool


class GetOrCreateDefaultSessionUseCase:
    """Use case for getting or creating a default session."""

    def __init__(self, chat_repo: SQLAlchemyChatRepository):
        self._chat_repo = chat_repo

    async def execute(
        self, input: GetOrCreateDefaultSessionInput
    ) -> GetOrCreateDefaultSessionOutput:
        """Execute the use case."""
        # Check if any session exists
        sessions_with_counts = await self._chat_repo.list_sessions(
            project_id=input.project_id,
            user_id=input.user_id,
            include_shared=True,
        )

        if sessions_with_counts:
            # Return the first session (most recent by last_message_at)
            session, message_count = sessions_with_counts[0]
            return GetOrCreateDefaultSessionOutput(
                session=_session_to_dto(session, message_count),
                created=False,
            )

        # Create a new default session
        session = await self._chat_repo.get_or_create_default_session(
            project_id=input.project_id,
            user_id=input.user_id,
        )

        return GetOrCreateDefaultSessionOutput(
            session=_session_to_dto(session, message_count=0),
            created=True,
        )


# =============================================================================
# Helper Functions
# =============================================================================


def _session_to_dto(session: ChatSession, message_count: int) -> SessionDTO:
    """Convert a ChatSession entity to a SessionDTO."""
    return SessionDTO(
        id=str(session.id),
        project_id=str(session.project_id),
        title=session.title,
        is_shared=session.is_shared,
        message_count=message_count,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        last_message_at=session.last_message_at.isoformat() if session.last_message_at else None,
    )

