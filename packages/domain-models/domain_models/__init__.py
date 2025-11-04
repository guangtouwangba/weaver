"""Domain models and schemas for the knowledge platform."""

from domain_models.topic import GoalType, Topic, TopicStatus
from domain_models.topic_schemas import (
    TopicCreate,
    TopicListResponse,
    TopicProgressUpdate,
    TopicResponse,
    TopicStatistics,
    TopicUpdate,
)
from domain_models.topic_content import TopicContent, ContentSource, ContentStatus, ProcessingStatus
from domain_models.topic_content_schemas import (
    TopicContentCreate,
    TopicContentUpdate,
    TopicContentResponse,
    TopicContentListResponse,
    TopicContentStats,
)
from domain_models.conversation import Conversation, Message
from domain_models.conversation_schemas import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
    MessageListResponse,
)

__all__ = [
    # ORM Models
    "Topic",
    "TopicContent",
    "Conversation",
    "Message",
    # Enums
    "GoalType",
    "TopicStatus",
    "ContentSource",
    "ContentStatus",
    "ProcessingStatus",
    # Pydantic Schemas - Topic
    "TopicCreate",
    "TopicUpdate",
    "TopicResponse",
    "TopicProgressUpdate",
    "TopicListResponse",
    "TopicStatistics",
    # Pydantic Schemas - TopicContent
    "TopicContentCreate",
    "TopicContentUpdate",
    "TopicContentResponse",
    "TopicContentListResponse",
    "TopicContentStats",
    # Pydantic Schemas - Conversation
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationListResponse",
    # Pydantic Schemas - Message
    "MessageCreate",
    "MessageResponse",
    "MessageListResponse",
]
