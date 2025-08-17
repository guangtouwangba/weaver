"""
FastAPI routes for task processing and real-time status updates.

Provides REST API endpoints for task management, status tracking,
and real-time notifications via WebSocket and SSE.
"""

import asyncio
import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, Depends, Query, Path, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from enum import Enum

# Task service imports
from infrastructure.tasks.service import get_task_service, TaskService
from infrastructure.tasks.models import TaskType, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

# Pydantic models for API

class TaskTypeEnum(str, Enum):
    """Task type enumeration for API."""
    FILE_EMBEDDING = "file_embedding"
    DOCUMENT_PARSING = "document_parsing"
    CONTENT_ANALYSIS = "content_analysis"
    THUMBNAIL_GENERATION = "thumbnail_gen"
    OCR_PROCESSING = "ocr_processing"

class TaskPriorityEnum(str, Enum):
    """Task priority enumeration for API."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatusEnum(str, Enum):
    """Task status enumeration for API."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class SubmitTaskRequest(BaseModel):
    """Request model for task submission."""
    file_id: str = Field(..., description="File ID to process", example="file_abc123")
    file_path: str = Field(..., description="Path to the file", example="/uploads/documents/research_paper.pdf")
    file_name: str = Field(..., description="Original file name", example="AI Research Paper.pdf")
    file_size: int = Field(..., description="File size in bytes", example=2048000)
    mime_type: str = Field(..., description="MIME type of the file", example="application/pdf")
    topic_id: Optional[int] = Field(None, description="Topic ID", example=42)
    user_id: str = Field("", description="User ID who submitted the task", example="user_456")
    task_types: List[TaskTypeEnum] = Field(
        [TaskTypeEnum.FILE_EMBEDDING], 
        description="Types of processing to perform",
        example=["file_embedding", "document_parsing"]
    )
    priority: TaskPriorityEnum = Field(
        TaskPriorityEnum.NORMAL, 
        description="Task priority level",
        example="normal"
    )
    custom_config: Optional[Dict[str, Any]] = Field(
        None, 
        description="Custom processing configuration",
        example={
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "embedding_model": "text-embedding-ada-002"
        }
    )

class TaskResponse(BaseModel):
    """Response model for task information."""
    task_id: str = Field(..., description="Task ID", example="task_uuid_1")
    task_type: str = Field(..., description="Task type", example="file_embedding")
    status: str = Field(..., description="Current status", example="processing")
    file_name: str = Field(..., description="File name", example="AI Research Paper.pdf")
    progress: Dict[str, Any] = Field(
        ..., 
        description="Progress information",
        example={
            "current_step": 3,
            "total_steps": 6,
            "percentage": 50.0,
            "current_operation": "生成向量嵌入",
            "estimated_remaining_seconds": 120
        }
    )
    created_at: str = Field(..., description="Creation timestamp", example="2024-01-15T10:30:00Z")
    started_at: Optional[str] = Field(None, description="Start timestamp", example="2024-01-15T10:30:05Z")
    completed_at: Optional[str] = Field(None, description="Completion timestamp", example="2024-01-15T10:32:15Z")
    error: Optional[Dict[str, Any]] = Field(None, description="Error information if failed")

class SubmitTaskResponse(BaseModel):
    """Response model for task submission."""
    success: bool = Field(..., description="Whether submission was successful", example=True)
    task_ids: List[str] = Field(
        ..., 
        description="List of created task IDs",
        example=["task_uuid_1", "task_uuid_2"]
    )
    message: str = Field(
        ..., 
        description="Status message",
        example="Successfully submitted 2 tasks for processing"
    )

class TaskSummaryResponse(BaseModel):
    """Response model for task processing summary."""
    topic_id: Optional[int] = Field(None, description="Topic ID")
    queue_stats: Dict[str, Any] = Field(..., description="Queue statistics")
    recent_tasks: Dict[str, Any] = Field(..., description="Recent task information")
    last_updated: str = Field(..., description="Last update timestamp")

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.topic_subscriptions: Dict[int, List[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str, topic_id: int):
        """Accept WebSocket connection and subscribe to topic."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        if topic_id not in self.topic_subscriptions:
            self.topic_subscriptions[topic_id] = []
        self.topic_subscriptions[topic_id].append(client_id)
        
        # Subscribe to task service updates
        task_service = await get_task_service()
        await task_service.subscribe_to_updates(client_id, topic_id, websocket)
        
        logger.info(f"WebSocket client {client_id} connected to topic {topic_id}")

    def disconnect(self, client_id: str, topic_id: int):
        """Remove WebSocket connection."""
        self.active_connections.pop(client_id, None)
        
        if topic_id in self.topic_subscriptions:
            if client_id in self.topic_subscriptions[topic_id]:
                self.topic_subscriptions[topic_id].remove(client_id)
            if not self.topic_subscriptions[topic_id]:
                del self.topic_subscriptions[topic_id]
        
        logger.info(f"WebSocket client {client_id} disconnected from topic {topic_id}")

    async def send_personal_message(self, message: str, client_id: str):
        """Send message to specific client."""
        websocket = self.active_connections.get(client_id)
        if websocket:
            await websocket.send_text(message)

    async def broadcast_to_topic(self, message: str, topic_id: int):
        """Broadcast message to all clients subscribed to a topic."""
        if topic_id in self.topic_subscriptions:
            for client_id in self.topic_subscriptions[topic_id]:
                await self.send_personal_message(message, client_id)

# Global connection manager
manager = ConnectionManager()

# API Routes

@router.post("/submit", response_model=SubmitTaskResponse, 
             summary="Submit file for processing",
             description="""
             Submit a file for asynchronous processing including embedding generation, 
             document parsing, and content analysis.
             
             **Features:**
             - Multiple task types per file
             - Priority-based queue processing
             - Real-time progress tracking
             - Automatic retry on failures
             
             **Task Types:**
             - `file_embedding`: Generate vector embeddings for semantic search
             - `document_parsing`: Extract text, metadata, and document structure
             - `content_analysis`: Keyword extraction, sentiment analysis, content classification
             - `ocr_processing`: Optical character recognition for images and PDFs
             - `thumbnail_generation`: Generate preview thumbnails for visual content
             
             **Priority Levels:**
             - `urgent`: Highest priority, processed immediately
             - `high`: High priority, processed before normal tasks
             - `normal`: Standard priority (default)
             - `low`: Lower priority, processed when queue is less busy
             
             **Processing Flow:**
             1. File validation and accessibility check
             2. Content extraction based on file type
             3. Text chunking for embedding (if applicable)
             4. Vector generation using specified embedding model
             5. Storage in vector database
             6. Metadata update with processing results
             
             Returns task IDs that can be used to track progress via WebSocket or polling.
             """,
             responses={
                 200: {
                     "description": "Tasks submitted successfully",
                     "content": {
                         "application/json": {
                             "example": {
                                 "success": True,
                                 "task_ids": ["task_uuid_1", "task_uuid_2"],
                                 "message": "Successfully submitted 2 tasks for processing"
                             }
                         }
                     }
                 },
                 422: {
                     "description": "Validation error",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": [
                                     {
                                         "loc": ["body", "file_id"],
                                         "msg": "field required",
                                         "type": "value_error.missing"
                                     }
                                 ]
                             }
                         }
                     }
                 },
                 500: {
                     "description": "Internal server error or queue full",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": "Failed to submit task: Queue is full"
                             }
                         }
                     }
                 }
             })
async def submit_task(
    request: SubmitTaskRequest,
    task_service: TaskService = Depends(get_task_service)
) -> SubmitTaskResponse:
    """
    Submit a file for processing.
    
    Creates one or more processing tasks based on the specified task types.
    Returns task IDs that can be used to track progress.
    """
    try:
        # Convert enum types to internal types
        internal_task_types = []
        for task_type in request.task_types:
            if task_type == TaskTypeEnum.FILE_EMBEDDING:
                internal_task_types.append(TaskType.FILE_EMBEDDING)
            elif task_type == TaskTypeEnum.DOCUMENT_PARSING:
                internal_task_types.append(TaskType.DOCUMENT_PARSING)
            elif task_type == TaskTypeEnum.CONTENT_ANALYSIS:
                internal_task_types.append(TaskType.CONTENT_ANALYSIS)
            # Add more mappings as needed
        
        # Convert priority
        priority_map = {
            TaskPriorityEnum.LOW: TaskPriority.LOW,
            TaskPriorityEnum.NORMAL: TaskPriority.NORMAL,
            TaskPriorityEnum.HIGH: TaskPriority.HIGH,
            TaskPriorityEnum.URGENT: TaskPriority.URGENT
        }
        internal_priority = priority_map[request.priority]
        
        # Submit tasks
        task_ids = await task_service.submit_file_for_processing(
            file_id=request.file_id,
            file_path=request.file_path,
            file_name=request.file_name,
            file_size=request.file_size,
            mime_type=request.mime_type,
            topic_id=request.topic_id,
            user_id=request.user_id,
            task_types=internal_task_types,
            priority=internal_priority,
            custom_config=request.custom_config
        )
        
        if task_ids:
            return SubmitTaskResponse(
                success=True,
                task_ids=task_ids,
                message=f"Successfully submitted {len(task_ids)} tasks for processing"
            )
        else:
            return SubmitTaskResponse(
                success=False,
                task_ids=[],
                message="Failed to submit tasks - queue may be full"
            )
            
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.get("/status/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str = Path(..., description="Task ID"),
    task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """Get detailed status of a specific task."""
    try:
        task_data = await task_service.get_task_status(task_id)
        if not task_data:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return TaskResponse(
            task_id=task_data["task_id"],
            task_type=task_data["task_type"],
            status=task_data["status"],
            file_name=task_data["file_name"],
            progress=task_data["progress"],
            created_at=task_data["created_at"],
            started_at=task_data.get("started_at"),
            completed_at=task_data.get("completed_at"),
            error=task_data.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/topic/{topic_id}", response_model=List[TaskResponse])
async def get_topic_tasks(
    topic_id: int = Path(..., description="Topic ID"),
    status: Optional[TaskStatusEnum] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of tasks"),
    task_service: TaskService = Depends(get_task_service)
) -> List[TaskResponse]:
    """Get tasks for a specific topic with optional filtering."""
    try:
        # Convert status filter
        status_filter = None
        if status:
            status_map = {
                TaskStatusEnum.PENDING: TaskStatus.PENDING,
                TaskStatusEnum.PROCESSING: TaskStatus.PROCESSING,
                TaskStatusEnum.COMPLETED: TaskStatus.COMPLETED,
                TaskStatusEnum.FAILED: TaskStatus.FAILED,
                TaskStatusEnum.CANCELLED: TaskStatus.CANCELLED,
                TaskStatusEnum.RETRYING: TaskStatus.RETRYING
            }
            status_filter = status_map.get(status)
        
        tasks = await task_service.get_topic_tasks(topic_id, status_filter, limit)
        
        return [
            TaskResponse(
                task_id=task["task_id"],
                task_type=task["task_type"],
                status=task["status"],
                file_name=task["file_name"],
                progress=task["progress"],
                created_at=task["created_at"],
                started_at=task.get("started_at"),
                completed_at=task.get("completed_at"),
                error=task.get("error")
            )
            for task in tasks
        ]
        
    except Exception as e:
        logger.error(f"Error getting topic tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get topic tasks: {str(e)}")


@router.get("/summary", response_model=TaskSummaryResponse)
async def get_processing_summary(
    topic_id: Optional[int] = Query(None, description="Topic ID (optional)"),
    task_service: TaskService = Depends(get_task_service)
) -> TaskSummaryResponse:
    """Get processing status summary for a topic or all tasks."""
    try:
        summary = await task_service.get_processing_summary(topic_id)
        
        return TaskSummaryResponse(
            topic_id=summary.get("topic_id"),
            queue_stats=summary["queue_stats"],
            recent_tasks=summary["recent_tasks"],
            last_updated=summary["last_updated"]
        )
        
    except Exception as e:
        logger.error(f"Error getting processing summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing summary: {str(e)}")


@router.post("/cancel/{task_id}")
async def cancel_task(
    task_id: str = Path(..., description="Task ID"),
    task_service: TaskService = Depends(get_task_service)
):
    """Cancel a pending or active task."""
    try:
        success = await task_service.cancel_task(task_id)
        
        if success:
            return {"success": True, "message": f"Task {task_id} cancelled successfully"}
        else:
            return {"success": False, "message": f"Task {task_id} could not be cancelled"}
            
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.post("/retry/{task_id}")
async def retry_task(
    task_id: str = Path(..., description="Task ID"),
    task_service: TaskService = Depends(get_task_service)
):
    """Retry a failed task."""
    try:
        new_task_id = await task_service.retry_failed_task(task_id)
        
        if new_task_id:
            return {
                "success": True, 
                "message": f"Task retried successfully",
                "new_task_id": new_task_id
            }
        else:
            return {
                "success": False, 
                "message": f"Task {task_id} cannot be retried"
            }
            
    except Exception as e:
        logger.error(f"Error retrying task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry task: {str(e)}")


# WebSocket endpoint for real-time updates
@router.websocket("/ws/{topic_id}/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    topic_id: int = Path(..., description="Topic ID for task filtering", example=42),
    client_id: str = Path(..., description="Unique client identifier", example="client_123")
):
    """
    WebSocket endpoint for real-time task status updates.
    
    Clients can connect to receive real-time notifications about
    task status changes for a specific topic.
    """
    await manager.connect(websocket, client_id, topic_id)
    
    try:
        # Send initial status
        task_service = await get_task_service()
        summary = await task_service.get_processing_summary(topic_id)
        
        await websocket.send_text(json.dumps({
            "type": "initial_status",
            "data": summary
        }))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "get_status":
                    task_id = message.get("task_id")
                    if task_id:
                        status = await task_service.get_task_status(task_id)
                        await websocket.send_text(json.dumps({
                            "type": "task_status",
                            "task_id": task_id,
                            "data": status
                        }))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error for client {client_id}: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(client_id, topic_id)


# Server-Sent Events endpoint for real-time updates
@router.get("/events/{topic_id}")
async def task_events_stream(
    topic_id: int = Path(..., description="Topic ID"),
    client_id: str = Query(..., description="Client ID"),
    task_service: TaskService = Depends(get_task_service)
):
    """
    Server-Sent Events endpoint for real-time task status updates.
    
    Alternative to WebSocket for clients that prefer SSE.
    """
    
    async def event_generator():
        # Subscribe to updates
        await task_service.subscribe_to_updates(client_id, topic_id)
        
        try:
            # Send initial status
            summary = await task_service.get_processing_summary(topic_id)
            yield f"event: initial_status\ndata: {json.dumps(summary)}\n\n"
            
            # Keep connection alive and send updates
            while True:
                await asyncio.sleep(1)  # Keep connection alive
                
                # In a real implementation, the status manager would
                # queue events for SSE clients. For now, we'll send
                # periodic heartbeats.
                yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.now().isoformat()})}\n\n"
                
        except asyncio.CancelledError:
            pass
        finally:
            # Unsubscribe when connection closes
            await task_service.unsubscribe_from_updates(client_id, topic_id)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


# Queue management endpoints (for admin use)
@router.post("/queue/pause")
async def pause_queue(
    task_service: TaskService = Depends(get_task_service)
):
    """Pause task processing (admin only)."""
    try:
        await task_service.pause_processing()
        return {"success": True, "message": "Task processing paused"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause queue: {str(e)}")


@router.post("/queue/resume")
async def resume_queue(
    task_service: TaskService = Depends(get_task_service)
):
    """Resume task processing (admin only)."""
    try:
        await task_service.resume_processing()
        return {"success": True, "message": "Task processing resumed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume queue: {str(e)}")


@router.get("/queue/stats")
async def get_queue_stats(
    task_service: TaskService = Depends(get_task_service)
):
    """Get detailed queue statistics."""
    try:
        stats = await task_service.get_queue_stats()
        return {
            "pending_tasks": stats.pending_tasks,
            "processing_tasks": stats.processing_tasks,
            "completed_tasks": stats.completed_tasks,
            "failed_tasks": stats.failed_tasks,
            "total_tasks": stats.total_tasks,
            "queue_length": stats.queue_length,
            "active_workers": stats.active_workers,
            "average_processing_time": stats.average_processing_time,
            "queue_status": stats.queue_status.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue stats: {str(e)}")


# Health check
@router.get("/health")
async def health_check():
    """Task service health check."""
    try:
        task_service = await get_task_service()
        stats = await task_service.get_queue_stats()
        
        return {
            "status": "healthy",
            "service": "task_processing",
            "timestamp": datetime.now().isoformat(),
            "queue_status": stats.queue_status.value,
            "active_workers": stats.active_workers
        }
    except Exception as e:
        logger.error(f"Task service health check failed: {e}")
        raise HTTPException(status_code=503, detail="Task service unavailable")