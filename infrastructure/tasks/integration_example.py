"""
Integration example for file processing task system.

Shows how to integrate the task processing system with
existing file upload and management workflows.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Task system imports
from .service import get_task_service, process_file_embedding, process_file_complete
from .models import TaskType, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class FileProcessingIntegration:
    """
    Integration layer between file upload and task processing.
    
    Demonstrates how to connect file uploads to the task processing
    system for automatic embedding and analysis.
    """
    
    def __init__(self):
        self.task_service = None
        self.processing_enabled = True
        
    async def initialize(self):
        """Initialize the integration."""
        self.task_service = await get_task_service()
        logger.info("File processing integration initialized")

    async def on_file_uploaded(
        self,
        file_id: str,
        file_path: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        topic_id: Optional[int] = None,
        user_id: str = "",
        auto_process: bool = True,
        processing_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle file upload completion and trigger processing.
        
        This function should be called when a file upload completes
        to automatically start the embedding and analysis pipeline.
        
        Returns:
            Dict containing task IDs and processing status
        """
        if not auto_process or not self.processing_enabled:
            return {
                "processing_started": False,
                "reason": "Auto-processing disabled",
                "task_ids": []
            }
        
        try:
            # Determine processing tasks based on file type
            task_types = self._determine_task_types(mime_type, processing_config)
            
            # Determine priority based on file characteristics
            priority = self._determine_priority(file_size, topic_id, processing_config)
            
            # Submit for processing
            task_ids = await self.task_service.submit_file_for_processing(
                file_id=file_id,
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                mime_type=mime_type,
                topic_id=topic_id,
                user_id=user_id,
                task_types=task_types,
                priority=priority,
                custom_config=processing_config
            )
            
            logger.info(
                f"Started processing for file {file_name} "
                f"(tasks: {len(task_ids)}, types: {[t.value for t in task_types]})"
            )
            
            return {
                "processing_started": True,
                "task_ids": task_ids,
                "task_types": [t.value for t in task_types],
                "priority": priority.value,
                "estimated_completion": self._estimate_completion_time(task_types, file_size)
            }
            
        except Exception as e:
            logger.error(f"Failed to start processing for file {file_name}: {e}")
            return {
                "processing_started": False,
                "error": str(e),
                "task_ids": []
            }

    async def get_file_processing_status(self, file_id: str) -> Dict[str, Any]:
        """
        Get processing status for all tasks related to a file.
        
        Args:
            file_id: The file ID to check
            
        Returns:
            Dict containing processing status and progress
        """
        try:
            # In a real implementation, you'd query the database to find
            # all tasks associated with this file_id
            # For this example, we'll simulate the response
            
            return {
                "file_id": file_id,
                "overall_status": "processing",
                "progress_percentage": 67.5,
                "tasks": [
                    {
                        "task_id": f"task_{file_id}_embedding",
                        "task_type": "file_embedding",
                        "status": "completed",
                        "progress": 100.0,
                        "completed_at": datetime.now().isoformat()
                    },
                    {
                        "task_id": f"task_{file_id}_parsing",
                        "task_type": "document_parsing",
                        "status": "processing",
                        "progress": 45.0,
                        "current_operation": "提取图片和表格"
                    },
                    {
                        "task_id": f"task_{file_id}_analysis",
                        "task_type": "content_analysis",
                        "status": "pending",
                        "progress": 0.0
                    }
                ],
                "estimated_remaining_time": 120,  # seconds
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing status for file {file_id}: {e}")
            return {
                "file_id": file_id,
                "error": str(e)
            }

    async def on_task_completed(self, task_id: str, result: Dict[str, Any]):
        """
        Handle task completion callback.
        
        This method should be called when a task completes
        to update file metadata and trigger follow-up actions.
        """
        try:
            task_status = await self.task_service.get_task_status(task_id)
            if not task_status:
                logger.warning(f"Task {task_id} not found for completion callback")
                return
            
            file_id = task_status.get("file_id")
            task_type = task_status.get("task_type")
            
            # Update file metadata based on task type
            if task_type == "file_embedding":
                await self._update_file_embedding_metadata(file_id, result)
            elif task_type == "document_parsing":
                await self._update_file_parsing_metadata(file_id, result)
            elif task_type == "content_analysis":
                await self._update_file_analysis_metadata(file_id, result)
            
            # Check if all tasks for this file are complete
            await self._check_file_processing_completion(file_id)
            
            logger.info(f"Processed task completion for {task_id} (type: {task_type})")
            
        except Exception as e:
            logger.error(f"Failed to handle task completion for {task_id}: {e}")

    async def retry_failed_processing(self, file_id: str) -> Dict[str, Any]:
        """
        Retry failed processing tasks for a file.
        
        Args:
            file_id: The file ID to retry processing for
            
        Returns:
            Dict containing retry results
        """
        try:
            # Find failed tasks for this file
            # In a real implementation, query the database
            failed_task_ids = [f"task_{file_id}_embedding"]  # Mock
            
            retry_results = []
            for task_id in failed_task_ids:
                new_task_id = await self.task_service.retry_failed_task(task_id)
                retry_results.append({
                    "original_task_id": task_id,
                    "new_task_id": new_task_id,
                    "retry_successful": new_task_id is not None
                })
            
            successful_retries = [r for r in retry_results if r["retry_successful"]]
            
            return {
                "file_id": file_id,
                "retries_attempted": len(retry_results),
                "retries_successful": len(successful_retries),
                "new_task_ids": [r["new_task_id"] for r in successful_retries if r["new_task_id"]],
                "results": retry_results
            }
            
        except Exception as e:
            logger.error(f"Failed to retry processing for file {file_id}: {e}")
            return {
                "file_id": file_id,
                "error": str(e)
            }

    def _determine_task_types(self, mime_type: str, config: Optional[Dict[str, Any]] = None) -> List[TaskType]:
        """Determine which task types to run based on file type and config."""
        task_types = []
        
        # Always include embedding for searchable content
        if self._is_text_content(mime_type):
            task_types.append(TaskType.FILE_EMBEDDING)
        
        # Include parsing for document types
        if self._is_document_type(mime_type):
            task_types.append(TaskType.DOCUMENT_PARSING)
        
        # Include analysis for text content
        if self._is_text_content(mime_type):
            task_types.append(TaskType.CONTENT_ANALYSIS)
        
        # Include OCR for image/PDF types
        if self._needs_ocr(mime_type):
            task_types.append(TaskType.OCR_PROCESSING)
        
        # Include thumbnail generation for visual content
        if self._is_visual_content(mime_type):
            task_types.append(TaskType.THUMBNAIL_GENERATION)
        
        # Apply config overrides
        if config and "task_types" in config:
            # Allow configuration to override default task types
            config_types = []
            for task_type_str in config["task_types"]:
                try:
                    config_types.append(TaskType(task_type_str))
                except ValueError:
                    logger.warning(f"Unknown task type in config: {task_type_str}")
            
            if config_types:
                task_types = config_types
        
        return task_types or [TaskType.FILE_EMBEDDING]  # Default fallback

    def _determine_priority(self, file_size: int, topic_id: Optional[int], config: Optional[Dict[str, Any]] = None) -> TaskPriority:
        """Determine task priority based on file characteristics."""
        # Check config override
        if config and "priority" in config:
            try:
                return TaskPriority(config["priority"])
            except ValueError:
                logger.warning(f"Invalid priority in config: {config['priority']}")
        
        # Small files get higher priority for faster processing
        if file_size < 1024 * 1024:  # < 1MB
            return TaskPriority.HIGH
        
        # Large files get lower priority to not block the queue
        if file_size > 100 * 1024 * 1024:  # > 100MB
            return TaskPriority.LOW
        
        # Default priority
        return TaskPriority.NORMAL

    def _estimate_completion_time(self, task_types: List[TaskType], file_size: int) -> int:
        """Estimate completion time in seconds."""
        # Base times for different task types (in seconds)
        base_times = {
            TaskType.FILE_EMBEDDING: 30,
            TaskType.DOCUMENT_PARSING: 20,
            TaskType.CONTENT_ANALYSIS: 15,
            TaskType.OCR_PROCESSING: 60,
            TaskType.THUMBNAIL_GENERATION: 10
        }
        
        # Calculate base time
        total_time = sum(base_times.get(task_type, 30) for task_type in task_types)
        
        # Adjust for file size (larger files take longer)
        size_factor = min(file_size / (10 * 1024 * 1024), 5.0)  # Max 5x for very large files
        total_time = int(total_time * (1 + size_factor))
        
        return total_time

    def _is_text_content(self, mime_type: str) -> bool:
        """Check if content is text-based and suitable for embedding."""
        text_types = [
            "text/", "application/pdf", "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        ]
        return any(mime_type.startswith(t) for t in text_types)

    def _is_document_type(self, mime_type: str) -> bool:
        """Check if content is a structured document."""
        doc_types = [
            "application/pdf", "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ]
        return any(mime_type.startswith(t) for t in doc_types)

    def _needs_ocr(self, mime_type: str) -> bool:
        """Check if content might need OCR processing."""
        ocr_types = ["image/", "application/pdf"]
        return any(mime_type.startswith(t) for t in ocr_types)

    def _is_visual_content(self, mime_type: str) -> bool:
        """Check if content is visual and needs thumbnails."""
        visual_types = ["image/", "video/", "application/pdf"]
        return any(mime_type.startswith(t) for t in visual_types)

    async def _update_file_embedding_metadata(self, file_id: str, result: Dict[str, Any]):
        """Update file metadata with embedding results."""
        # In a real implementation, update the database
        logger.info(f"Updating embedding metadata for file {file_id}")

    async def _update_file_parsing_metadata(self, file_id: str, result: Dict[str, Any]):
        """Update file metadata with parsing results."""
        # In a real implementation, update the database
        logger.info(f"Updating parsing metadata for file {file_id}")

    async def _update_file_analysis_metadata(self, file_id: str, result: Dict[str, Any]):
        """Update file metadata with analysis results."""
        # In a real implementation, update the database
        logger.info(f"Updating analysis metadata for file {file_id}")

    async def _check_file_processing_completion(self, file_id: str):
        """Check if all processing tasks for a file are complete."""
        # In a real implementation, check if all tasks are done
        # and trigger any post-processing actions
        logger.info(f"Checking processing completion for file {file_id}")


# Example usage function
async def example_usage():
    """Example of how to use the file processing integration."""
    
    # Initialize the integration
    integration = FileProcessingIntegration()
    await integration.initialize()
    
    # Simulate a file upload
    file_info = {
        "file_id": "file_123",
        "file_path": "/uploads/document.pdf",
        "file_name": "important_document.pdf",
        "file_size": 2 * 1024 * 1024,  # 2MB
        "mime_type": "application/pdf",
        "topic_id": 42,
        "user_id": "user_456"
    }
    
    # Start processing
    result = await integration.on_file_uploaded(**file_info)
    print(f"Processing started: {result}")
    
    # Check status
    status = await integration.get_file_processing_status(file_info["file_id"])
    print(f"Processing status: {status}")
    
    # Simulate task completion
    await integration.on_task_completed(
        result["task_ids"][0] if result["task_ids"] else "mock_task_id",
        {"success": True, "vectors_created": 25}
    )


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())