from pydantic import BaseModel


class ContentFormat(str, Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


class MessageContent(BaseModel):
    content: str
    format: ContentFormat



class ChatMessage(BaseModel):
    id: str
    conversation_id: str
    content: MessageContent
    role: str
    created_at: datetime
    updated_at: datetime
    user_id: str
    is_read: bool
    is_deleted: bool
    is_pinned: bool
    is_edited: bool
    is_starred: bool
    is_read: bool
    additional_kwargs: dict[str, Any] = Field(default_factory=dict)



