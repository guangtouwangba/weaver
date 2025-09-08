"""
Chat domain service.

Handles chat-related business logic and AI interactions.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..entities.chat_session import ChatSession
from ..value_objects.chat_message import ChatMessage
from ..value_objects.document_chunk import DocumentChunk


class ChatContext:
    """Chat context containing relevant information for response generation."""
    
    def __init__(
        self, 
        relevant_chunks: List[DocumentChunk], 
        conversation_history: List[ChatMessage],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.relevant_chunks = relevant_chunks
        self.conversation_history = conversation_history
        self.metadata = metadata or {}


class ChatService(ABC):
    """Abstract domain service for chat operations."""
    
    @abstractmethod
    async def generate_response(
        self, 
        message: str, 
        context: ChatContext,
        model_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate AI response based on message and context."""
        pass
    
    @abstractmethod
    async def generate_session_title(self, messages: List[ChatMessage]) -> str:
        """Generate a title for a chat session based on messages."""
        pass
    
    @abstractmethod
    async def generate_session_summary(self, messages: List[ChatMessage]) -> str:
        """Generate a summary for a chat session."""
        pass
    
    @abstractmethod
    async def extract_intent(self, message: str) -> Dict[str, Any]:
        """Extract user intent from message."""
        pass
    
    @abstractmethod
    async def suggest_follow_up_questions(
        self, 
        context: ChatContext,
        count: int = 3
    ) -> List[str]:
        """Suggest follow-up questions based on context."""
        pass
    
    @abstractmethod
    async def evaluate_response_quality(
        self, 
        question: str, 
        response: str, 
        context: ChatContext
    ) -> Dict[str, Any]:
        """Evaluate the quality of a generated response."""
        pass
    
    @abstractmethod
    async def detect_sensitive_content(self, message: str) -> Dict[str, Any]:
        """Detect sensitive or inappropriate content."""
        pass
    
    @abstractmethod
    def format_context_for_ai(self, context: ChatContext) -> str:
        """Format context information for AI model consumption."""
        pass
    
    @abstractmethod
    def should_use_context(self, message: str, session: ChatSession) -> bool:
        """Determine if context should be used for this message."""
        pass