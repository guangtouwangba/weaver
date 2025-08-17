"""
Task processing models and enums.

Defines the core data structures for file processing tasks,
including status tracking, progress monitoring, and error handling.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class TaskStatus(str, Enum):
    """Task processing status."""
    PENDING = "pending"           # 等待处理
    PROCESSING = "processing"     # 处理中
    COMPLETED = "completed"       # 处理成功
    FAILED = "failed"            # 处理失败
    CANCELLED = "cancelled"       # 已取消
    RETRYING = "retrying"        # 重试中


class TaskType(str, Enum):
    """Task processing types."""
    FILE_EMBEDDING = "file_embedding"        # 文件向量化
    DOCUMENT_PARSING = "document_parsing"    # 文档解析
    CONTENT_ANALYSIS = "content_analysis"    # 内容分析
    THUMBNAIL_GENERATION = "thumbnail_gen"   # 缩略图生成
    OCR_PROCESSING = "ocr_processing"        # OCR识别


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class TaskProgress:
    """Task progress tracking."""
    current_step: int = 0
    total_steps: int = 1
    percentage: float = 0.0
    current_operation: str = ""
    estimated_remaining_seconds: Optional[int] = None
    
    def update(self, step: int, operation: str = "", total: Optional[int] = None):
        """Update progress."""
        self.current_step = step
        if total:
            self.total_steps = total
        self.current_operation = operation
        self.percentage = min((step / self.total_steps) * 100, 100.0)


@dataclass
class TaskError:
    """Task error information."""
    error_code: str
    error_message: str
    error_details: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    is_retryable: bool = True
    occurred_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskResult:
    """Task processing result."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    artifacts: List[str] = field(default_factory=list)  # Generated files/URLs
    metrics: Optional[Dict[str, Any]] = None
    processing_time_seconds: Optional[float] = None


@dataclass
class ProcessingTask:
    """File processing task definition."""
    
    # Basic identification
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType = TaskType.FILE_EMBEDDING
    priority: TaskPriority = TaskPriority.NORMAL
    
    # File information
    file_id: str = ""
    file_path: str = ""
    file_name: str = ""
    file_size: int = 0
    mime_type: str = ""
    
    # Context information
    topic_id: Optional[int] = None
    user_id: str = ""
    
    # Processing configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Status tracking
    status: TaskStatus = TaskStatus.PENDING
    progress: TaskProgress = field(default_factory=TaskProgress)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results and errors
    result: Optional[TaskResult] = None
    error: Optional[TaskError] = None
    
    # Retry configuration
    max_retries: int = 3
    retry_count: int = 0
    retry_delay_seconds: int = 60
    
    def start_processing(self):
        """Mark task as started."""
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.now()
        
    def complete_successfully(self, result: TaskResult):
        """Mark task as completed successfully."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        self.progress.percentage = 100.0
        
    def fail_with_error(self, error: TaskError):
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
        
    def should_retry(self) -> bool:
        """Check if task should be retried."""
        return (
            self.status == TaskStatus.FAILED and
            self.retry_count < self.max_retries and
            self.error and
            self.error.is_retryable
        )
        
    def prepare_retry(self):
        """Prepare task for retry."""
        if self.should_retry():
            self.retry_count += 1
            self.status = TaskStatus.RETRYING
            self.completed_at = None
            if self.error:
                self.error.retry_count = self.retry_count
                
    @property
    def processing_duration(self) -> Optional[float]:
        """Get processing duration in seconds."""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
        
    @property
    def is_terminal_status(self) -> bool:
        """Check if task is in terminal status."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "priority": self.priority.value,
            "file_id": self.file_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "topic_id": self.topic_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "progress": {
                "current_step": self.progress.current_step,
                "total_steps": self.progress.total_steps,
                "percentage": self.progress.percentage,
                "current_operation": self.progress.current_operation,
                "estimated_remaining_seconds": self.progress.estimated_remaining_seconds
            },
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "processing_duration": self.processing_duration,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "result": self.result.__dict__ if self.result else None,
            "error": self.error.__dict__ if self.error else None
        }


# Pre-defined processing configurations
EMBEDDING_CONFIG = {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "embedding_model": "text-embedding-ada-002",
    "vector_dimension": 1536,
    "batch_size": 10
}

PARSING_CONFIG = {
    "extract_images": True,
    "extract_tables": True,
    "ocr_enabled": True,
    "language": "auto"
}

ANALYSIS_CONFIG = {
    "extract_keywords": True,
    "generate_summary": True,
    "detect_language": True,
    "classify_content": True
}