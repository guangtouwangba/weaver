"""WebSocket API endpoints for real-time notifications."""

from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from research_agent.api.auth.websocket_auth import verify_project_access, verify_websocket_token
from research_agent.infrastructure.websocket.canvas_notification_service import (
    canvas_notification_service,
)
from research_agent.infrastructure.websocket.notification_service import (
    document_notification_service,
)
from research_agent.infrastructure.websocket.output_notification_service import (
    output_notification_service,
)
from research_agent.shared.utils.logger import logger

router = APIRouter()


@router.websocket("/ws/projects/{project_id}/documents")
async def project_documents_websocket(
    websocket: WebSocket,
    project_id: str,
    token: Optional[str] = None,
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
    try:
        user_id, is_anonymous = await verify_websocket_token(websocket, token)
        await verify_project_access(project_id, user_id, is_anonymous)
    except Exception:
        return  # Connection was rejected

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
    token: Optional[str] = None,
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
    try:
        user_id, is_anonymous = await verify_websocket_token(websocket, token)
        await verify_project_access(project_id, user_id, is_anonymous)
    except Exception:
        return

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
    token: Optional[str] = None,
) -> None:
    """
    WebSocket endpoint for receiving Canvas real-time updates.

    This endpoint allows clients to subscribe to canvas updates for a project,
    enabling multi-device synchronization.

    Messages sent to client:
    ```json
    {
        "type": "node_added|node_updated|node_deleted|edge_added|canvas_batch_update",
        "timestamp": "2024-01-01T00:00:00.000Z",
        "node_id": "node-xxx",
        "node_data": {...},
        "message_ids": ["msg-1", "msg-2"]
    }
    ```

    Client can send:
    - "ping": Server responds with "pong" (keep-alive)
    """
    try:
        user_id, is_anonymous = await verify_websocket_token(websocket, token)
        await verify_project_access(project_id, user_id, is_anonymous)
    except Exception:
        return

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


@router.websocket("/ws/projects/{project_id}/outputs")
async def project_outputs_websocket(
    websocket: WebSocket,
    project_id: str,
    task_id: Optional[str] = None,
    token: Optional[str] = None,
) -> None:
    """
    WebSocket endpoint for receiving output generation updates.

    Connect to receive real-time updates about:
    - Generation progress
    - New nodes being added (for mindmaps)
    - Completion or error status

    Query params:
        task_id: Optional specific task to subscribe to

    Messages sent to client:
    ```json
    {
        "taskId": "uuid",
        "type": "generation_started|node_added|generation_complete|...",
        "timestamp": "ISO timestamp",
        "nodeData": {...},  // for node events
        "progress": 0.5,    // for progress events
        "errorMessage": "..." // for error events
    }
    ```

    Output Event Types:
    - `generation_started`: Generation task started
    - `generation_progress`: Progress update (0.0 - 1.0)
    - `generation_complete`: Generation finished successfully
    - `generation_error`: Generation failed
    - `node_generating`: A node is being generated
    - `node_added`: A new node was added
    - `edge_added`: A new edge was added
    - `level_complete`: A level of the mindmap is complete
    - `token`: A token for streaming text (explain operation)

    Client can send:
    - "ping": Server responds with "pong" (keep-alive)
    """
    try:
        user_id, is_anonymous = await verify_websocket_token(websocket, token)
        await verify_project_access(project_id, user_id, is_anonymous)
    except Exception:
        return

    await output_notification_service.connect(websocket, project_id, task_id)

    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()

            # Handle ping/pong for connection keep-alive
            if data == "ping":
                await websocket.send_text("pong")

            logger.debug(f"[Output WebSocket] Received from client: {data}")

    except WebSocketDisconnect:
        await output_notification_service.disconnect(websocket, project_id, task_id)
    except Exception as e:
        logger.error(f"[Output WebSocket] Error in output websocket: {e}")
        await output_notification_service.disconnect(websocket, project_id, task_id)
