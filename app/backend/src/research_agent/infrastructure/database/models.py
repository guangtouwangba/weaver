"""SQLAlchemy ORM models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class ProjectModel(Base):
    """Project ORM model."""

    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    documents: Mapped[List["DocumentModel"]] = relationship(
        "DocumentModel", back_populates="project", cascade="all, delete-orphan"
    )
    canvas: Mapped[Optional["CanvasModel"]] = relationship(
        "CanvasModel", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[List["ChatSessionModel"]] = relationship(
        "ChatSessionModel", back_populates="project", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[List["ChatMessageModel"]] = relationship(
        "ChatMessageModel", back_populates="project", cascade="all, delete-orphan"
    )
    chat_memories: Mapped[List["ChatMemoryModel"]] = relationship(
        "ChatMemoryModel", back_populates="project", cascade="all, delete-orphan"
    )
    chat_summary: Mapped[Optional["ChatSummaryModel"]] = relationship(
        "ChatSummaryModel", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )


class DocumentModel(Base):
    """Document ORM model."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/pdf")
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    graph_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Long context mode fields
    full_content: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Full document content for long context
    content_token_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Cached token count
    parsing_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # Parsing metadata (layout, tables, etc.)

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="documents")
    chunks: Mapped[List["DocumentChunkModel"]] = relationship(
        "DocumentChunkModel", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunkModel(Base):
    """Document chunk ORM model for RAG."""

    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)
    chunk_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    content_tsvector: Mapped[Optional[Any]] = mapped_column(TSVECTOR, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Citation and positioning fields
    char_start: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Character start position in original document
    char_end: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Character end position
    paragraph_index: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Paragraph index
    sentence_index: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Sentence index for precise citation

    # Relationships
    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="chunks")


class CanvasModel(Base):
    """Canvas ORM model for storing node and edge data."""

    __tablename__ = "canvases"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )  # Version for optimistic locking
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="canvas")


class ChatSessionModel(Base):
    """
    Chat session ORM model for managing multiple conversations per project.

    Supports both shared sessions (visible to all devices) and private sessions
    (visible only to the user/device that created them).
    """

    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # NULL = shared session, has value = private session for that user/device
    user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Conversation")
    # Redundant field for easier querying: True = shared, False = private
    is_shared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Timestamp of last message for sorting sessions
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="chat_sessions")
    messages: Mapped[List["ChatMessageModel"]] = relationship(
        "ChatMessageModel", back_populates="session", cascade="all, delete-orphan"
    )


class ChatMessageModel(Base):
    """Chat message ORM model for storing conversation history."""

    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    session_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for backward compatibility during migration
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' or 'ai'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="chat_messages")
    session: Mapped[Optional["ChatSessionModel"]] = relationship(
        "ChatSessionModel", back_populates="messages"
    )


class ChatMemoryModel(Base):
    """
    Chat memory ORM model for storing vectorized conversation memories.

    This enables semantic retrieval of past conversations (Long-Term Episodic Memory).
    Each memory represents a Q&A interaction that can be retrieved by similarity search.
    """

    __tablename__ = "chat_memories"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # The content stores the formatted Q&A pair: "User: <question>\nAssistant: <answer>"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Vector embedding for semantic search (1536 dimensions for OpenAI embeddings)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)
    # Metadata for filtering and context (named memory_metadata to avoid SQLAlchemy reserved name)
    memory_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=dict
    )
    # Timestamp for temporal ordering and decay
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="chat_memories")


class ChatSummaryModel(Base):
    """
    Chat summary ORM model for storing session summaries (Short-Term Working Memory).

    This stores the summarized version of older conversation turns to maintain
    context while staying within token limits.
    """

    __tablename__ = "chat_summaries"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One summary per project
        index=True,
    )
    # The summarized content of older conversation turns
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Number of messages that have been summarized
    summarized_message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Timestamp of last update
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="chat_summary")


class TaskQueueModel(Base):
    """Task queue ORM model for background job processing."""

    __tablename__ = "task_queue"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # ✅ Environment isolation: tasks are only processed by workers in the same environment
    environment: Mapped[str] = mapped_column(
        String(50), nullable=False, default="development", index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EntityModel(Base):
    """Entity ORM model for knowledge graph nodes."""

    __tablename__ = "entities"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entity_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel")
    document: Mapped[Optional["DocumentModel"]] = relationship("DocumentModel")
    outgoing_relations: Mapped[List["RelationModel"]] = relationship(
        "RelationModel",
        foreign_keys="RelationModel.source_entity_id",
        back_populates="source_entity",
    )
    incoming_relations: Mapped[List["RelationModel"]] = relationship(
        "RelationModel",
        foreign_keys="RelationModel.target_entity_id",
        back_populates="target_entity",
    )


class RelationModel(Base):
    """Relation ORM model for knowledge graph edges."""

    __tablename__ = "relations"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    source_entity_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    target_entity_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(nullable=True, default=1.0)
    relation_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel")
    source_entity: Mapped["EntityModel"] = relationship(
        "EntityModel", foreign_keys=[source_entity_id], back_populates="outgoing_relations"
    )
    target_entity: Mapped["EntityModel"] = relationship(
        "EntityModel", foreign_keys=[target_entity_id], back_populates="incoming_relations"
    )


class CurriculumModel(Base):
    """Curriculum ORM model for storing learning paths."""

    __tablename__ = "curriculums"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    steps: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    total_duration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel")


class EvaluationLogModel(Base):
    """Evaluation log ORM model for storing RAG quality metrics."""

    __tablename__ = "evaluation_logs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )

    # Test case information
    test_case_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    ground_truth: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Retrieval information
    chunking_strategy: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    retrieval_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    retrieved_contexts: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)

    # Generation information
    generated_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Evaluation metrics (Ragas)
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Metadata
    evaluation_type: Mapped[str] = mapped_column(String(50), nullable=False, default="realtime")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project: Mapped[Optional["ProjectModel"]] = relationship("ProjectModel")


# =============================================================================
# Configuration Center Models
# =============================================================================


class GlobalSettingModel(Base):
    """
    Global settings ORM model.

    Stores system-wide configuration that applies to all projects.
    Priority: Project Settings > Global Settings > Environment Variables
    """

    __tablename__ = "global_settings"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    value: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    category: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # model, api_key, rag_strategy, advanced
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_encrypted: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProjectSettingModel(Base):
    """
    Project-specific settings ORM model.

    Stores configuration that overrides global settings for a specific project.
    Priority: Project Settings > Global Settings > Environment Variables
    """

    __tablename__ = "project_settings"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    value: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    category: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # model, api_key, rag_strategy, advanced
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_encrypted: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Unique constraint: each project can have only one setting per key
    __table_args__ = (
        UniqueConstraint("project_id", "key", name="uq_project_settings_project_key"),
    )

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel")


class UserSettingModel(Base):
    """
    User-specific settings ORM model.

    Stores configuration for individual users.
    Priority: User Settings > Project Settings > Global Settings > Environment Variables
    """

    __tablename__ = "user_settings"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    value: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    category: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # model, api_key, rag_strategy, advanced
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_encrypted: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Unique constraint: each user can have only one setting per key
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_user_settings_user_key"),)
