"""Conversation ORM model for chat sessions."""

import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from rag_core.storage.database import Base


class Conversation(Base):
    """Model for conversation sessions."""
    
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic information
    title = Column(String(200), nullable=True)  # Auto-generated or manual
    
    # Statistics
    message_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, nullable=True)
    
    # Relationships
    topic = relationship("Topic", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}', message_count={self.message_count})>"


class Message(Base):
    """Model for conversation messages."""
    
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Sources (for assistant messages)
    sources = Column(ARRAY(Text), nullable=True)  # Stored as JSON array temporarily, will be JSONB later
    
    # Embedding for semantic search with pgvector
    embedding = Column(Vector(1536), nullable=True)  # OpenAI text-embedding-3-small dimension
    
    # Metadata (extensible)
    # metadata = Column(Text, nullable=True)  # Will be JSONB later
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Relationship
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        preview = self.content[:50] if self.content else ""
        return f"<Message(id={self.id}, role='{self.role}', content='{preview}...')>"

