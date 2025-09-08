"""
Send message use case.

Handles sending messages in chat sessions and generating AI responses.
"""

from typing import Optional, Dict, Any, List

from ...core.entities.chat_session import ChatSession
from ...core.repositories.chat_repository import ChatRepository
from ...core.repositories.document_repository import DocumentRepository
from ...core.domain_services.chat_service import ChatService, ChatContext
from ...core.domain_services.vector_search_service import VectorSearchService
from ...core.value_objects.chat_message import ChatMessage
from ..common.base_use_case import BaseUseCase
from ..common.exceptions import NotFoundError, ValidationError, BusinessRuleViolationError


class SendMessageRequest:
    """Request model for sending a message."""
    
    def __init__(
        self,
        session_id: str,
        message: str,
        use_context: bool = True,
        max_context_chunks: int = 5,
        model_config: Optional[Dict[str, Any]] = None
    ):
        self.session_id = session_id
        self.message = message
        self.use_context = use_context
        self.max_context_chunks = max_context_chunks
        self.model_config = model_config or {}


class SendMessageResult:
    """Result model for sending a message."""
    
    def __init__(
        self,
        user_message: ChatMessage,
        assistant_message: ChatMessage,
        context_used: bool,
        relevant_chunks_count: int,
        processing_time: float
    ):
        self.user_message = user_message
        self.assistant_message = assistant_message
        self.context_used = context_used
        self.relevant_chunks_count = relevant_chunks_count
        self.processing_time = processing_time


class SendMessageUseCase(BaseUseCase):
    """Use case for sending a message in a chat session."""
    
    def __init__(
        self,
        chat_repository: ChatRepository,
        document_repository: DocumentRepository,
        chat_service: ChatService,
        vector_search_service: VectorSearchService
    ):
        super().__init__()
        self._chat_repository = chat_repository
        self._document_repository = document_repository
        self._chat_service = chat_service
        self._vector_search_service = vector_search_service
    
    async def execute(self, request: SendMessageRequest) -> SendMessageResult:
        """Execute the send message use case."""
        import time
        start_time = time.time()
        
        self.log_execution_start("send_message", 
                                session_id=request.session_id,
                                message_length=len(request.message))
        
        try:
            # Validate input
            self._validate_request(request)
            
            # Get chat session
            session = await self._chat_repository.get_session_by_id(request.session_id)
            if not session:
                raise NotFoundError("ChatSession", request.session_id)
            
            if not session.is_active:
                raise BusinessRuleViolationError("Cannot send message to inactive session")
            
            # Create user message
            user_message = ChatMessage.user_message(request.message)
            
            # Add user message to session
            await self._chat_repository.add_message_to_session(request.session_id, user_message)
            session.add_message(user_message)
            
            # Determine if context should be used
            use_context = request.use_context and self._chat_service.should_use_context(
                request.message, session
            )
            
            # Build context for AI response
            context = await self._build_chat_context(
                session, 
                request.message, 
                use_context, 
                request.max_context_chunks
            )
            
            # Generate AI response
            response_content = await self._chat_service.generate_response(
                request.message,
                context,
                request.model_config
            )
            
            # Create assistant message
            assistant_message = ChatMessage.assistant_message(
                response_content,
                metadata={
                    "context_used": use_context,
                    "relevant_chunks": len(context.relevant_chunks),
                    "model_config": request.model_config
                }
            )
            
            # Add assistant message to session
            await self._chat_repository.add_message_to_session(request.session_id, assistant_message)
            session.add_message(assistant_message)
            
            processing_time = time.time() - start_time
            
            result = SendMessageResult(
                user_message=user_message,
                assistant_message=assistant_message,
                context_used=use_context,
                relevant_chunks_count=len(context.relevant_chunks),
                processing_time=processing_time
            )
            
            self.log_execution_end("send_message", 
                                  session_id=request.session_id,
                                  response_length=len(response_content),
                                  processing_time=processing_time)
            return result
            
        except Exception as e:
            self.log_error("send_message", e, session_id=request.session_id)
            raise
    
    def _validate_request(self, request: SendMessageRequest) -> None:
        """Validate the send message request."""
        if not request.session_id or not request.session_id.strip():
            raise ValidationError("Session ID is required", "session_id")
        
        if not request.message or not request.message.strip():
            raise ValidationError("Message content is required", "message")
        
        if len(request.message) > 10000:
            raise ValidationError("Message too long (max 10000 characters)", "message")
        
        if request.max_context_chunks <= 0 or request.max_context_chunks > 20:
            raise ValidationError("Max context chunks must be between 1 and 20", "max_context_chunks")
    
    async def _build_chat_context(
        self,
        session: ChatSession,
        message: str,
        use_context: bool,
        max_context_chunks: int
    ) -> ChatContext:
        """Build chat context for AI response generation."""
        relevant_chunks = []
        
        if use_context:
            # Search for relevant document chunks
            search_results = await self._vector_search_service.search_similar_chunks(
                query=message,
                limit=max_context_chunks,
                threshold=0.7
            )
            relevant_chunks = [result.chunk for result in search_results]
        
        # Get conversation history (last 10 messages)
        conversation_history = session.get_conversation_context(max_messages=10)
        
        return ChatContext(
            relevant_chunks=relevant_chunks,
            conversation_history=conversation_history,
            metadata={
                "session_id": session.id,
                "topic_id": session.topic_id,
                "message_count": session.get_message_count()
            }
        )