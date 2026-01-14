"""WebSocket notification service for document processing status updates."""

import asyncio
from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket

from research_agent.shared.utils.logger import logger


@dataclass
class DocumentStatusUpdate:
    """Document status update payload."""

    document_id: str
    status: str  # "pending" | "processing" | "ready" | "error"
    summary: str | None = None
    page_count: int | None = None
    graph_status: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "type": "document_status",
            "document_id": self.document_id,
            "status": self.status,
        }
        if self.summary is not None:
            result["summary"] = self.summary
        if self.page_count is not None:
            result["page_count"] = self.page_count
        if self.graph_status is not None:
            result["graph_status"] = self.graph_status
        if self.error_message is not None:
            result["error_message"] = self.error_message
        return result


class DocumentNotificationService:
    """
    Service for managing WebSocket connections and sending document status notifications.

    Uses a simple in-memory connection registry. For horizontal scaling, consider
    using Redis Pub/Sub or similar for cross-instance communication.
    """

    def __init__(self):
        # Map: project_id -> Set[WebSocket]
        self._project_connections: dict[str, set[WebSocket]] = {}
        # Map: document_id -> Set[WebSocket]
        self._document_connections: dict[str, set[WebSocket]] = {}
        # Lock for thread-safe connection management
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        project_id: str,
        document_id: str | None = None,
    ) -> None:
        """
        Register a WebSocket connection for a project (and optionally a specific document).

        Args:
            websocket: The WebSocket connection
            project_id: Project ID to subscribe to
            document_id: Optional specific document ID to subscribe to
        """
        await websocket.accept()

        async with self._lock:
            # Register for project-level updates
            if project_id not in self._project_connections:
                self._project_connections[project_id] = set()
            self._project_connections[project_id].add(websocket)

            # Register for document-specific updates
            if document_id:
                if document_id not in self._document_connections:
                    self._document_connections[document_id] = set()
                self._document_connections[document_id].add(websocket)

        logger.info(
            f"[WebSocket] Client connected - project_id={project_id}, document_id={document_id}"
        )

    async def disconnect(
        self,
        websocket: WebSocket,
        project_id: str,
        document_id: str | None = None,
    ) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            websocket: The WebSocket connection
            project_id: Project ID to unsubscribe from
            document_id: Optional specific document ID to unsubscribe from
        """
        async with self._lock:
            # Remove from project connections
            if project_id in self._project_connections:
                self._project_connections[project_id].discard(websocket)
                if not self._project_connections[project_id]:
                    del self._project_connections[project_id]

            # Remove from document connections
            if document_id and document_id in self._document_connections:
                self._document_connections[document_id].discard(websocket)
                if not self._document_connections[document_id]:
                    del self._document_connections[document_id]

        logger.info(
            f"[WebSocket] Client disconnected - project_id={project_id}, document_id={document_id}"
        )

    async def notify_document_status(
        self,
        project_id: str,
        document_id: str,
        status: str,
        summary: str | None = None,
        page_count: int | None = None,
        graph_status: str | None = None,
        error_message: str | None = None,
    ) -> int:
        """
        Send document status update to all connected clients.

        Args:
            project_id: Project ID
            document_id: Document ID
            status: New document status
            summary: Document summary (if available)
            page_count: Number of pages (if available)
            graph_status: Graph extraction status (if available)
            error_message: Error message (if status is "error")

        Returns:
            Number of clients notified
        """
        update = DocumentStatusUpdate(
            document_id=document_id,
            status=status,
            summary=summary,
            page_count=page_count,
            graph_status=graph_status,
            error_message=error_message,
        )

        message = update.to_dict()
        notified_count = 0

        # Collect all relevant connections
        connections_to_notify: set[WebSocket] = set()

        async with self._lock:
            # Get project-level subscribers
            if project_id in self._project_connections:
                connections_to_notify.update(self._project_connections[project_id])

            # Get document-specific subscribers
            if document_id in self._document_connections:
                connections_to_notify.update(self._document_connections[document_id])

        # Send notifications
        disconnected: set[WebSocket] = set()
        for websocket in connections_to_notify:
            try:
                await websocket.send_json(message)
                notified_count += 1
            except Exception as e:
                logger.warning(f"[WebSocket] Failed to send notification: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    for conns in self._project_connections.values():
                        conns.discard(ws)
                    for conns in self._document_connections.values():
                        conns.discard(ws)

        logger.info(
            f"[WebSocket] Notified {notified_count} clients - "
            f"document_id={document_id}, status={status}"
        )

        return notified_count

    async def broadcast_to_project(
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
                logger.warning(f"[WebSocket] Failed to broadcast: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                if project_id in self._project_connections:
                    for ws in disconnected:
                        self._project_connections[project_id].discard(ws)

        return notified_count

    @property
    def connection_count(self) -> int:
        """Get total number of active connections."""
        all_connections: set[WebSocket] = set()
        for conns in self._project_connections.values():
            all_connections.update(conns)
        return len(all_connections)

    async def notify_thumbnail_ready(
        self,
        project_id: str,
        document_id: str,
        thumbnail_url: str,
    ) -> int:
        """
        Send thumbnail ready notification to all connected clients.

        Args:
            project_id: Project ID
            document_id: Document ID
            thumbnail_url: URL to the generated thumbnail

        Returns:
            Number of clients notified
        """
        message = {
            "type": "thumbnail_ready",
            "document_id": document_id,
            "thumbnail_url": thumbnail_url,
            "thumbnail_status": "ready",
        }

        # Collect all relevant connections
        connections_to_notify: set[WebSocket] = set()

        async with self._lock:
            if project_id in self._project_connections:
                connections_to_notify.update(self._project_connections[project_id])
            if document_id in self._document_connections:
                connections_to_notify.update(self._document_connections[document_id])

        notified_count = 0
        for websocket in connections_to_notify:
            try:
                await websocket.send_json(message)
                notified_count += 1
            except Exception as e:
                logger.warning(f"[WebSocket] Failed to send thumbnail notification: {e}")

        logger.info(
            f"[WebSocket] Thumbnail ready notification sent - "
            f"document_id={document_id}, notified={notified_count}"
        )

        return notified_count


# Singleton instance
document_notification_service = DocumentNotificationService()
