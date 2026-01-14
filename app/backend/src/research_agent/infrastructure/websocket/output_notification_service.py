"""WebSocket notification service for Output generation real-time updates."""

import asyncio
from datetime import datetime
from typing import Any

from fastapi import WebSocket

from research_agent.domain.agents.base_agent import OutputEvent, OutputEventType
from research_agent.shared.utils.logger import logger


class OutputNotificationService:
    """
    Service for managing WebSocket connections and sending output generation notifications.

    Supports:
    - Real-time mindmap node/edge generation updates
    - Progress updates during generation
    - Token streaming for explain operations
    - Multi-client synchronization

    Uses in-memory connection registry. For horizontal scaling, consider
    using Redis Pub/Sub for cross-instance communication.
    """

    def __init__(self):
        # Map: project_id -> Set[WebSocket]
        self._project_connections: dict[str, set[WebSocket]] = {}
        # Map: task_id -> Set[WebSocket] (for task-specific subscriptions)
        self._task_connections: dict[str, set[WebSocket]] = {}
        # Lock for thread-safe connection management
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        project_id: str,
        task_id: str | None = None,
    ) -> None:
        """
        Register a WebSocket connection for output updates.

        Args:
            websocket: The WebSocket connection
            project_id: Project ID to subscribe to
            task_id: Optional specific task ID to subscribe to
        """
        await websocket.accept()

        async with self._lock:
            # Subscribe to project updates
            if project_id not in self._project_connections:
                self._project_connections[project_id] = set()
            self._project_connections[project_id].add(websocket)

            # Optionally subscribe to specific task
            if task_id:
                if task_id not in self._task_connections:
                    self._task_connections[task_id] = set()
                self._task_connections[task_id].add(websocket)

        logger.info(
            f"[Output WebSocket] Client connected - project_id={project_id}, task_id={task_id}"
        )

    async def disconnect(
        self,
        websocket: WebSocket,
        project_id: str,
        task_id: str | None = None,
    ) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            websocket: The WebSocket connection
            project_id: Project ID to unsubscribe from
            task_id: Optional specific task ID to unsubscribe from
        """
        async with self._lock:
            if project_id in self._project_connections:
                self._project_connections[project_id].discard(websocket)
                if not self._project_connections[project_id]:
                    del self._project_connections[project_id]

            if task_id and task_id in self._task_connections:
                self._task_connections[task_id].discard(websocket)
                if not self._task_connections[task_id]:
                    del self._task_connections[task_id]

        logger.info(
            f"[Output WebSocket] Client disconnected - project_id={project_id}, task_id={task_id}"
        )

    async def _broadcast_to_project(
        self,
        project_id: str,
        message: dict[str, Any],
    ) -> int:
        """
        Broadcast a message to all clients connected to a project.

        Args:
            project_id: Project ID
            message: Message to broadcast

        Returns:
            Number of clients notified
        """
        notified_count = 0

        async with self._lock:
            connections = self._project_connections.get(project_id, set()).copy()

        disconnected: set[WebSocket] = set()
        for websocket in connections:
            try:
                await websocket.send_json(message)
                notified_count += 1
            except Exception as e:
                logger.warning(f"[Output WebSocket] Failed to broadcast: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                if project_id in self._project_connections:
                    for ws in disconnected:
                        self._project_connections[project_id].discard(ws)

        return notified_count

    async def _broadcast_to_task(
        self,
        task_id: str,
        message: dict[str, Any],
    ) -> int:
        """
        Broadcast a message to all clients subscribed to a specific task.

        Args:
            task_id: Task ID
            message: Message to broadcast

        Returns:
            Number of clients notified
        """
        notified_count = 0

        async with self._lock:
            connections = self._task_connections.get(task_id, set()).copy()

        disconnected: set[WebSocket] = set()
        for websocket in connections:
            try:
                await websocket.send_json(message)
                notified_count += 1
            except Exception as e:
                logger.warning(f"[Output WebSocket] Failed to broadcast to task: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                if task_id in self._task_connections:
                    for ws in disconnected:
                        self._task_connections[task_id].discard(ws)

        return notified_count

    async def notify_event(
        self,
        project_id: str,
        task_id: str,
        event: OutputEvent,
    ) -> int:
        """
        Notify clients of an output generation event.

        Args:
            project_id: Project ID
            task_id: Task ID for the generation
            event: The output event to broadcast

        Returns:
            Number of clients notified
        """
        message = {
            "taskId": task_id,
            **event.to_dict(),
        }

        # Log markdown content if present (for debugging)
        if event.type.value == "generation_complete" and event.markdown_content:
            logger.info(
                f"[Output WebSocket] Sending generation_complete with markdownContent "
                f"({len(event.markdown_content)} chars) and documentId={event.document_id}"
            )
            # Log the actual message keys to verify markdownContent is included
            logger.info(f"[Output WebSocket] Message keys: {list(message.keys())}")

        # Broadcast to task-specific subscribers first
        task_count = await self._broadcast_to_task(task_id, message)

        # Then broadcast to project subscribers (excluding task subscribers to avoid duplicates)
        project_count = await self._broadcast_to_project(project_id, message)

        total = max(task_count, project_count)  # Dedupe count since some may be subscribed to both
        logger.debug(
            f"[Output WebSocket] Notified {total} clients - event={event.type.value}, task={task_id}"
        )
        return total

    async def notify_generation_started(
        self,
        project_id: str,
        task_id: str,
        output_type: str,
        message: str = "Generation started",
    ) -> int:
        """Notify that generation has started."""
        event_message = {
            "taskId": task_id,
            "type": OutputEventType.GENERATION_STARTED.value,
            "outputType": output_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        count = await self._broadcast_to_project(project_id, event_message)
        logger.info(f"[Output WebSocket] Generation started - task={task_id}, notified={count}")
        return count

    async def notify_generation_progress(
        self,
        project_id: str,
        task_id: str,
        progress: float,
        message: str | None = None,
    ) -> int:
        """Notify generation progress update."""
        event_message = {
            "taskId": task_id,
            "type": OutputEventType.GENERATION_PROGRESS.value,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return await self._broadcast_to_project(project_id, event_message)

    async def notify_generation_complete(
        self,
        project_id: str,
        task_id: str,
        output_id: str,
        message: str = "Generation complete",
    ) -> int:
        """Notify that generation is complete."""
        event_message = {
            "taskId": task_id,
            "type": OutputEventType.GENERATION_COMPLETE.value,
            "outputId": output_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        count = await self._broadcast_to_project(project_id, event_message)
        logger.info(f"[Output WebSocket] Generation complete - task={task_id}, output={output_id}")
        return count

    async def notify_generation_error(
        self,
        project_id: str,
        task_id: str,
        error_message: str,
    ) -> int:
        """Notify that generation failed."""
        event_message = {
            "taskId": task_id,
            "type": OutputEventType.GENERATION_ERROR.value,
            "errorMessage": error_message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        count = await self._broadcast_to_project(project_id, event_message)
        logger.error(f"[Output WebSocket] Generation error - task={task_id}, error={error_message}")
        return count

    async def notify_node_added(
        self,
        project_id: str,
        task_id: str,
        node_id: str,
        node_data: dict[str, Any],
    ) -> int:
        """Notify that a mindmap node was added."""
        event_message = {
            "taskId": task_id,
            "type": OutputEventType.NODE_ADDED.value,
            "nodeId": node_id,
            "nodeData": node_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return await self._broadcast_to_project(project_id, event_message)

    async def notify_edge_added(
        self,
        project_id: str,
        task_id: str,
        edge_id: str,
        edge_data: dict[str, Any],
    ) -> int:
        """Notify that a mindmap edge was added."""
        event_message = {
            "taskId": task_id,
            "type": OutputEventType.EDGE_ADDED.value,
            "edgeId": edge_id,
            "edgeData": edge_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return await self._broadcast_to_project(project_id, event_message)

    async def notify_token(
        self,
        project_id: str,
        task_id: str,
        token: str,
    ) -> int:
        """Notify a token for streaming text (e.g., explain)."""
        event_message = {
            "taskId": task_id,
            "type": OutputEventType.TOKEN.value,
            "token": token,
            "timestamp": datetime.utcnow().isoformat(),
        }
        # Only send to task-specific subscribers for tokens (high frequency)
        return await self._broadcast_to_task(task_id, event_message)

    def cleanup_task(self, task_id: str) -> None:
        """
        Clean up task-specific subscriptions.
        Call this when a task is complete or cancelled.
        """
        if task_id in self._task_connections:
            del self._task_connections[task_id]
            logger.debug(f"[Output WebSocket] Cleaned up task subscriptions: {task_id}")

    @property
    def connection_count(self) -> int:
        """Get total number of active project connections."""
        all_connections: set[WebSocket] = set()
        for conns in self._project_connections.values():
            all_connections.update(conns)
        return len(all_connections)

    def get_project_connection_count(self, project_id: str) -> int:
        """Get number of connections for a specific project."""
        return len(self._project_connections.get(project_id, set()))


# Singleton instance
output_notification_service = OutputNotificationService()








