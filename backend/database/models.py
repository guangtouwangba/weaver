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
    name = Column(String(255), nullable=False, unique=True)
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
    
    # Celery task tracking
    task_id = Column(String(255), nullable=True, unique=True, index=True)
    
    # Status tracking
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'running', 'completed', 'failed', 'partial'
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    current_step = Column(String(255), nullable=True)
    
    # Manual trigger tracking
    manual_trigger = Column(Boolean, default=False)
    user_params = Column(JSON, nullable=True)
    
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
    
    def to_dict(self) -> dict:
        """Convert JobRun instance to dictionary"""
        return {
            'id': str(self.id),
            'job_id': str(self.job_id),
            'task_id': self.task_id,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress_percentage': self.progress_percentage,
            'current_step': self.current_step,
            'manual_trigger': self.manual_trigger,
            'user_params': self.user_params,
            'papers_found': self.papers_found,
            'papers_processed': self.papers_processed,
            'papers_skipped': self.papers_skipped,
            'papers_embedded': self.papers_embedded,
            'embedding_errors': self.embedding_errors,
            'vector_db_errors': self.vector_db_errors,
            'error_message': self.error_message,
            'execution_log': self.execution_log
        }
    
    # Relationships
    job = relationship("CronJob", back_populates="job_runs")
    logs = relationship("JobLog", back_populates="job_run", cascade="all, delete-orphan")
    status_history = relationship("JobStatusHistory", back_populates="job_run", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_runs_job_id', 'job_id'),
        Index('idx_job_runs_status', 'status'),
        Index('idx_job_runs_started_at', 'started_at'),
        Index('idx_job_runs_task_id', 'task_id'),
        Index('idx_job_runs_manual_trigger', 'manual_trigger'),
    )

class JobLog(Base):
    """Structured logs for job runs with partitioning support"""
    __tablename__ = 'job_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_run_id = Column(UUID(as_uuid=True), ForeignKey('job_runs.id', ondelete='CASCADE'), nullable=False)
    
    # Log metadata
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    level = Column(String(10), nullable=False)  # 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    logger_name = Column(String(255), nullable=True)
    
    # Log content
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # Additional structured data
    
    # Context information
    step = Column(String(255), nullable=True)  # Current execution step
    paper_id = Column(String(255), nullable=True)  # Related paper if applicable
    error_code = Column(String(50), nullable=True)
    
    # Performance metrics
    duration_ms = Column(Integer, nullable=True)  # Duration of the operation in milliseconds
    
    # Relationships
    job_run = relationship("JobRun", back_populates="logs")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_job_logs_job_run_id', 'job_run_id'),
        Index('idx_job_logs_timestamp', 'timestamp'),
        Index('idx_job_logs_level', 'level'),
        Index('idx_job_logs_step', 'step'),
        Index('idx_job_logs_paper_id', 'paper_id'),
        # Composite index for common queries
        Index('idx_job_logs_job_run_level', 'job_run_id', 'level'),
        Index('idx_job_logs_job_run_timestamp', 'job_run_id', 'timestamp'),
    )

class JobStatusHistory(Base):
    """Status change history for job runs"""
    __tablename__ = 'job_status_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_run_id = Column(UUID(as_uuid=True), ForeignKey('job_runs.id', ondelete='CASCADE'), nullable=False)
    
    # Status information
    from_status = Column(String(20), nullable=True)
    to_status = Column(String(20), nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    
    # Context
    reason = Column(Text, nullable=True)  # Reason for status change
    details = Column(JSON, nullable=True)  # Additional context
    
    # Relationships
    job_run = relationship("JobRun", back_populates="status_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_status_history_job_run_id', 'job_run_id'),
        Index('idx_job_status_history_timestamp', 'timestamp'),
        Index('idx_job_status_history_to_status', 'to_status'),
    )

class JobMetrics(Base):
    """Real-time metrics for job runs"""
    __tablename__ = 'job_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_run_id = Column(UUID(as_uuid=True), ForeignKey('job_runs.id', ondelete='CASCADE'), nullable=False)
    
    # Metric data
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    metric_name = Column(String(100), nullable=False)  # 'papers_processed', 'embedding_errors', etc.
    metric_value = Column(Integer, nullable=False)
    metric_type = Column(String(20), default='counter')  # 'counter', 'gauge', 'histogram'
    
    # Additional context
    labels = Column(JSON, nullable=True)  # Key-value pairs for metric dimensions
    
    # Relationships
    job_run = relationship("JobRun")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_metrics_job_run_id', 'job_run_id'),
        Index('idx_job_metrics_timestamp', 'timestamp'),
        Index('idx_job_metrics_name', 'metric_name'),
        Index('idx_job_metrics_job_run_name', 'job_run_id', 'metric_name'),
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

class AnalysisSession(Base):
    """Analysis session tracking for research queries"""
    __tablename__ = 'analysis_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Session metadata
    query = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default='started')  # 'started', 'in_progress', 'completed', 'failed'
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(255), nullable=True)
    
    # Request parameters
    max_papers = Column(Integer, default=20)
    similarity_threshold = Column(String(10), default='0.5')  # Store as string to avoid float precision issues
    enable_arxiv_fallback = Column(Boolean, default=True)
    selected_agents = Column(ARRAY(String), nullable=True)
    
    # Results
    papers_found = Column(Integer, default=0)
    papers_data = Column(JSON, nullable=True)  # Store paper metadata
    agent_insights = Column(JSON, nullable=True)  # Store agent responses
    final_results = Column(JSON, nullable=True)  # Store final analysis results
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Session tracking
    client_ip = Column(String(45), nullable=True)  # For tracking unique users
    user_agent = Column(Text, nullable=True)
    
    def to_dict(self) -> dict:
        """Convert AnalysisSession instance to dictionary"""
        return {
            'id': str(self.id),
            'query': self.query,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'max_papers': self.max_papers,
            'similarity_threshold': self.similarity_threshold,
            'enable_arxiv_fallback': self.enable_arxiv_fallback,
            'selected_agents': self.selected_agents,
            'papers_found': self.papers_found,
            'papers_data': self.papers_data,
            'agent_insights': self.agent_insights,
            'final_results': self.final_results,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'client_ip': self.client_ip,
            'user_agent': self.user_agent
        }
    
    # Relationships
    progress_history = relationship("AnalysisProgress", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_sessions_status', 'status'),
        Index('idx_analysis_sessions_started_at', 'started_at'),
        Index('idx_analysis_sessions_client_ip', 'client_ip'),
    )

class AnalysisProgress(Base):
    """Progress history for analysis sessions"""
    __tablename__ = 'analysis_progress'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('analysis_sessions.id', ondelete='CASCADE'), nullable=False)
    
    # Progress data
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    step_name = Column(String(255), nullable=False)
    progress_percentage = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)  # 'running', 'completed', 'error'
    message = Column(Text, nullable=True)
    
    # Context data
    current_papers = Column(JSON, nullable=True)  # Papers found at this step
    agent_insights = Column(JSON, nullable=True)  # Agent insights at this step
    step_duration_ms = Column(Integer, nullable=True)  # Duration of this step
    
    # Relationships
    session = relationship("AnalysisSession", back_populates="progress_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_progress_session_id', 'session_id'),
        Index('idx_analysis_progress_timestamp', 'timestamp'),
        Index('idx_analysis_progress_step', 'step_name'),
    )