"""
Task processing service integration.

Main service class that orchestrates task queue, processors,
and status management for file processing operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .models import ProcessingTask, TaskType, TaskPriority, TaskStatus, EMBEDDING_CONFIG, PARSING_CONFIG, ANALYSIS_CONFIG
from .queue import TaskQueue, QueueStats
from .processors import get_processor, TASK_PROCESSORS
from .status_manager import TaskStatusManager

logger = logging.getLogger(__name__)


class TaskService:
    """
    Main task processing service.
    
    Provides a unified interface for:
    - Task submission and management
    - Real-time status tracking
    - Client notifications
    - Processing coordination
    """
    
    def __init__(
        self,
        max_workers: int = 3,
        max_queue_size: int = 1000,
        task_timeout: int = 300
    ):
        # Initialize task queue
        self.task_queue = TaskQueue(
            max_workers=max_workers,
            max_queue_size=max_queue_size,
            task_timeout=task_timeout
        )
        
        # Initialize status manager
        self.status_manager = TaskStatusManager(self.task_queue)
        
        # Register task processors
        self._register_processors()
        
        # Service state
        self._running = False
        
        logger.info("TaskService initialized")

    async def start(self):
        """Start the task processing service."""
        if self._running:
            logger.warning("TaskService is already running")
            return
        
        try:
            # Start task queue
            await self.task_queue.start()
            
            # Start status monitoring
            await self.status_manager.start_monitoring()
            
            self._running = True
            logger.info("TaskService started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start TaskService: {e}")
            await self.stop()
            raise

    async def stop(self):
        """Stop the task processing service."""
        if not self._running:
            return
        
        logger.info("Stopping TaskService...")
        
        try:
            # Stop status monitoring
            await self.status_manager.stop_monitoring()
            
            # Stop task queue
            await self.task_queue.stop()
            
            self._running = False
            logger.info("TaskService stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping TaskService: {e}")

    async def submit_file_for_processing(
        self,
        file_id: str,
        file_path: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        topic_id: Optional[int] = None,
        user_id: str = "",
        task_types: List[TaskType] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Submit a file for processing with multiple task types.
        
        Returns:
            List[str]: List of task IDs created
        """
        if not self._running:
            raise RuntimeError("TaskService is not running")
        
        if task_types is None:
            task_types = [TaskType.FILE_EMBEDDING]  # Default to embedding
        
        task_ids = []
        
        for task_type in task_types:
            # Get default config for task type
            default_config = self._get_default_config(task_type)
            
            # Merge with custom config if provided
            if custom_config:
                config = {**default_config, **custom_config}
            else:
                config = default_config
            
            # Create processing task
            task = ProcessingTask(
                task_type=task_type,
                priority=priority,
                file_id=file_id,
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                mime_type=mime_type,
                topic_id=topic_id,
                user_id=user_id,
                config=config
            )
            
            # Submit to queue
            success = await self.task_queue.submit_task(task)
            if success:
                task_ids.append(task.task_id)
                logger.info(
                    f"Submitted {task_type.value} task {task.task_id} for file {file_name}"
                )
            else:
                logger.error(f"Failed to submit {task_type.value} task for file {file_name}")
        
        return task_ids

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a specific task."""
        return await self.status_manager.get_task_details(task_id)

    async def get_topic_tasks(
        self,
        topic_id: int,
        status_filter: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get tasks for a specific topic."""
        return await self.status_manager.get_topic_tasks(topic_id, status_filter, limit)

    async def get_processing_summary(self, topic_id: Optional[int] = None) -> Dict[str, Any]:
        """Get processing status summary."""
        return await self.status_manager.get_task_status_summary(topic_id)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or active task."""
        success = await self.task_queue.cancel_task(task_id)
        if success:
            await self.status_manager.update_task_status(task_id, TaskStatus.CANCELLED)
        return success

    async def retry_failed_task(self, task_id: str) -> Optional[str]:
        """Retry a failed task, returns new task ID if successful."""
        task = await self.task_queue.get_task_status(task_id)
        if not task or task.status != TaskStatus.FAILED:
            return None
        
        # Create new task with same parameters
        new_task = ProcessingTask(
            task_type=task.task_type,
            priority=task.priority,
            file_id=task.file_id,
            file_path=task.file_path,
            file_name=task.file_name,
            file_size=task.file_size,
            mime_type=task.mime_type,
            topic_id=task.topic_id,
            user_id=task.user_id,
            config=task.config,
            max_retries=task.max_retries
        )
        
        success = await self.task_queue.submit_task(new_task)
        return new_task.task_id if success else None

    async def subscribe_to_updates(self, client_id: str, topic_id: int, connection=None):
        """Subscribe a client to real-time task updates."""
        await self.status_manager.subscribe_to_topic(client_id, topic_id, connection)

    async def unsubscribe_from_updates(self, client_id: str, topic_id: int):
        """Unsubscribe a client from task updates."""
        await self.status_manager.unsubscribe_from_topic(client_id, topic_id)

    async def get_queue_stats(self) -> QueueStats:
        """Get current queue statistics."""
        return await self.task_queue.get_stats()

    async def pause_processing(self):
        """Pause task processing."""
        await self.task_queue.pause()

    async def resume_processing(self):
        """Resume task processing."""
        await self.task_queue.resume()

    def _register_processors(self):
        """Register task processors with the queue."""
        for task_type, processor_class in TASK_PROCESSORS.items():
            processor = processor_class()
            self.task_queue.register_handler(task_type, self._create_processor_handler(processor))
            logger.info(f"Registered processor for {task_type.value}")

    def _create_processor_handler(self, processor):
        """Create a handler function that wraps processor with status updates."""
        async def handler(task: ProcessingTask):
            # Update status to processing
            await self.status_manager.update_task_status(
                task.task_id,
                TaskStatus.PROCESSING,
                {"current_operation": "开始处理", "percentage": 0}
            )
            
            try:
                # Process the task
                result = await processor.process(task)
                
                # Update progress during processing (processor should call this)
                # This is handled by the processor itself via progress updates
                
                # Task completed successfully
                await self.status_manager.update_task_status(
                    task.task_id,
                    TaskStatus.COMPLETED,
                    {"current_operation": "处理完成", "percentage": 100}
                )
                
                return result
                
            except Exception as e:
                # Task failed
                await self.status_manager.update_task_status(
                    task.task_id,
                    TaskStatus.FAILED,
                    {"current_operation": f"处理失败: {str(e)}", "percentage": 0}
                )
                raise
        
        return handler

    def _get_default_config(self, task_type: TaskType) -> Dict[str, Any]:
        """Get default configuration for a task type."""
        config_map = {
            TaskType.FILE_EMBEDDING: EMBEDDING_CONFIG,
            TaskType.DOCUMENT_PARSING: PARSING_CONFIG,
            TaskType.CONTENT_ANALYSIS: ANALYSIS_CONFIG
        }
        return config_map.get(task_type, {}).copy()


# Global task service instance
_task_service: Optional[TaskService] = None


async def get_task_service() -> TaskService:
    """Get the global task service instance."""
    global _task_service
    
    if _task_service is None:
        _task_service = TaskService()
        await _task_service.start()
    
    return _task_service


async def shutdown_task_service():
    """Shutdown the global task service."""
    global _task_service
    
    if _task_service:
        await _task_service.stop()
        _task_service = None


# Convenience functions for common operations

async def process_file_embedding(
    file_id: str,
    file_path: str,
    file_name: str,
    file_size: int,
    mime_type: str,
    topic_id: Optional[int] = None,
    user_id: str = "",
    priority: TaskPriority = TaskPriority.NORMAL,
    custom_config: Optional[Dict[str, Any]] = None
) -> str:
    """
    Convenience function to submit a file for embedding processing.
    
    Returns:
        str: Task ID
    """
    service = await get_task_service()
    task_ids = await service.submit_file_for_processing(
        file_id=file_id,
        file_path=file_path,
        file_name=file_name,
        file_size=file_size,
        mime_type=mime_type,
        topic_id=topic_id,
        user_id=user_id,
        task_types=[TaskType.FILE_EMBEDDING],
        priority=priority,
        custom_config=custom_config
    )
    return task_ids[0] if task_ids else ""


async def process_file_complete(
    file_id: str,
    file_path: str,
    file_name: str,
    file_size: int,
    mime_type: str,
    topic_id: Optional[int] = None,
    user_id: str = "",
    priority: TaskPriority = TaskPriority.NORMAL
) -> List[str]:
    """
    Convenience function to submit a file for complete processing
    (embedding + parsing + analysis).
    
    Returns:
        List[str]: List of task IDs
    """
    service = await get_task_service()
    return await service.submit_file_for_processing(
        file_id=file_id,
        file_path=file_path,
        file_name=file_name,
        file_size=file_size,
        mime_type=mime_type,
        topic_id=topic_id,
        user_id=user_id,
        task_types=[
            TaskType.DOCUMENT_PARSING,
            TaskType.FILE_EMBEDDING,
            TaskType.CONTENT_ANALYSIS
        ],
        priority=priority
    )