"""
Topic database model.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.types import UserDefinedType
from .base import BaseModel


class Topic(BaseModel):
    """Topic model."""
    
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(255))
    core_concepts_discovered = Column(Integer, default=0, nullable=False)
    concept_relationships = Column(Integer, default=0, nullable=False)
    missing_materials_count = Column(Integer, default=0, nullable=False)
    user_id = Column(Integer)
    conversation_id = Column(String(255))
    parent_topic_id = Column(Integer, ForeignKey("topics.id"))
    settings = Column(JSON)
    status = Column(String(50))  # Simplified as string instead of enum for now
    total_resources = Column(Integer)
    total_conversations = Column(Integer)
    last_accessed_at = Column(DateTime)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime)


class Tag(BaseModel):
    """Tag model."""
    
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(255))
    description = Column(Text)
    usage_count = Column(Integer, default=0, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)


class TopicResource(BaseModel):
    """Topic resource model."""
    
    __tablename__ = "topic_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(255))
    resource_type = Column(String(50), nullable=False)  # Simplified as string
    is_parsed = Column(Boolean, default=False, nullable=False)
    parse_status = Column(String(50), nullable=False)  # Simplified as string
    parse_error = Column(Text)
    total_pages = Column(Integer)
    parsed_pages = Column(Integer, default=0, nullable=False)
    content_preview = Column(Text)
    resource_metadata = Column("metadata", JSON)  # Using explicit column name due to SQLAlchemy reserved word
    uploaded_at = Column(DateTime, nullable=False)
    parsed_at = Column(DateTime)
    last_accessed_at = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime)
    file_hash = Column(String(255))
    content_summary = Column(Text)
    parse_attempts = Column(Integer, default=0, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    access_level = Column(String(50), default="private", nullable=False)
    source_url = Column(Text)


class Conversation(BaseModel):
    """Conversation model."""
    
    __tablename__ = "conversations"
    
    id = Column(String(255), primary_key=True, index=True)  # String ID for conversations
    topic_id = Column(Integer, ForeignKey("topics.id"))
    title = Column(String(255))
    message_count = Column(Integer, default=0, nullable=False)
    conversation_data = Column(JSON)
    external_conversation_url = Column(Text)
    last_message_at = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime)