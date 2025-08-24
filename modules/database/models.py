"""
数据库模型

定义RAG系统的核心数据模型。
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

# 尝试导入VECTOR类型（需要pgvector扩展）
try:
    from pgvector.sqlalchemy import Vector as VECTOR
except ImportError:
    # 如果没有pgvector，使用Text作为替代
    VECTOR = lambda x: Text

from modules.database.connection import Base

# Import enums will be done at the class level to avoid circular imports


class Topic(Base):
    """主题模型"""

    __tablename__ = "topics"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # 基础信息
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        ENUM("active", "archived", "draft", "completed", name="topic_status_enum"),
        default="active",
    )

    # 统计信息
    total_resources: Mapped[int] = mapped_column(Integer, default=0)
    total_conversations: Mapped[int] = mapped_column(Integer, default=0)
    core_concepts_discovered: Mapped[int] = mapped_column(Integer, default=0)
    concept_relationships: Mapped[int] = mapped_column(Integer, default=0)
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

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # 关联信息 - 添加Foreign key约束
    topic_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("topics.id"), nullable=True
    )

    # 文件信息 - 匹配实际数据库字段
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(String(200), nullable=False)

    # 存储信息 - 匹配实际数据库字段
    storage_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    storage_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # 状态 - 匹配实际数据库字段
    status: Mapped[str] = mapped_column(
        ENUM(
            "uploading",
            "available",
            "processing",
            "failed",
            "deleted",
            "quarantined",
            name="file_status_enum",
        ),
        default="uploading",
    )
    access_level: Mapped[str] = mapped_column(
        ENUM(
            "private",
            "public_read",
            "shared",
            "authenticated",
            name="access_level_enum",
        ),
        default="private",
    )
    download_count: Mapped[int] = mapped_column(Integer, default=0)

    # 软删除 - 匹配实际数据库字段
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # 时间戳 - 匹配实际数据库字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )

    # 关系
    topic: Mapped[Optional["Topic"]] = relationship("Topic", back_populates="files")
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="file"
    )


class Document(Base):
    """Document model"""

    __tablename__ = "documents"

    # Primary key
    id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # 基础信息
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # 文件关联
    file_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("files.id"), nullable=True
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
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document"
    )


class DocumentChunk(Base):
    """Document chunk model"""

    __tablename__ = "document_chunks"

    # Primary key
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

    # 元数据 - use chunk_metadata to avoid SQLAlchemy reserved word
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 关系
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
