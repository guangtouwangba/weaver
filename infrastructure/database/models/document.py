"""
Document database model for RAG system.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Float, DateTime
from .base import BaseModel


class Document(BaseModel):
    """Document model for RAG system."""
    
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    file_id = Column(String(36), ForeignKey("files.id"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    is_processed = Column(Boolean, default=False, nullable=False)


class DocumentChunk(BaseModel):
    """Document chunk model for RAG system."""
    
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    start_position = Column(Integer, nullable=False)
    end_position = Column(Integer, nullable=False)


class QueryHistory(BaseModel):
    """Query history model."""
    
    __tablename__ = "query_history"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID
    user_id = Column(String(36), nullable=True)
    query = Column(Text, nullable=False)
    results_count = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)


class UserSession(BaseModel):
    """User session model."""
    
    __tablename__ = "user_sessions"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID
    user_id = Column(String(36), nullable=False)
    session_start = Column(DateTime, nullable=False)
    session_end = Column(DateTime, nullable=True)
    activity_count = Column(Integer, default=0, nullable=False)


class VectorIndex(BaseModel):
    """Vector index model."""
    
    __tablename__ = "vector_indexes"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    dimension = Column(Integer, nullable=False)
    index_type = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)