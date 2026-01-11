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
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR, UUID
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
    # User ownership for multi-tenant isolation
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

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

    # Thumbnail fields for PDF preview
    thumbnail_path: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )  # Path to generated thumbnail image
    thumbnail_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # pending, processing, ready, error

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="documents")
    chunks: Mapped[List["DocumentChunkModel"]] = relationship(
        "DocumentChunkModel", back_populates="document", cascade="all, delete-orphan"
    )
    highlights: Mapped[List["HighlightModel"]] = relationship(
        "HighlightModel", back_populates="document", cascade="all, delete-orphan"
    )
    comments: Mapped[List["CommentModel"]] = relationship(
        "CommentModel", back_populates="document", cascade="all, delete-orphan"
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


class HighlightModel(Base):
    """Highlight ORM model for PDF annotations."""

    __tablename__ = "highlights"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str] = mapped_column(
        String(20), nullable=False, default="yellow"
    )  # yellow, green, blue, pink
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="highlight"
    )  # highlight, underline, strike, pen, etc.
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Selected text
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rects: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # Store rect positions for rendering
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="highlights")


class CommentModel(Base):
    """Comment ORM model for document comments/discussions."""

    __tablename__ = "comments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )  # For threaded replies
    page_number: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Optional page anchor
    highlight_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("highlights.id", ondelete="SET NULL"), nullable=True
    )  # Optional annotation anchor
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # For future auth
    author_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Anonymous")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="comments")
    parent: Mapped[Optional["CommentModel"]] = relationship(
        "CommentModel", remote_side="CommentModel.id", back_populates="replies"
    )
    replies: Mapped[List["CommentModel"]] = relationship(
        "CommentModel", back_populates="parent", cascade="all, delete-orphan"
    )


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
    # Context references for user messages: {url_ids: [], node_ids: [], nodes: []}
    context_refs: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
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


# =============================================================================
# Async File Cleanup Models
# =============================================================================


class PendingCleanupModel(Base):
    """
    Pending cleanup ORM model for tracking files that need async deletion.

    When a document is deleted, its physical files (local + remote storage) are
    cleaned up asynchronously. This table serves as a fallback queue to ensure
    files are eventually deleted even if the initial async cleanup fails.

    Design: Fire-and-Forget + Scheduled Cleanup
    - On document delete: Record pending cleanup, then fire async task
    - Async task: Delete files, then remove from pending_cleanups
    - Scheduled job: Periodically retry failed cleanups
    """

    __tablename__ = "pending_cleanups"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    # File path in storage (e.g., "projects/{project_id}/{uuid}.pdf")
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    # Storage type: "local", "supabase", or "both"
    storage_type: Mapped[str] = mapped_column(String(50), nullable=False, default="both")
    # Number of cleanup attempts
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Maximum retry attempts before giving up
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    # Last error message if cleanup failed
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # When this cleanup was scheduled
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # When the last attempt was made
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Optional: reference to original document (for debugging)
    document_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    project_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)


# =============================================================================
# Output Generation Models
# =============================================================================


class OutputModel(Base):
    """
    Output ORM model for storing generated outputs (mindmaps, summaries, etc.).

    This table stores the results of AI-generated outputs that users can create
    from their documents in the Canvas toolbox.
    """

    __tablename__ = "outputs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Output type: 'mindmap', 'summary', 'custom', etc.
    output_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Source document IDs that this output was generated from
    source_ids: Mapped[List[UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"
    )
    # Status: 'generating', 'complete', 'error', 'cancelled'
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="generating")
    # Optional title for the output
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Output data stored as JSONB (nodes, edges for mindmap, content for summary, etc.)
    data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    # Error message if generation failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    project: Mapped["ProjectModel"] = relationship("ProjectModel")


# =============================================================================
# Inbox & Collection Models
# =============================================================================


class TagModel(Base):
    """Tag ORM model for categorizing inbox items."""

    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="blue")
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("name", "user_id", name="uq_tags_name_user"),)

    # Relationships
    inbox_items: Mapped[List["InboxItemModel"]] = relationship(
        "InboxItemModel", secondary="inbox_item_tags", back_populates="tags"
    )


class InboxItemModel(Base):
    """Inbox Item ORM model."""

    __tablename__ = "inbox_items"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # link, pdf, note, video, article
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # extension, manual, upload
    meta_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, server_default="{}", nullable=False, default=dict
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_read: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    is_processed: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    tags: Mapped[List["TagModel"]] = relationship(
        "TagModel", secondary="inbox_item_tags", back_populates="inbox_items"
    )


class InboxItemTagModel(Base):
    """Association table for inbox items and tags."""

    __tablename__ = "inbox_item_tags"

    inbox_item_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inbox_items.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class UrlContentModel(Base):
    """URL Content ORM model for storing extracted content from URLs."""

    __tablename__ = "url_contents"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    platform: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # youtube, bilibili, douyin, web
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)  # video, article, link

    # Extracted content
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Article text or transcript
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Platform-specific metadata
    meta_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, server_default="{}", nullable=False, default=dict
    )

    # Processing status
    status: Mapped[str] = mapped_column(
        String(20), server_default="pending", nullable=False
    )  # pending, processing, completed, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    extracted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Project association (for studio sidebar persistence)
    project_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Optional: User ownership (for multi-tenant)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class ApiKeyModel(Base):
    """API Key ORM model for external collection access."""

    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
