"""WebSocket API endpoints for real-time notifications."""

from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from research_agent.infrastructure.websocket.canvas_notification_service import (
    canvas_notification_service,
)
from research_agent.infrastructure.websocket.notification_service import (
    document_notification_service,
)
from research_agent.shared.utils.logger import logger

router = APIRouter()


@router.websocket("/ws/projects/{project_id}/documents")
async def project_documents_websocket(
    websocket: WebSocket,
    project_id: str,
) -> None:
    """
    WebSocket endpoint for receiving document status updates for a project.

    This endpoint allows clients to subscribe to all document status updates
    for a specific project. Useful for monitoring upload progress and
    processing status of multiple documents.

    Messages sent to client:
    ```json
    {
        "type": "document_status",
        "document_id": "uuid",
        "status": "processing|ready|error",
        "summary": "Document summary (when available)",
        "page_count": 10,
        "graph_status": "processing|ready|error",
        "error_message": "Error details (when status is error)"
    }
    ```
    """
    await document_notification_service.connect(websocket, project_id)

    try:
        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()

            # Handle ping/pong for connection keep-alive
            if data == "ping":
                await websocket.send_text("pong")

            logger.debug(f"[WebSocket] Received from client: {data}")

    except WebSocketDisconnect:
        await document_notification_service.disconnect(websocket, project_id)
    except Exception as e:
        logger.error(f"[WebSocket] Error in project documents websocket: {e}")
        await document_notification_service.disconnect(websocket, project_id)


@router.websocket("/ws/projects/{project_id}/documents/{document_id}")
async def document_status_websocket(
    websocket: WebSocket,
    project_id: str,
    document_id: str,
) -> None:
    """
    WebSocket endpoint for receiving status updates for a specific document.

    This endpoint allows clients to subscribe to status updates for a single
    document. Useful for tracking the processing progress of a specific upload.

    Messages sent to client:
    ```json
    {
        "type": "document_status",
        "document_id": "uuid",
        "status": "processing|ready|error",
        "summary": "Document summary (when available)",
        "page_count": 10,
        "graph_status": "processing|ready|error",
        "error_message": "Error details (when status is error)"
    }
    ```
    """
    await document_notification_service.connect(websocket, project_id, document_id)

    try:
        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()

            # Handle ping/pong for connection keep-alive
            if data == "ping":
                await websocket.send_text("pong")

            logger.debug(f"[WebSocket] Received from client: {data}")

    except WebSocketDisconnect:
        await document_notification_service.disconnect(websocket, project_id, document_id)
    except Exception as e:
        logger.error(f"[WebSocket] Error in document status websocket: {e}")
        await document_notification_service.disconnect(websocket, project_id, document_id)


@router.websocket("/ws/projects/{project_id}/canvas")
async def project_canvas_websocket(
    websocket: WebSocket,
    project_id: str,
) -> None:
    """
    WebSocket endpoint for receiving Canvas/Thinking Path real-time updates.

    This endpoint allows clients to subscribe to canvas updates for a project,
    enabling multi-device synchronization and real-time thinking path generation.

    Messages sent to client:
    ```json
    {
        "type": "node_added|node_updated|node_deleted|edge_added|thinking_path_analyzed|...",
        "timestamp": "2024-01-01T00:00:00.000Z",
        "node_id": "node-xxx",
        "node_data": {...},
        "message_ids": ["msg-1", "msg-2"],
        "analysis_status": "pending|analyzed|error"
    }
    ```

    Thinking Path Analysis Events:
    - `thinking_path_analyzing`: Analysis started for a message
    - `thinking_path_analyzed`: Analysis complete with nodes/edges
    - `thinking_path_error`: Analysis failed

    Client can send:
    - "ping": Server responds with "pong" (keep-alive)
    """
    await canvas_notification_service.connect(websocket, project_id)

    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()

            # Handle ping/pong for connection keep-alive
            if data == "ping":
                await websocket.send_text("pong")

            logger.debug(f"[Canvas WebSocket] Received from client: {data}")

    except WebSocketDisconnect:
        await canvas_notification_service.disconnect(websocket, project_id)
    except Exception as e:
        logger.error(f"[Canvas WebSocket] Error in canvas websocket: {e}")
        await canvas_notification_service.disconnect(websocket, project_id)
