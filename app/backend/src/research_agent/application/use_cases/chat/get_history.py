"""Get chat history use case."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from research_agent.infrastructure.database.repositories.sqlalchemy_chat_repo import (
    SQLAlchemyChatRepository,
)


@dataclass
class ChatMessageDTO:
    """Chat message DTO."""

    id: UUID
    role: str
    content: str
    session_id: Optional[UUID]
    sources: Optional[List[Dict[str, Any]]]
    context_refs: Optional[List[Dict[str, Any]]]
    created_at: str


@dataclass
class GetHistoryInput:
    """Input for get history use case."""

    project_id: UUID
    session_id: Optional[UUID] = None  # If provided, get history for this session only
    limit: int = 50


@dataclass
class GetHistoryOutput:
    """Output for get history use case."""

    messages: List[ChatMessageDTO]


class GetHistoryUseCase:
    """Use case for getting chat history."""

    def __init__(self, chat_repo: SQLAlchemyChatRepository):
        self._chat_repo = chat_repo

    async def execute(self, input: GetHistoryInput) -> GetHistoryOutput:
        """Execute the use case."""
        messages = await self._chat_repo.get_history(
            project_id=input.project_id,
            session_id=input.session_id,
            limit=input.limit,
        )

        return GetHistoryOutput(
            messages=[
                ChatMessageDTO(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    session_id=m.session_id,
                    sources=m.sources,
                    context_refs=getattr(m, "context_refs", None),
                    created_at=m.created_at.isoformat(),
                )
                for m in messages
            ]
        )
