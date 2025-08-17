"""
Task queue management for file processing.

Handles task queuing, priority management, and worker coordination
for file embedding and processing operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

from .models import ProcessingTask, TaskStatus, TaskType, TaskPriority

logger = logging.getLogger(__name__)


class QueueStatus(str, Enum):
    """Queue status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    DRAINING = "draining"
    STOPPED = "stopped"


@dataclass
class QueueStats:
    """Queue statistics."""
    pending_tasks: int = 0
    processing_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_tasks: int = 0
    average_processing_time: float = 0.0
    queue_length: int = 0
    active_workers: int = 0
    queue_status: QueueStatus = QueueStatus.ACTIVE


class TaskQueue:
    """
    Async task queue for file processing operations.
    
    Features:
    - Priority-based task scheduling
    - Concurrent worker management
    - Task retry and error handling
    - Real-time status tracking
    - Queue statistics and monitoring
    """
    
    def __init__(
        self,
        max_workers: int = 3,
        max_queue_size: int = 1000,
        default_retry_delay: int = 60,
        task_timeout: int = 300
    ):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.default_retry_delay = default_retry_delay
        self.task_timeout = task_timeout
        
        # Queue data structures
        self._queues: Dict[TaskPriority, asyncio.Queue] = {
            TaskPriority.URGENT: asyncio.Queue(),
            TaskPriority.HIGH: asyncio.Queue(),
            TaskPriority.NORMAL: asyncio.Queue(),
            TaskPriority.LOW: asyncio.Queue()
        }
        
        # Task tracking
        self._active_tasks: Dict[str, ProcessingTask] = {}
        self._completed_tasks: Dict[str, ProcessingTask] = {}
        self._failed_tasks: Dict[str, ProcessingTask] = {}
        self._task_handlers: Dict[TaskType, Callable] = {}
        
        # Worker management
        self._workers: List[asyncio.Task] = []
        self._worker_status: Dict[str, Dict[str, Any]] = {}
        self._status = QueueStatus.ACTIVE
        
        # Statistics
        self._stats = QueueStats()
        self._processing_times: List[float] = []
        
        # Events
        self._shutdown_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        
        logger.info(f"TaskQueue initialized with {max_workers} workers")

    async def start(self):
        """Start the task queue and workers."""
        if self._status != QueueStatus.STOPPED:
            logger.warning("Queue is already running")
            return
            
        self._status = QueueStatus.ACTIVE
        self._shutdown_event.clear()
        self._pause_event.clear()
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker_id = f"worker-{i}"
            worker_task = asyncio.create_task(
                self._worker_loop(worker_id),
                name=worker_id
            )
            self._workers.append(worker_task)
            self._worker_status[worker_id] = {
                "status": "idle",
                "current_task": None,
                "processed_count": 0,
                "start_time": datetime.now()
            }
        
        logger.info(f"Started {len(self._workers)} workers")

    async def stop(self, timeout: int = 30):
        """Stop the task queue gracefully."""
        logger.info("Stopping task queue...")
        
        self._status = QueueStatus.DRAINING
        self._shutdown_event.set()
        
        # Wait for workers to finish current tasks
        if self._workers:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._workers, return_exceptions=True),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning("Workers did not finish within timeout, cancelling...")
                for worker in self._workers:
                    worker.cancel()
        
        self._workers.clear()
        self._worker_status.clear()
        self._status = QueueStatus.STOPPED
        
        logger.info("Task queue stopped")

    async def pause(self):
        """Pause task processing."""
        self._status = QueueStatus.PAUSED
        self._pause_event.set()
        logger.info("Task queue paused")

    async def resume(self):
        """Resume task processing."""
        self._status = QueueStatus.ACTIVE
        self._pause_event.clear()
        logger.info("Task queue resumed")

    def register_handler(self, task_type: TaskType, handler: Callable):
        """Register a task handler for a specific task type."""
        self._task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")

    async def submit_task(self, task: ProcessingTask) -> bool:
        """
        Submit a task to the queue.
        
        Returns:
            bool: True if task was queued successfully
        """
        if self._status == QueueStatus.STOPPED:
            logger.error("Cannot submit task: queue is stopped")
            return False
            
        # Check queue size limits
        total_queued = sum(q.qsize() for q in self._queues.values())
        if total_queued >= self.max_queue_size:
            logger.error(f"Queue is full ({total_queued}/{self.max_queue_size})")
            return False
        
        # Add to appropriate priority queue
        priority_queue = self._queues[task.priority]
        
        try:
            priority_queue.put_nowait(task)
            self._stats.total_tasks += 1
            self._stats.pending_tasks += 1
            
            logger.info(
                f"Task {task.task_id} queued with priority {task.priority} "
                f"(type: {task.task_type})"
            )
            return True
            
        except asyncio.QueueFull:
            logger.error(f"Priority queue {task.priority} is full")
            return False

    async def get_task_status(self, task_id: str) -> Optional[ProcessingTask]:
        """Get the current status of a task."""
        # Check active tasks
        if task_id in self._active_tasks:
            return self._active_tasks[task_id]
        
        # Check completed tasks
        if task_id in self._completed_tasks:
            return self._completed_tasks[task_id]
        
        # Check failed tasks
        if task_id in self._failed_tasks:
            return self._failed_tasks[task_id]
        
        return None

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or active task."""
        # Check if task is active
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            
            # Move to failed tasks (cancelled tasks are treated as failed)
            self._failed_tasks[task_id] = task
            del self._active_tasks[task_id]
            
            self._stats.processing_tasks -= 1
            self._stats.failed_tasks += 1
            
            logger.info(f"Cancelled active task {task_id}")
            return True
        
        # Check pending queues
        for priority_queue in self._queues.values():
            temp_tasks = []
            cancelled = False
            
            # Drain queue and check each task
            while not priority_queue.empty():
                try:
                    task = priority_queue.get_nowait()
                    if task.task_id == task_id:
                        task.status = TaskStatus.CANCELLED
                        task.completed_at = datetime.now()
                        self._failed_tasks[task_id] = task
                        
                        self._stats.pending_tasks -= 1
                        self._stats.failed_tasks += 1
                        
                        cancelled = True
                        logger.info(f"Cancelled pending task {task_id}")
                    else:
                        temp_tasks.append(task)
                except asyncio.QueueEmpty:
                    break
            
            # Put back non-cancelled tasks
            for task in temp_tasks:
                priority_queue.put_nowait(task)
            
            if cancelled:
                return True
        
        logger.warning(f"Task {task_id} not found for cancellation")
        return False

    async def get_stats(self) -> QueueStats:
        """Get current queue statistics."""
        # Update queue length
        self._stats.queue_length = sum(q.qsize() for q in self._queues.values())
        self._stats.active_workers = len([
            w for w in self._worker_status.values() 
            if w["status"] == "processing"
        ])
        self._stats.queue_status = self._status
        
        # Calculate average processing time
        if self._processing_times:
            self._stats.average_processing_time = sum(self._processing_times) / len(self._processing_times)
        
        return self._stats

    async def _get_next_task(self) -> Optional[ProcessingTask]:
        """Get the next task from queues (priority order)."""
        # Check queues in priority order
        for priority in [TaskPriority.URGENT, TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]:
            queue = self._queues[priority]
            if not queue.empty():
                try:
                    return queue.get_nowait()
                except asyncio.QueueEmpty:
                    continue
        return None

    async def _worker_loop(self, worker_id: str):
        """Main worker loop for processing tasks."""
        logger.info(f"Worker {worker_id} started")
        
        while not self._shutdown_event.is_set():
            try:
                # Check if paused
                if self._status == QueueStatus.PAUSED:
                    await asyncio.sleep(1)
                    continue
                
                # Get next task
                task = await self._get_next_task()
                if not task:
                    # No tasks available, wait briefly
                    await asyncio.sleep(0.1)
                    continue
                
                # Process the task
                await self._process_task(worker_id, task)
                
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker {worker_id} stopped")

    async def _process_task(self, worker_id: str, task: ProcessingTask):
        """Process a single task."""
        # Update worker status
        self._worker_status[worker_id].update({
            "status": "processing",
            "current_task": task.task_id
        })
        
        # Move task to active
        self._active_tasks[task.task_id] = task
        self._stats.pending_tasks -= 1
        self._stats.processing_tasks += 1
        
        # Start processing
        task.start_processing()
        start_time = datetime.now()
        
        logger.info(f"Worker {worker_id} processing task {task.task_id} (type: {task.task_type})")
        
        try:
            # Get handler for task type
            handler = self._task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task.task_type}")
            
            # Execute task with timeout
            result = await asyncio.wait_for(
                handler(task),
                timeout=self.task_timeout
            )
            
            # Task completed successfully
            processing_time = (datetime.now() - start_time).total_seconds()
            self._processing_times.append(processing_time)
            
            # Keep only last 100 processing times for average calculation
            if len(self._processing_times) > 100:
                self._processing_times = self._processing_times[-100:]
            
            task.complete_successfully(result)
            
            # Move to completed
            self._completed_tasks[task.task_id] = task
            del self._active_tasks[task.task_id]
            
            self._stats.processing_tasks -= 1
            self._stats.completed_tasks += 1
            
            logger.info(
                f"Task {task.task_id} completed successfully in {processing_time:.2f}s"
            )
            
        except asyncio.TimeoutError:
            # Task timeout
            from .models import TaskError
            error = TaskError(
                error_code="TIMEOUT",
                error_message=f"Task timed out after {self.task_timeout} seconds",
                is_retryable=True
            )
            task.fail_with_error(error)
            await self._handle_failed_task(task)
            
        except Exception as e:
            # Task failed
            from .models import TaskError
            error = TaskError(
                error_code="PROCESSING_ERROR",
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
                is_retryable=True
            )
            task.fail_with_error(error)
            await self._handle_failed_task(task)
            
        finally:
            # Update worker status
            self._worker_status[worker_id].update({
                "status": "idle",
                "current_task": None,
                "processed_count": self._worker_status[worker_id]["processed_count"] + 1
            })

    async def _handle_failed_task(self, task: ProcessingTask):
        """Handle a failed task (retry or move to failed)."""
        # Move from active to failed
        if task.task_id in self._active_tasks:
            del self._active_tasks[task.task_id]
            self._stats.processing_tasks -= 1
        
        # Check if should retry
        if task.should_retry():
            task.prepare_retry()
            
            # Schedule retry after delay
            asyncio.create_task(self._schedule_retry(task))
            
            logger.info(
                f"Task {task.task_id} scheduled for retry {task.retry_count}/{task.max_retries}"
            )
        else:
            # No more retries, mark as failed
            self._failed_tasks[task.task_id] = task
            self._stats.failed_tasks += 1
            
            logger.error(
                f"Task {task.task_id} failed permanently after {task.retry_count} retries"
            )

    async def _schedule_retry(self, task: ProcessingTask):
        """Schedule a task retry after delay."""
        await asyncio.sleep(task.retry_delay_seconds)
        
        if self._status not in [QueueStatus.STOPPED, QueueStatus.DRAINING]:
            await self.submit_task(task)