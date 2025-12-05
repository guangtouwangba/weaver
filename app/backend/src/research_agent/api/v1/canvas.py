"""Canvas API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.api.deps import get_db
from research_agent.application.dto.canvas import (
    CanvasDataRequest,
    CanvasDataResponse,
    CanvasEdgeDTO,
    CanvasNodeDTO,
    CanvasNodeOperationResponse,
    CanvasSaveResponse,
    CanvasViewportDTO,
    CreateCanvasNodeRequest,
    UpdateCanvasNodeRequest,
)
from research_agent.application.use_cases.canvas.create_node import (
    CreateCanvasNodeInput,
    CreateCanvasNodeUseCase,
)
from research_agent.application.use_cases.canvas.delete_node import (
    DeleteCanvasNodeInput,
    DeleteCanvasNodeUseCase,
)
from research_agent.application.use_cases.canvas.get_canvas import (
    GetCanvasInput,
    GetCanvasUseCase,
)
from research_agent.application.use_cases.canvas.save_canvas import (
    SaveCanvasInput,
    SaveCanvasUseCase,
)
from research_agent.application.use_cases.canvas.update_node import (
    UpdateCanvasNodeInput,
    UpdateCanvasNodeUseCase,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_canvas_repo import (
    SQLAlchemyCanvasRepository,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_project_repo import (
    SQLAlchemyProjectRepository,
)
from research_agent.shared.exceptions import ConflictError, NotFoundError

router = APIRouter()


@router.get("/projects/{project_id}/canvas", response_model=CanvasDataResponse)
async def get_canvas(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> CanvasDataResponse:
    """Get canvas data for a project."""
    canvas_repo = SQLAlchemyCanvasRepository(session)
    use_case = GetCanvasUseCase(canvas_repo)

    result = await use_case.execute(GetCanvasInput(project_id=project_id))

    data = result.data
    return CanvasDataResponse(
        nodes=[
            CanvasNodeDTO(
                id=n["id"],
                type=n.get("type", "card"),
                title=n.get("title", ""),
                content=n.get("content", ""),
                x=n.get("x", 0),
                y=n.get("y", 0),
                width=n.get("width", 200),
                height=n.get("height", 150),
                color=n.get("color", "default"),
                tags=n.get("tags", []),
                sourceId=n.get("sourceId"),
                sourcePage=n.get("sourcePage"),
            )
            for n in data.get("nodes", [])
        ],
        edges=[
            CanvasEdgeDTO(
                id=e.get("id"),
                source=e["source"],
                target=e["target"],
            )
            for e in data.get("edges", [])
        ],
        viewport=CanvasViewportDTO(
            x=data.get("viewport", {}).get("x", 0),
            y=data.get("viewport", {}).get("y", 0),
            scale=data.get("viewport", {}).get("scale", 1),
        ),
        updated_at=result.updated_at,
        version=result.version,
    )


@router.put("/projects/{project_id}/canvas", response_model=CanvasSaveResponse)
async def save_canvas(
    project_id: UUID,
    request: CanvasDataRequest,
    session: AsyncSession = Depends(get_db),
) -> CanvasSaveResponse:
    """Save canvas data for a project."""
    canvas_repo = SQLAlchemyCanvasRepository(session)
    project_repo = SQLAlchemyProjectRepository(session)

    use_case = SaveCanvasUseCase(
        canvas_repo=canvas_repo,
        project_repo=project_repo,
    )

    # Convert request to dict
    canvas_data = {
        "nodes": [n.model_dump() for n in request.nodes],
        "edges": [e.model_dump() for e in request.edges],
        "viewport": request.viewport.model_dump(),
    }

    try:
        result = await use_case.execute(
            SaveCanvasInput(
                project_id=project_id,
                data=canvas_data,
            )
        )

        return CanvasSaveResponse(
            success=result.success,
            updated_at=result.updated_at,
            version=result.version,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.post(
    "/projects/{project_id}/canvas/nodes",
    response_model=CanvasNodeOperationResponse,
    status_code=201,
)
async def create_canvas_node(
    project_id: UUID,
    request: CreateCanvasNodeRequest,
    session: AsyncSession = Depends(get_db),
) -> CanvasNodeOperationResponse:
    """Create a new canvas node."""
    canvas_repo = SQLAlchemyCanvasRepository(session)
    project_repo = SQLAlchemyProjectRepository(session)

    use_case = CreateCanvasNodeUseCase(
        canvas_repo=canvas_repo,
        project_repo=project_repo,
    )

    # Convert request to dict (keep camelCase for sourceId and sourcePage)
    node_data = request.model_dump(exclude_unset=True)

    try:
        result = await use_case.execute(
            CreateCanvasNodeInput(
                project_id=project_id,
                node_data=node_data,
            )
        )

        return CanvasNodeOperationResponse(
            success=result.success,
            nodeId=result.node_id,
            updated_at=result.updated_at,
            version=result.version,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.put(
    "/projects/{project_id}/canvas/nodes/{node_id}",
    response_model=CanvasNodeOperationResponse,
)
async def update_canvas_node(
    project_id: UUID,
    node_id: str,
    request: UpdateCanvasNodeRequest,
    session: AsyncSession = Depends(get_db),
) -> CanvasNodeOperationResponse:
    """Update a canvas node."""
    canvas_repo = SQLAlchemyCanvasRepository(session)
    project_repo = SQLAlchemyProjectRepository(session)

    use_case = UpdateCanvasNodeUseCase(
        canvas_repo=canvas_repo,
        project_repo=project_repo,
    )

    # Convert request to dict (only include provided fields, keep camelCase)
    node_data = request.model_dump(exclude_unset=True)

    try:
        result = await use_case.execute(
            UpdateCanvasNodeInput(
                project_id=project_id,
                node_id=node_id,
                node_data=node_data,
            )
        )

        return CanvasNodeOperationResponse(
            success=result.success,
            updated_at=result.updated_at,
            version=result.version,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.delete(
    "/projects/{project_id}/canvas/nodes/{node_id}",
    response_model=CanvasNodeOperationResponse,
)
async def delete_canvas_node(
    project_id: UUID,
    node_id: str,
    session: AsyncSession = Depends(get_db),
) -> CanvasNodeOperationResponse:
    """Delete a canvas node."""
    canvas_repo = SQLAlchemyCanvasRepository(session)
    project_repo = SQLAlchemyProjectRepository(session)

    use_case = DeleteCanvasNodeUseCase(
        canvas_repo=canvas_repo,
        project_repo=project_repo,
    )

    try:
        result = await use_case.execute(
            DeleteCanvasNodeInput(
                project_id=project_id,
                node_id=node_id,
            )
        )

        return CanvasNodeOperationResponse(
            success=result.success,
            updated_at=result.updated_at,
            version=result.version,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
