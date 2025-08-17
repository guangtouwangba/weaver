"""
Task processing infrastructure for file embedding and analysis.

This module provides a complete task processing system including:
- Task queue management with priority scheduling
- Real-time status tracking and notifications
- File processing workflows (embedding, parsing, analysis)
- Error handling and retry mechanisms
- WebSocket and SSE support for real-time updates

Main components:
- TaskService: Main service orchestrating all task operations
- TaskQueue: Priority-based async task queue with worker management
- TaskStatusManager: Real-time status tracking and notifications
- Processors: Specialized handlers for different task types

Usage:
    from infrastructure.tasks import get_task_service, process_file_embedding
    
    # Get the task service
    service = await get_task_service()
    
    # Submit a file for embedding
    task_id = await process_file_embedding(
        file_id="file123",
        file_path="/path/to/file.pdf",
        file_name="document.pdf",
        file_size=1024000,
        mime_type="application/pdf",
        topic_id=42
    )
    
    # Check task status
    status = await service.get_task_status(task_id)
"""

from .models import (
    ProcessingTask,
    TaskStatus,
    TaskType,
    TaskPriority,
    TaskProgress,
    TaskError,
    TaskResult,
    EMBEDDING_CONFIG,
    PARSING_CONFIG,
    ANALYSIS_CONFIG
)

from .queue import TaskQueue, QueueStats, QueueStatus
from .status_manager import TaskStatusManager, NotificationChannel
from .processors import BaseProcessor, get_processor
from .service import (
    TaskService,
    get_task_service,
    shutdown_task_service,
    process_file_embedding,
    process_file_complete
)

__all__ = [
    # Models
    "ProcessingTask",
    "TaskStatus",
    "TaskType",
    "TaskPriority",
    "TaskProgress",
    "TaskError",
    "TaskResult",
    "EMBEDDING_CONFIG",
    "PARSING_CONFIG",
    "ANALYSIS_CONFIG",
    
    # Queue management
    "TaskQueue",
    "QueueStats",
    "QueueStatus",
    
    # Status management
    "TaskStatusManager",
    "NotificationChannel",
    
    # Processors
    "BaseProcessor",
    "get_processor",
    
    # Main service
    "TaskService",
    "get_task_service",
    "shutdown_task_service",
    
    # Convenience functions
    "process_file_embedding",
    "process_file_complete"
]