"""WebSocket API endpoints for real-time notifications."""

from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

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
