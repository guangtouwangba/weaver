"""
Task status management and real-time updates.

Provides task status tracking, real-time notifications,
and database persistence for processing tasks.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Callable, Any
from datetime import datetime, timedelta
import json
from dataclasses import asdict
from enum import Enum

from .models import ProcessingTask, TaskStatus, TaskType
from .queue import TaskQueue

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification channels for status updates."""
    WEBSOCKET = "websocket"
    WEBHOOK = "webhook"
    DATABASE = "database"
    REDIS = "redis"
    SSE = "server_sent_events"


class TaskStatusManager:
    """
    Manages task status tracking and real-time notifications.
    
    Features:
    - Real-time status updates via WebSocket/SSE
    - Database persistence of task states
    - Status change notifications
    - Task history and analytics
    - Client subscription management
    """
    
    def __init__(self, task_queue: TaskQueue):
        self.task_queue = task_queue
        
        # Client connections for real-time updates
        self._websocket_clients: Dict[str, Any] = {}
        self._sse_clients: Dict[str, Any] = {}
        self._topic_subscribers: Dict[int, Set[str]] = {}  # topic_id -> set of client_ids
        
        # Status change listeners
        self._status_listeners: List[Callable] = []
        self._notification_channels: Dict[NotificationChannel, bool] = {
            NotificationChannel.WEBSOCKET: True,
            NotificationChannel.DATABASE: True,
            NotificationChannel.SSE: True,
            NotificationChannel.REDIS: False,
            NotificationChannel.WEBHOOK: False
        }
        
        # Task history and metrics
        self._task_history: Dict[str, List[Dict[str, Any]]] = {}
        self._status_change_log: List[Dict[str, Any]] = []
        
        # Background monitoring task
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info("TaskStatusManager initialized")

    async def start_monitoring(self):
        """Start background task monitoring."""
        if self._running:
            return
            
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Task status monitoring started")

    async def stop_monitoring(self):
        """Stop background task monitoring."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Task status monitoring stopped")

    async def subscribe_to_topic(self, client_id: str, topic_id: int, connection=None):
        """Subscribe a client to task updates for a specific topic."""
        if topic_id not in self._topic_subscribers:
            self._topic_subscribers[topic_id] = set()
        
        self._topic_subscribers[topic_id].add(client_id)
        
        # Store connection for real-time updates
        if connection:
            if hasattr(connection, 'send_text'):  # WebSocket
                self._websocket_clients[client_id] = connection
            else:  # SSE or other
                self._sse_clients[client_id] = connection
        
        logger.info(f"Client {client_id} subscribed to topic {topic_id}")

    async def unsubscribe_from_topic(self, client_id: str, topic_id: int):
        """Unsubscribe a client from topic updates."""
        if topic_id in self._topic_subscribers:
            self._topic_subscribers[topic_id].discard(client_id)
            if not self._topic_subscribers[topic_id]:
                del self._topic_subscribers[topic_id]
        
        # Remove client connections
        self._websocket_clients.pop(client_id, None)
        self._sse_clients.pop(client_id, None)
        
        logger.info(f"Client {client_id} unsubscribed from topic {topic_id}")

    async def get_task_status_summary(self, topic_id: Optional[int] = None) -> Dict[str, Any]:
        """Get task status summary for a topic or all tasks."""
        stats = await self.task_queue.get_stats()
        
        # Get recent task history
        recent_tasks = await self._get_recent_tasks(topic_id, hours=24)
        
        # Calculate status distribution
        status_distribution = {}
        for task in recent_tasks:
            status = task.get('status', 'unknown')
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        return {
            "queue_stats": {
                "pending": stats.pending_tasks,
                "processing": stats.processing_tasks,
                "completed": stats.completed_tasks,
                "failed": stats.failed_tasks,
                "queue_length": stats.queue_length,
                "active_workers": stats.active_workers,
                "average_processing_time": stats.average_processing_time
            },
            "topic_id": topic_id,
            "recent_tasks": {
                "total": len(recent_tasks),
                "last_24_hours": len(recent_tasks),
                "status_distribution": status_distribution
            },
            "last_updated": datetime.now().isoformat()
        }

    async def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific task."""
        task = await self.task_queue.get_task_status(task_id)
        if not task:
            return None
        
        # Get task history
        history = self._task_history.get(task_id, [])
        
        # Convert task to dict and add history
        task_dict = task.to_dict()
        task_dict['status_history'] = history
        task_dict['total_status_changes'] = len(history)
        
        return task_dict

    async def get_topic_tasks(self, topic_id: int, status_filter: Optional[TaskStatus] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get tasks for a specific topic with optional status filtering."""
        # In a real implementation, this would query the database
        # For now, we'll simulate getting tasks from the queue and completed tasks
        
        all_tasks = []
        
        # Get active tasks
        queue_stats = await self.task_queue.get_stats()
        # This is simplified - in reality you'd query the database
        
        # Mock some tasks for demonstration
        mock_tasks = [
            {
                "task_id": f"task_{topic_id}_1",
                "task_type": TaskType.FILE_EMBEDDING.value,
                "status": TaskStatus.PROCESSING.value,
                "file_name": "document1.pdf",
                "progress": {"percentage": 45.0, "current_operation": "生成向量嵌入"},
                "created_at": datetime.now().isoformat()
            },
            {
                "task_id": f"task_{topic_id}_2",
                "task_type": TaskType.DOCUMENT_PARSING.value,
                "status": TaskStatus.COMPLETED.value,
                "file_name": "document2.docx",
                "progress": {"percentage": 100.0, "current_operation": "完成"},
                "created_at": (datetime.now() - timedelta(minutes=10)).isoformat()
            }
        ]
        
        # Apply status filter
        if status_filter:
            mock_tasks = [t for t in mock_tasks if t['status'] == status_filter.value]
        
        return mock_tasks[:limit]

    async def update_task_status(self, task_id: str, status: TaskStatus, progress_data: Optional[Dict[str, Any]] = None):
        """Update task status and notify subscribers."""
        # Get current task
        task = await self.task_queue.get_task_status(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for status update")
            return
        
        # Record status change
        previous_status = task.status
        status_change = {
            "task_id": task_id,
            "previous_status": previous_status.value if previous_status else None,
            "new_status": status.value,
            "timestamp": datetime.now().isoformat(),
            "progress_data": progress_data
        }
        
        # Add to task history
        if task_id not in self._task_history:
            self._task_history[task_id] = []
        self._task_history[task_id].append(status_change)
        
        # Add to global change log (keep last 1000 entries)
        self._status_change_log.append(status_change)
        if len(self._status_change_log) > 1000:
            self._status_change_log = self._status_change_log[-1000:]
        
        # Update task progress if provided
        if progress_data:
            if 'percentage' in progress_data:
                task.progress.percentage = progress_data['percentage']
            if 'current_operation' in progress_data:
                task.progress.current_operation = progress_data['current_operation']
            if 'current_step' in progress_data:
                task.progress.current_step = progress_data['current_step']
        
        # Notify subscribers
        await self._notify_status_change(task, status_change)
        
        logger.info(f"Task {task_id} status updated: {previous_status} -> {status}")

    async def _notify_status_change(self, task: ProcessingTask, status_change: Dict[str, Any]):
        """Notify all relevant subscribers about status change."""
        topic_id = task.topic_id
        if not topic_id:
            return
        
        # Get subscribers for this topic
        subscribers = self._topic_subscribers.get(topic_id, set())
        if not subscribers:
            return
        
        # Prepare notification message
        notification = {
            "type": "task_status_update",
            "task_id": task.task_id,
            "topic_id": topic_id,
            "status": status_change["new_status"],
            "previous_status": status_change["previous_status"],
            "progress": {
                "percentage": task.progress.percentage,
                "current_operation": task.progress.current_operation,
                "current_step": task.progress.current_step,
                "total_steps": task.progress.total_steps
            },
            "file_name": task.file_name,
            "task_type": task.task_type.value,
            "timestamp": status_change["timestamp"]
        }
        
        # Send WebSocket notifications
        if self._notification_channels[NotificationChannel.WEBSOCKET]:
            await self._send_websocket_notifications(subscribers, notification)
        
        # Send SSE notifications
        if self._notification_channels[NotificationChannel.SSE]:
            await self._send_sse_notifications(subscribers, notification)
        
        # Database persistence
        if self._notification_channels[NotificationChannel.DATABASE]:
            await self._persist_status_change(status_change)

    async def _send_websocket_notifications(self, subscribers: Set[str], notification: Dict[str, Any]):
        """Send notifications via WebSocket."""
        message = json.dumps(notification)
        
        for client_id in subscribers:
            websocket = self._websocket_clients.get(client_id)
            if websocket:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket notification to {client_id}: {e}")
                    # Remove dead connection
                    self._websocket_clients.pop(client_id, None)

    async def _send_sse_notifications(self, subscribers: Set[str], notification: Dict[str, Any]):
        """Send notifications via Server-Sent Events."""
        data = json.dumps(notification)
        
        for client_id in subscribers:
            sse_connection = self._sse_clients.get(client_id)
            if sse_connection:
                try:
                    # Format as SSE
                    sse_message = f"event: task_update\ndata: {data}\n\n"
                    await sse_connection.send(sse_message)
                except Exception as e:
                    logger.warning(f"Failed to send SSE notification to {client_id}: {e}")
                    # Remove dead connection
                    self._sse_clients.pop(client_id, None)

    async def _persist_status_change(self, status_change: Dict[str, Any]):
        """Persist status change to database."""
        # In real implementation, save to database
        # For now, just log
        logger.info(f"Persisting status change: {status_change}")

    async def _get_recent_tasks(self, topic_id: Optional[int] = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent tasks from the specified time period."""
        # In real implementation, query database
        # For now, return mock data
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_tasks = []
        
        # Filter task history based on time and topic
        for task_id, history in self._task_history.items():
            if history:
                latest_change = history[-1]
                change_time = datetime.fromisoformat(latest_change['timestamp'])
                
                if change_time >= cutoff_time:
                    # Get task details
                    task = await self.task_queue.get_task_status(task_id)
                    if task and (topic_id is None or task.topic_id == topic_id):
                        recent_tasks.append(task.to_dict())
        
        return recent_tasks

    async def _monitor_loop(self):
        """Background monitoring loop for automatic status updates."""
        while self._running:
            try:
                # Check for status changes that need notification
                # In a real implementation, this might poll the database
                # or listen to queue events
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
                # Example: Check for long-running tasks that might need updates
                queue_stats = await self.task_queue.get_stats()
                
                # Broadcast queue statistics to all connected clients
                if self._websocket_clients or self._sse_clients:
                    stats_update = {
                        "type": "queue_stats_update",
                        "stats": {
                            "pending": queue_stats.pending_tasks,
                            "processing": queue_stats.processing_tasks,
                            "completed": queue_stats.completed_tasks,
                            "failed": queue_stats.failed_tasks,
                            "active_workers": queue_stats.active_workers
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Send to all connected clients
                    all_subscribers = set()
                    for topic_subscribers in self._topic_subscribers.values():
                        all_subscribers.update(topic_subscribers)
                    
                    if all_subscribers:
                        await self._send_websocket_notifications(all_subscribers, stats_update)
                        await self._send_sse_notifications(all_subscribers, stats_update)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in status monitoring loop: {e}")
                await asyncio.sleep(10)  # Wait longer on error

    def add_status_listener(self, listener: Callable):
        """Add a listener for status change events."""
        self._status_listeners.append(listener)

    def remove_status_listener(self, listener: Callable):
        """Remove a status change listener."""
        if listener in self._status_listeners:
            self._status_listeners.remove(listener)

    async def get_status_change_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent status change log."""
        return self._status_change_log[-limit:] if self._status_change_log else []

    async def cleanup_old_data(self, days: int = 7):
        """Clean up old task history and logs."""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Clean task history
        for task_id in list(self._task_history.keys()):
            history = self._task_history[task_id]
            if history:
                last_change = datetime.fromisoformat(history[-1]['timestamp'])
                if last_change < cutoff_time:
                    del self._task_history[task_id]
        
        # Clean status change log
        self._status_change_log = [
            change for change in self._status_change_log
            if datetime.fromisoformat(change['timestamp']) >= cutoff_time
        ]
        
        logger.info(f"Cleaned up task data older than {days} days")