"""Update canvas node use case."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from research_agent.domain.repositories.canvas_repo import CanvasRepository
from research_agent.domain.repositories.project_repo import ProjectRepository
from research_agent.shared.exceptions import ConflictError, NotFoundError


@dataclass
class UpdateCanvasNodeInput:
    """Input for update canvas node use case."""

    project_id: UUID
    node_id: str
    node_data: Dict[str, Any]


@dataclass
class UpdateCanvasNodeOutput:
    """Output for update canvas node use case."""

    success: bool
    updated_at: datetime
    version: int  # Canvas version after update


class UpdateCanvasNodeUseCase:
    """Use case for updating a canvas node."""

    def __init__(
        self,
        canvas_repo: CanvasRepository,
        project_repo: ProjectRepository,
    ):
        self._canvas_repo = canvas_repo
        self._project_repo = project_repo

    async def execute(self, input: UpdateCanvasNodeInput) -> UpdateCanvasNodeOutput:
        """Execute the use case."""
        # Verify project exists
        project = await self._project_repo.find_by_id(input.project_id)
        if not project:
            raise NotFoundError("Project", str(input.project_id))

        # Get canvas with current version
        canvas = await self._canvas_repo.find_by_project(input.project_id)
        if not canvas:
            raise NotFoundError("Canvas", f"for project {input.project_id}")

        current_version = canvas.version

        # Find node
        node = canvas.find_node(input.node_id)
        if not node:
            raise NotFoundError("Node", input.node_id)

        # Prepare update kwargs (only include provided fields)
        update_kwargs = {}
        if "type" in input.node_data:
            update_kwargs["type"] = input.node_data["type"]
        if "title" in input.node_data:
            update_kwargs["title"] = input.node_data["title"]
        if "content" in input.node_data:
            update_kwargs["content"] = input.node_data["content"]
        if "x" in input.node_data:
            update_kwargs["x"] = input.node_data["x"]
        if "y" in input.node_data:
            update_kwargs["y"] = input.node_data["y"]
        if "width" in input.node_data:
            update_kwargs["width"] = input.node_data["width"]
        if "height" in input.node_data:
            update_kwargs["height"] = input.node_data["height"]
        if "color" in input.node_data:
            update_kwargs["color"] = input.node_data["color"]
        if "tags" in input.node_data:
            update_kwargs["tags"] = input.node_data["tags"]
        if "sourceId" in input.node_data:
            update_kwargs["source_id"] = input.node_data["sourceId"]
        if "sourcePage" in input.node_data:
            update_kwargs["source_page"] = input.node_data["sourcePage"]

        # Update node
        success = canvas.update_node(input.node_id, **update_kwargs)
        if not success:
            raise NotFoundError("Node", input.node_id)

        # Save canvas with version check (optimistic locking)
        try:
            saved_canvas = await self._canvas_repo.save_with_version(
                canvas, expected_version=current_version
            )
        except ConflictError:
            # Retry: reload canvas and merge updates
            canvas = await self._canvas_repo.find_by_project(input.project_id)
            if not canvas:
                raise NotFoundError("Canvas", f"for project {input.project_id}")
            
            # Check if node still exists
            node = canvas.find_node(input.node_id)
            if not node:
                raise NotFoundError("Node", input.node_id)
            
            # Re-apply updates
            canvas.update_node(input.node_id, **update_kwargs)
            saved_canvas = await self._canvas_repo.save_with_version(
                canvas, expected_version=canvas.version
            )

        return UpdateCanvasNodeOutput(
            success=True,
            updated_at=saved_canvas.updated_at,
            version=saved_canvas.version,
        )

