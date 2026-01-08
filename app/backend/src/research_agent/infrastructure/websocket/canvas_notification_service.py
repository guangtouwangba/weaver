"""WebSocket notification service for Canvas real-time updates."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket

from research_agent.shared.utils.logger import logger


class CanvasEventType(str, Enum):
    """Canvas event types for WebSocket notifications."""

    # Node events
    NODE_ADDED = "node_added"
    NODE_UPDATED = "node_updated"
    NODE_DELETED = "node_deleted"

    # Edge events
    EDGE_ADDED = "edge_added"
    EDGE_DELETED = "edge_deleted"

    # Section events
    SECTION_ADDED = "section_added"
    SECTION_UPDATED = "section_updated"
    SECTION_DELETED = "section_deleted"

    # Batch update
    CANVAS_BATCH_UPDATE = "canvas_batch_update"


@dataclass
class CanvasNodeUpdate:
    """Canvas node update payload."""

    node_id: str
    event_type: CanvasEventType
    node_data: Optional[Dict[str, Any]] = None
    message_ids: Optional[List[str]] = None  # Linked chat message IDs
    analysis_status: Optional[str] = None  # "pending" | "analyzed" | "error"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "type": self.event_type.value,
            "node_id": self.node_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if self.node_data is not None:
            result["node_data"] = self.node_data
        if self.message_ids is not None:
            result["message_ids"] = self.message_ids
        if self.analysis_status is not None:
            result["analysis_status"] = self.analysis_status
        return result


@dataclass
class CanvasEdgeUpdate:
    """Canvas edge update payload."""

    edge_id: str
    event_type: CanvasEventType
    source_id: str
    target_id: str
    edge_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "type": self.event_type.value,
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if self.edge_data is not None:
            result["edge_data"] = self.edge_data
        return result


class CanvasNotificationService:
    """
    Service for managing WebSocket connections and sending Canvas notifications.

    Supports:
    - Real-time node/edge updates
    - Multi-client synchronization (multiple browser tabs/devices)

    Uses in-memory connection registry. For horizontal scaling, consider
    using Redis Pub/Sub for cross-instance communication.
    """

    def __init__(self):
        # Map: project_id -> Set[WebSocket]
        self._project_connections: Dict[str, Set[WebSocket]] = {}
        # Lock for thread-safe connection management
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        project_id: str,
    ) -> None:
        """
        Register a WebSocket connection for canvas updates.

        Args:
            websocket: The WebSocket connection
            project_id: Project ID to subscribe to
        """
        await websocket.accept()

        async with self._lock:
            if project_id not in self._project_connections:
                self._project_connections[project_id] = set()
            self._project_connections[project_id].add(websocket)

        logger.info(f"[Canvas WebSocket] Client connected - project_id={project_id}")

    async def disconnect(
        self,
        websocket: WebSocket,
        project_id: str,
    ) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            websocket: The WebSocket connection
            project_id: Project ID to unsubscribe from
        """
        async with self._lock:
            if project_id in self._project_connections:
                self._project_connections[project_id].discard(websocket)
                if not self._project_connections[project_id]:
                    del self._project_connections[project_id]

        logger.info(f"[Canvas WebSocket] Client disconnected - project_id={project_id}")

    async def _broadcast(
        self,
        project_id: str,
        message: Dict[str, Any],
        exclude_websocket: Optional[WebSocket] = None,
    ) -> int:
        """
        Broadcast a message to all clients connected to a project.

        Args:
            project_id: Project ID
            message: Message to broadcast
            exclude_websocket: Optional websocket to exclude (e.g., the sender)

        Returns:
            Number of clients notified
        """
        notified_count = 0

        async with self._lock:
            connections = self._project_connections.get(project_id, set()).copy()

        disconnected: Set[WebSocket] = set()
        for websocket in connections:
            if exclude_websocket and websocket == exclude_websocket:
                continue
            try:
                await websocket.send_json(message)
                notified_count += 1
            except Exception as e:
                logger.warning(f"[Canvas WebSocket] Failed to broadcast: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                if project_id in self._project_connections:
                    for ws in disconnected:
                        self._project_connections[project_id].discard(ws)

        return notified_count

    async def notify_node_added(
        self,
        project_id: str,
        node_id: str,
        node_data: Dict[str, Any],
        message_ids: Optional[List[str]] = None,
        analysis_status: str = "pending",
        exclude_websocket: Optional[WebSocket] = None,
    ) -> int:
        """
        Notify clients that a new node was added.

        Args:
            project_id: Project ID
            node_id: New node ID
            node_data: Node data
            message_ids: Associated chat message IDs
            analysis_status: Current analysis status
            exclude_websocket: Optional websocket to exclude

        Returns:
            Number of clients notified
        """
        update = CanvasNodeUpdate(
            node_id=node_id,
            event_type=CanvasEventType.NODE_ADDED,
            node_data=node_data,
            message_ids=message_ids,
            analysis_status=analysis_status,
        )

        count = await self._broadcast(project_id, update.to_dict(), exclude_websocket)
        logger.info(f"[Canvas WebSocket] Notified {count} clients - node_added: {node_id}")
        return count

    async def notify_node_updated(
        self,
        project_id: str,
        node_id: str,
        node_data: Dict[str, Any],
        message_ids: Optional[List[str]] = None,
        analysis_status: Optional[str] = None,
        exclude_websocket: Optional[WebSocket] = None,
    ) -> int:
        """
        Notify clients that a node was updated.
        """
        update = CanvasNodeUpdate(
            node_id=node_id,
            event_type=CanvasEventType.NODE_UPDATED,
            node_data=node_data,
            message_ids=message_ids,
            analysis_status=analysis_status,
        )

        count = await self._broadcast(project_id, update.to_dict(), exclude_websocket)
        logger.info(f"[Canvas WebSocket] Notified {count} clients - node_updated: {node_id}")
        return count

    async def notify_node_deleted(
        self,
        project_id: str,
        node_id: str,
        exclude_websocket: Optional[WebSocket] = None,
    ) -> int:
        """
        Notify clients that a node was deleted.
        """
        update = CanvasNodeUpdate(
            node_id=node_id,
            event_type=CanvasEventType.NODE_DELETED,
        )

        count = await self._broadcast(project_id, update.to_dict(), exclude_websocket)
        logger.info(f"[Canvas WebSocket] Notified {count} clients - node_deleted: {node_id}")
        return count

    async def notify_edge_added(
        self,
        project_id: str,
        edge_id: str,
        source_id: str,
        target_id: str,
        edge_data: Optional[Dict[str, Any]] = None,
        exclude_websocket: Optional[WebSocket] = None,
    ) -> int:
        """
        Notify clients that a new edge was added.
        """
        update = CanvasEdgeUpdate(
            edge_id=edge_id,
            event_type=CanvasEventType.EDGE_ADDED,
            source_id=source_id,
            target_id=target_id,
            edge_data=edge_data,
        )

        count = await self._broadcast(project_id, update.to_dict(), exclude_websocket)
        logger.info(f"[Canvas WebSocket] Notified {count} clients - edge_added: {edge_id}")
        return count

    async def notify_batch_update(
        self,
        project_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        sections: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """
        Send a batch update with multiple nodes/edges.
        Useful for initial sync or large updates.
        """
        message = {
            "type": CanvasEventType.CANVAS_BATCH_UPDATE.value,
            "timestamp": datetime.utcnow().isoformat(),
            "nodes": nodes,
            "edges": edges,
        }
        if sections:
            message["sections"] = sections

        count = await self._broadcast(project_id, message)
        logger.info(
            f"[Canvas WebSocket] Batch update - {count} clients, "
            f"{len(nodes)} nodes, {len(edges)} edges"
        )
        return count

    @property
    def connection_count(self) -> int:
        """Get total number of active connections."""
        all_connections: Set[WebSocket] = set()
        for conns in self._project_connections.values():
            all_connections.update(conns)
        return len(all_connections)

    def get_project_connection_count(self, project_id: str) -> int:
        """Get number of connections for a specific project."""
        return len(self._project_connections.get(project_id, set()))


# Singleton instance
canvas_notification_service = CanvasNotificationService()
