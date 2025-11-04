"""TopicContent ORM model for content associated with topics."""

import datetime
import uuid
from enum import Enum

from sqlalchemy import Column, String, DateTime, Integer, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from rag_core.storage.database import Base


class ContentSource(str, Enum):
    """Content source types."""
    FILE_UPLOAD = "file_upload"
    URL = "url"
    EXISTING_DOC = "existing_doc"
    TEXT_INPUT = "text_input"


class ContentStatus(str, Enum):
    """Content learning status."""
    PENDING = "pending"           # 待消化
    READING = "reading"           # 阅读中
    UNDERSTOOD = "understood"     # 已理解
    QUESTIONED = "questioned"     # 有疑问
    PRACTICED = "practiced"       # 已实践


class ProcessingStatus(str, Enum):
    """Document processing status for RAG system."""
    NOT_STARTED = "not_started"   # 未开始处理
    PROCESSING = "processing"     # 处理中
    COMPLETED = "completed"       # 处理完成
    FAILED = "failed"             # 处理失败


class TopicContent(Base):
    """Model for content associated with a topic."""
    
    __tablename__ = "topic_contents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Content source
    source_type = Column(String, default=ContentSource.FILE_UPLOAD.value, nullable=False)
    
    # Content information
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    source_url = Column(String(1000), nullable=True)  # File path or URL
    document_id = Column(String, nullable=True)  # RAG system document ID
    
    # Processing status for RAG system
    processing_status = Column(String, default=ProcessingStatus.NOT_STARTED.value, nullable=False)
    processing_error = Column(Text, nullable=True)  # Error message if failed
    
    # Learning status
    status = Column(String, default=ContentStatus.PENDING.value, nullable=False)
    understanding_level = Column(Integer, default=0, nullable=False)  # 0-100
    
    # Metadata
    author = Column(String(200), nullable=True)
    publish_date = Column(DateTime, nullable=True)
    word_count = Column(Integer, nullable=True)
    estimated_time = Column(Integer, nullable=True)  # Minutes
    
    # User interaction
    notes = Column(Text, nullable=True)
    highlights = Column(ARRAY(Text), default=list, nullable=True)
    tags = Column(ARRAY(String), default=list, nullable=True)
    
    # Timestamps
    added_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_viewed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationship
    topic = relationship("Topic", back_populates="contents")

    def __repr__(self):
        return f"<TopicContent(id={self.id}, title='{self.title}', status={self.status})>"

