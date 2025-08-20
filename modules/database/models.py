"""
数据库模型

定义RAG系统的核心数据模型。
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import Column, String, Integer, BigInteger, Text, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB
import uuid
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

# 尝试导入VECTOR类型（需要pgvector扩展）
try:
    from pgvector.sqlalchemy import Vector as VECTOR
except ImportError:
    # 如果没有pgvector，使用Text作为替代
    VECTOR = lambda x: Text

from .connection import Base

# 枚举类型
class FileStatus(str, Enum):
    """文件状态"""
    UPLOADING = "uploading"
    AVAILABLE = "available"
    PROCESSING = "processing" 
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"
    QUARANTINED = "quarantined"

class TopicStatus(str, Enum):
    """主题状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    COMPLETED = "completed"

class ContentType(str, Enum):
    """内容类型"""
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    MD = "md"
    JSON = "json"
    CSV = "csv"

class Topic(Base):
    """主题模型"""
    __tablename__ = "topics"
    
    # 主键
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # 基础信息
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=TopicStatus.ACTIVE)
    
    # 统计信息
    total_resources: Mapped[int] = mapped_column(Integer, default=0)
    total_conversations: Mapped[int] = mapped_column(Integer, default=0)
    core_concepts_discovered: Mapped[int] = mapped_column(Integer, default=0)
    concept_relationships: Mapped[Optional[dict]] = mapped_column(JSONB, default=lambda: {})
    missing_materials_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 关联信息
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    parent_topic_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("topics.id"), nullable=True
    )
    
    # 配置信息
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # 关系
    files: Mapped[List["File"]] = relationship("File", back_populates="topic")
    parent_topic: Mapped[Optional["Topic"]] = relationship(
        "Topic", remote_side=[id], back_populates="child_topics"
    )
    child_topics: Mapped[List["Topic"]] = relationship(
        "Topic", back_populates="parent_topic"
    )

class File(Base):
    """文件模型 - 匹配实际数据库结构"""
    __tablename__ = "files"
    
    # 主键
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联信息 - 添加外键约束
    topic_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("topics.id"), nullable=True
    )
    
    # 文件信息 - 匹配实际数据库字段
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 存储信息 - 匹配实际数据库字段
    storage_bucket: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    storage_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    storage_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 状态 - 匹配实际数据库字段
    status: Mapped[str] = mapped_column(String(50), default='active')
    
    # 软删除 - 匹配实际数据库字段
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 时间戳 - 匹配实际数据库字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.current_timestamp()
    )
    
    # 关系
    topic: Mapped[Optional["Topic"]] = relationship("Topic", back_populates="files")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="file")

class Document(Base):
    """文档模型"""
    __tablename__ = "documents"
    
    # 主键
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    
    # 基础信息
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # 文件关联
    file_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey("files.id"), nullable=True
    )
    file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    
    # 处理状态
    status: Mapped[str] = mapped_column(String(50), default="pending")
    processing_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 元数据
    doc_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # 关系
    file: Mapped[Optional["File"]] = relationship("File", back_populates="documents")
    chunks: Mapped[List["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    """文档块模型"""
    __tablename__ = "document_chunks"
    
    # 主键
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    
    # 文档关联
    document_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("documents.id"), nullable=False
    )
    
    # 内容信息
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_char: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_char: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 向量嵌入（如果使用pgvector）
    embedding_vector: Mapped[Optional[str]] = mapped_column(VECTOR(1536), nullable=True)
    
    # 元数据
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # 关系
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
