"""
SQLAlchemy models for the cronjob system with vector database and embedding support
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, 
    ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class CronJob(Base):
    """Job configurations for automated paper fetching"""
    __tablename__ = 'cronjobs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    keywords = Column(ARRAY(String), nullable=False)
    cron_expression = Column(String(100), nullable=True)
    interval_hours = Column(Integer, nullable=True)
    enabled = Column(Boolean, default=True)
    max_papers_per_run = Column(Integer, default=50)
    
    # Vector and embedding configuration
    embedding_provider = Column(String(50), default='openai')
    embedding_model = Column(String(100), default='text-embedding-3-small')
    vector_db_provider = Column(String(50), default='chroma')
    vector_db_config = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    job_runs = relationship("JobRun", back_populates="job", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_cronjobs_enabled', 'enabled'),
        Index('idx_cronjobs_provider', 'embedding_provider', 'vector_db_provider'),
    )

class JobRun(Base):
    """Job execution history and status tracking"""
    __tablename__ = 'job_runs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('cronjobs.id', ondelete='CASCADE'), nullable=False)
    
    # Status tracking
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'running', 'completed', 'failed', 'partial'
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Metrics
    papers_found = Column(Integer, default=0)
    papers_processed = Column(Integer, default=0)
    papers_skipped = Column(Integer, default=0)
    papers_embedded = Column(Integer, default=0)
    embedding_errors = Column(Integer, default=0)
    vector_db_errors = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    execution_log = Column(JSON, nullable=True)
    
    # Relationships
    job = relationship("CronJob", back_populates="job_runs")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_runs_job_id', 'job_id'),
        Index('idx_job_runs_status', 'status'),
        Index('idx_job_runs_started_at', 'started_at'),
    )

class Paper(Base):
    """Enhanced papers table with vector and embedding metadata"""
    __tablename__ = 'papers'
    
    id = Column(String(255), primary_key=True)
    arxiv_id = Column(String(50), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    authors = Column(ARRAY(String), nullable=False)
    abstract = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    categories = Column(ARRAY(String), nullable=False)
    published = Column(DateTime, nullable=False)
    pdf_url = Column(String(500), nullable=True)
    entry_id = Column(String(500), nullable=True)
    doi = Column(String(255), nullable=True)
    
    # Vector and embedding metadata
    embedding_provider = Column(String(50), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    vector_id = Column(String(255), nullable=True)
    embedding_status = Column(String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    embedding_error = Column(Text, nullable=True)
    last_embedded_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('arxiv_id', name='unique_arxiv_id'),
        UniqueConstraint('doi', name='unique_doi'),
        Index('idx_papers_embedding_status', 'embedding_status'),
        Index('idx_papers_embedding_provider', 'embedding_provider'),
        Index('idx_papers_published', 'published'),
        Index('idx_papers_categories', 'categories'),
    )

class VectorDBConfig(Base):
    """Vector database provider configurations"""
    __tablename__ = 'vector_db_configs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False)  # 'chroma', 'pinecone', 'weaviate', 'qdrant'
    config = Column(JSON, nullable=False)
    is_default = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_vector_db_configs_provider', 'provider'),
        Index('idx_vector_db_configs_default', 'is_default'),
    )

class EmbeddingConfig(Base):
    """Embedding model provider configurations"""
    __tablename__ = 'embedding_configs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False)  # 'openai', 'deepseek', 'anthropic', 'huggingface'
    model_name = Column(String(100), nullable=False)
    config = Column(JSON, nullable=True)
    is_default = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_embedding_configs_provider', 'provider'),
        Index('idx_embedding_configs_default', 'is_default'),
    )