"""Create canvas node use case."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4

from research_agent.domain.entities.canvas import Canvas, CanvasNode
from research_agent.domain.repositories.canvas_repo import CanvasRepository
from research_agent.domain.repositories.project_repo import ProjectRepository
from research_agent.shared.exceptions import ConflictError, NotFoundError


@dataclass
class CreateCanvasNodeInput:
    """Input for create canvas node use case."""

    project_id: UUID
    node_data: Dict[str, Any]


@dataclass
class CreateCanvasNodeOutput:
    """Output for create canvas node use case."""

    success: bool
    node_id: str
    updated_at: datetime
    version: int  # Canvas version after update


class CreateCanvasNodeUseCase:
    """Use case for creating a canvas node."""

    def __init__(
        self,
        canvas_repo: CanvasRepository,
        project_repo: ProjectRepository,
    ):
        self._canvas_repo = canvas_repo
        self._project_repo = project_repo

    async def execute(self, input: CreateCanvasNodeInput) -> CreateCanvasNodeOutput:
        """Execute the use case."""
        # Verify project exists
        project = await self._project_repo.find_by_id(input.project_id)
        if not project:
            raise NotFoundError("Project", str(input.project_id))

        # Get or create canvas
        canvas = await self._canvas_repo.find_by_project(input.project_id)
        current_version = canvas.version if canvas else 0

        if not canvas:
            # Create empty canvas
            canvas = Canvas(
                project_id=input.project_id,
                nodes=[],
                edges=[],
                version=0,
            )

        # Generate node ID if not provided
        node_id = input.node_data.get("id")
        if not node_id:
            node_id = f"node-{uuid4().hex[:12]}"

        # Check if node ID already exists
        if canvas.find_node(node_id):
            raise ConflictError("Node", node_id, f"Node with ID {node_id} already exists")

        # Create node from data
        # Note: generation is set automatically by canvas.add_node()
        node = CanvasNode(
            id=node_id,
            type=input.node_data.get("type", "card"),
            title=input.node_data.get("title", ""),
            content=input.node_data.get("content", ""),
            x=input.node_data.get("x", 0),
            y=input.node_data.get("y", 0),
            width=input.node_data.get("width", 200),
            height=input.node_data.get("height", 150),
            color=input.node_data.get("color", "default"),
            tags=input.node_data.get("tags", []),
            source_id=input.node_data.get("sourceId"),
            source_page=input.node_data.get("sourcePage"),
            view_type=input.node_data.get("viewType", "free"),
            section_id=input.node_data.get("sectionId"),
        )

        # Add node to canvas
        canvas.add_node(node)

        # Save canvas with version check (optimistic locking)
        try:
            saved_canvas = await self._canvas_repo.save_with_version(
                canvas, expected_version=current_version
            )
        except ConflictError:
            # Retry: reload canvas and try again
            canvas = await self._canvas_repo.find_by_project(input.project_id)
            if not canvas:
                canvas = Canvas(
                    project_id=input.project_id,
                    nodes=[],
                    edges=[],
                    version=0,
                )
            # Check if node was already added by another request
            if not canvas.find_node(node_id):
                canvas.add_node(node)
            saved_canvas = await self._canvas_repo.save_with_version(
                canvas, expected_version=canvas.version
            )

        return CreateCanvasNodeOutput(
            success=True,
            node_id=node_id,
            updated_at=saved_canvas.updated_at,
            version=saved_canvas.version,
        )
