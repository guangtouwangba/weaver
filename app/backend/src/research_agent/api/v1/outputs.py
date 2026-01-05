"""API endpoints for output generation (mindmap, summary, etc.)."""

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db
from research_agent.application.dto.output import (
    ExpandNodeRequest,
    ExplainNodeRequest,
    GenerateOutputRequest,
    GenerateOutputResponse,
    NodeActionResponse,
    OutputListResponse,
    OutputResponse,
    SynthesizeNodesRequest,
    UpdateOutputRequest,
)
from research_agent.application.services.output_generation_service import (
    output_generation_service,
)
from research_agent.shared.utils.logger import logger

router = APIRouter()


# =============================================================================
# REST API Endpoints
# =============================================================================


@router.post(
    "/projects/{project_id}/outputs/generate",
    response_model=GenerateOutputResponse,
    status_code=202,  # Accepted - async operation
)
async def generate_output(
    project_id: UUID,
    request: GenerateOutputRequest,
    session: AsyncSession = Depends(get_db),
) -> GenerateOutputResponse:
    """
    Start generating an output (mindmap, summary, etc.).

    This endpoint starts an async generation task and returns immediately.
    Subscribe to the WebSocket channel to receive real-time updates.

    Returns:
        - task_id: Use to track progress
        - output_id: ID of the output being generated
        - websocket_channel: WebSocket path to subscribe to
    """
    logger.info(
        f"[Outputs API] Generate request: project={project_id}, "
        f"type={request.output_type}, docs={request.document_ids}"
    )

    # Validate document_ids is not empty, except for 'custom' type with node_data
    # Custom type can work with canvas node_data instead of documents
    is_custom_with_node_data = (
        request.output_type == "custom" and
        request.options and
        (request.options.get("node_data") or request.options.get("mode"))
    )
    
    if not request.document_ids and not is_custom_with_node_data:
        raise HTTPException(
            status_code=400,
            detail="At least one document ID is required for output generation"
        )

    try:
        result = await output_generation_service.start_generation(
            project_id=project_id,
            output_type=request.output_type,
            document_ids=request.document_ids,
            title=request.title,
            options=request.options or {},
            session=session,
        )

        return GenerateOutputResponse(
            task_id=result["task_id"],
            output_id=result["output_id"],
            status="generating",
            websocket_channel=f"/ws/projects/{project_id}/outputs?task_id={result['task_id']}",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Outputs API] Generate failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start generation")


@router.get(
    "/projects/{project_id}/outputs",
    response_model=OutputListResponse,
)
async def list_outputs(
    project_id: UUID,
    output_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
) -> OutputListResponse:
    """
    List outputs for a project.

    Args:
        project_id: Project ID
        output_type: Optional filter by type (mindmap, summary, etc.)
        limit: Maximum number of results
        offset: Pagination offset
    """
    outputs, total = await output_generation_service.list_outputs(
        project_id=project_id,
        output_type=output_type,
        limit=limit,
        offset=offset,
        session=session,
    )

    return OutputListResponse(
        outputs=[
            OutputResponse(
                id=o.id,
                project_id=o.project_id,
                output_type=o.output_type.value,
                document_ids=o.document_ids,
                status=o.status.value,
                title=o.title,
                data=o.data,
                error_message=o.error_message,
                created_at=o.created_at,
                updated_at=o.updated_at,
            )
            for o in outputs
        ],
        total=total,
    )


@router.get(
    "/projects/{project_id}/outputs/{output_id}",
    response_model=OutputResponse,
)
async def get_output(
    project_id: UUID,
    output_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> OutputResponse:
    """Get a specific output by ID."""
    output = await output_generation_service.get_output(
        project_id=project_id,
        output_id=output_id,
        session=session,
    )

    if not output:
        raise HTTPException(status_code=404, detail="Output not found")

    return OutputResponse(
        id=output.id,
        project_id=output.project_id,
        output_type=output.output_type.value,
        document_ids=output.document_ids,
        status=output.status.value,
        title=output.title,
        data=output.data,
        error_message=output.error_message,
        created_at=output.created_at,
        updated_at=output.updated_at,
    )


@router.delete(
    "/projects/{project_id}/outputs/{output_id}",
    status_code=204,
)
async def delete_output(
    project_id: UUID,
    output_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete an output."""
    success = await output_generation_service.delete_output(
        project_id=project_id,
        output_id=output_id,
        session=session,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Output not found")


@router.patch(
    "/projects/{project_id}/outputs/{output_id}",
    response_model=OutputResponse,
)
async def update_output(
    project_id: UUID,
    output_id: UUID,
    request: UpdateOutputRequest,
    session: AsyncSession = Depends(get_db),
) -> OutputResponse:
    """
    Update an output's title and/or data.

    This is used to persist user edits to generated content (e.g., mindmap changes).
    """
    updated = await output_generation_service.update_output(
        project_id=project_id,
        output_id=output_id,
        title=request.title,
        data=request.data,
        session=session,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Output not found")

    return OutputResponse(
        id=updated.id,
        project_id=updated.project_id,
        output_type=updated.output_type.value,
        document_ids=updated.document_ids,
        status=updated.status.value,
        title=updated.title,
        data=updated.data,
        error_message=updated.error_message,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


# =============================================================================
# Node Actions
# =============================================================================


@router.post(
    "/projects/{project_id}/outputs/{output_id}/nodes/{node_id}/explain",
    response_model=NodeActionResponse,
)
async def explain_node(
    project_id: UUID,
    output_id: UUID,
    node_id: str,
    request: ExplainNodeRequest,
    session: AsyncSession = Depends(get_db),
) -> NodeActionResponse:
    """
    Start explaining a node.

    Returns a task_id. The explanation will be streamed via WebSocket
    as TOKEN events.
    """
    logger.info(f"[Outputs API] Explain node: output={output_id}, node={node_id}")

    try:
        task_id = await output_generation_service.start_explain_node(
            project_id=project_id,
            output_id=output_id,
            node_id=node_id,
            node_data=request.node_data,
            session=session,
        )

        return NodeActionResponse(task_id=task_id, action="explain")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Outputs API] Explain failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start explanation")


@router.post(
    "/projects/{project_id}/outputs/{output_id}/nodes/{node_id}/explain/stream",
)
async def explain_node_stream(
    project_id: UUID,
    output_id: UUID,
    node_id: str,
    request: ExplainNodeRequest,
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Stream explanation for a node using Server-Sent Events.

    Alternative to WebSocket for simpler integration.
    """
    logger.info(f"[Outputs API] Explain stream: output={output_id}, node={node_id}")

    async def event_generator():
        try:
            async for token in output_generation_service.explain_node_stream(
                project_id=project_id,
                output_id=output_id,
                node_id=node_id,
                node_data=request.node_data,
                session=session,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"[Outputs API] Explain stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "/projects/{project_id}/outputs/{output_id}/nodes/{node_id}/expand",
    response_model=NodeActionResponse,
)
async def expand_node(
    project_id: UUID,
    output_id: UUID,
    node_id: str,
    request: ExpandNodeRequest,
    session: AsyncSession = Depends(get_db),
) -> NodeActionResponse:
    """
    Start expanding a node with additional children.

    Returns a task_id. New nodes will be streamed via WebSocket
    as NODE_ADDED and EDGE_ADDED events.
    """
    logger.info(f"[Outputs API] Expand node: output={output_id}, node={node_id}")

    try:
        task_id = await output_generation_service.start_expand_node(
            project_id=project_id,
            output_id=output_id,
            node_id=node_id,
            node_data=request.node_data,
            existing_children=request.existing_children,
            session=session,
        )

        return NodeActionResponse(task_id=task_id, action="expand")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Outputs API] Expand failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start expansion")


@router.post(
    "/projects/{project_id}/outputs/{output_id}/synthesize",
    response_model=NodeActionResponse,
)
async def synthesize_nodes(
    project_id: UUID,
    output_id: UUID,
    request: SynthesizeNodesRequest,
    session: AsyncSession = Depends(get_db),
) -> NodeActionResponse:
    """
    Synthesize multiple nodes into a consolidated insight.

    This endpoint takes 2+ node IDs and generates a new node that
    consolidates their content with AI-generated insights.

    Returns a task_id. The synthesized node will be streamed via WebSocket
    as a NODE_ADDED event.
    """
    from research_agent.application.dto.output import SynthesizeNodesRequest as SynthReq

    logger.info(f"[Outputs API] Synthesize nodes: output={output_id}, nodes={request.node_ids}")

    try:
        task_id = await output_generation_service.start_synthesize_nodes(
            project_id=project_id,
            output_id=output_id,
            node_ids=request.node_ids,
            node_data=request.node_data,
            session=session,
            mode=request.mode,
        )

        return NodeActionResponse(task_id=task_id, action="synthesize")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Outputs API] Synthesize failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start synthesis")


# =============================================================================
# Task Management
# =============================================================================


@router.post(
    "/projects/{project_id}/outputs/tasks/{task_id}/cancel",
    status_code=204,
)
async def cancel_task(
    project_id: UUID,
    task_id: str,
) -> None:
    """Cancel an ongoing generation task."""
    success = await output_generation_service.cancel_task(
        project_id=str(project_id),
        task_id=task_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Task not found or already completed")
