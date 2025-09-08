"""
Start chat session use case.

Handles creating new chat sessions.
"""

from typing import Optional

from ...core.entities.chat_session import ChatSession
from ...core.repositories.chat_repository import ChatRepository
from ...core.repositories.topic_repository import TopicRepository
from ..common.base_use_case import BaseUseCase
from ..common.exceptions import NotFoundError, ValidationError


class StartChatSessionRequest:
    """Request model for starting a chat session."""
    
    def __init__(
        self,
        topic_id: Optional[int] = None,
        user_id: Optional[int] = None,
        title: Optional[str] = None
    ):
        self.topic_id = topic_id
        self.user_id = user_id
        self.title = title


class StartChatSessionUseCase(BaseUseCase):
    """Use case for starting a new chat session."""
    
    def __init__(
        self,
        chat_repository: ChatRepository,
        topic_repository: TopicRepository
    ):
        super().__init__()
        self._chat_repository = chat_repository
        self._topic_repository = topic_repository
    
    async def execute(self, request: StartChatSessionRequest) -> ChatSession:
        """Execute the start chat session use case."""
        self.log_execution_start("start_chat_session", 
                                topic_id=request.topic_id, 
                                user_id=request.user_id)
        
        try:
            # Validate input
            await self._validate_request(request)
            
            # Create chat session
            session = ChatSession(
                topic_id=request.topic_id,
                user_id=request.user_id,
                title=request.title
            )
            
            # Save session
            await self._chat_repository.save_session(session)
            
            # Update topic conversation count if topic is specified
            if request.topic_id:
                topic = await self._topic_repository.get_by_id(request.topic_id)
                if topic:
                    topic.increment_conversations()
                    await self._topic_repository.save(topic)
            
            self.log_execution_end("start_chat_session", session_id=session.id)
            return session
            
        except Exception as e:
            self.log_error("start_chat_session", e, 
                          topic_id=request.topic_id, 
                          user_id=request.user_id)
            raise
    
    async def _validate_request(self, request: StartChatSessionRequest) -> None:
        """Validate the start chat session request."""
        # Validate topic exists if provided
        if request.topic_id:
            topic = await self._topic_repository.get_by_id(request.topic_id)
            if not topic:
                raise NotFoundError("Topic", str(request.topic_id))
            
            if not topic.is_active():
                raise ValidationError("Cannot start chat session for inactive topic", "topic_id")
        
        # Validate title length if provided
        if request.title and len(request.title) > 200:
            raise ValidationError("Session title too long (max 200 characters)", "title")