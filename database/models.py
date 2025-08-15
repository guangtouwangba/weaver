"""
SQLAlchemy 数据库模型
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, Text, BigInteger, Integer, DateTime, 
    ForeignKey, JSON, Index, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Text  # 临时使用Text代替VECTOR，生产环境应使用pgvector
import uuid

Base = declarative_base()


class Document(Base):
    """文档表"""
    __tablename__ = 'documents'
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    content = Column(Text)
    file_path = Column(String(1000))
    file_type = Column(String(50))
    file_size = Column(BigInteger, default=0)
    status = Column(String(50), default='pending')
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # 关系
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_documents_status', 'status'),
        Index('idx_documents_file_type', 'file_type'),
        Index('idx_documents_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title}, status={self.status})>"


class DocumentChunk(Base):
    """文档块表"""
    __tablename__ = 'document_chunks'
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(255), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    start_char = Column(Integer)
    end_char = Column(Integer)
    metadata = Column(JSON, default=dict)
    embedding_vector = Column(Text)  # 临时使用Text，生产环境应使用VECTOR(1536)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # 关系
    document = relationship("Document", back_populates="chunks")
    
    # 索引
    __table_args__ = (
        Index('idx_document_chunks_document_id', 'document_id'),
        Index('idx_document_chunks_chunk_index', 'document_id', 'chunk_index'),
    )
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"


class QueryHistory(Base):
    """查询历史表"""
    __tablename__ = 'query_history'
    
    id = Column(Integer, primary_key=True)
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50))
    strategy_used = Column(String(50))
    results_count = Column(Integer, default=0)
    response_time_ms = Column(Integer)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # 索引
    __table_args__ = (
        Index('idx_query_history_created_at', 'created_at'),
        Index('idx_query_history_query_type', 'query_type'),
        Index('idx_query_history_strategy', 'strategy_used'),
    )
    
    def __repr__(self):
        return f"<QueryHistory(id={self.id}, query_type={self.query_type}, created_at={self.created_at})>"


class UserSession(Base):
    """用户会话表"""
    __tablename__ = 'user_sessions'
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255))
    session_data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    # 索引
    __table_args__ = (
        Index('idx_user_sessions_user_id', 'user_id'),
        Index('idx_user_sessions_expires_at', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, created_at={self.created_at})>"


# 向量扩展表（可选，用于更复杂的向量操作）
class VectorIndex(Base):
    """向量索引表"""
    __tablename__ = 'vector_indexes'
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    chunk_id = Column(String(255), ForeignKey('document_chunks.id', ondelete='CASCADE'), nullable=False)
    vector_type = Column(String(50), default='embedding')  # embedding, keyword, etc.
    dimension = Column(Integer, default=1536)
    model_name = Column(String(100))  # text-embedding-ada-002, etc.
    vector_data = Column(Text)  # 临时使用Text，生产环境应使用VECTOR(1536)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # 索引
    __table_args__ = (
        Index('idx_vector_indexes_chunk_id', 'chunk_id'),
        Index('idx_vector_indexes_type', 'vector_type'),
        Index('idx_vector_indexes_model', 'model_name'),
    )
    
    def __repr__(self):
        return f"<VectorIndex(id={self.id}, chunk_id={self.chunk_id}, vector_type={self.vector_type})>"