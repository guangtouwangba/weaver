"""Delete canvas node use case."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from research_agent.domain.repositories.canvas_repo import CanvasRepository
from research_agent.domain.repositories.project_repo import ProjectRepository
from research_agent.shared.exceptions import ConflictError, NotFoundError


@dataclass
class DeleteCanvasNodeInput:
    """Input for delete canvas node use case."""

    project_id: UUID
    node_id: str
    user_id: str | None = None


@dataclass
class DeleteCanvasNodeOutput:
    """Output for delete canvas node use case."""

    success: bool
    updated_at: datetime
    version: int  # Canvas version after update


class DeleteCanvasNodeUseCase:
    """Use case for deleting a canvas node."""

    def __init__(
        self,
        canvas_repo: CanvasRepository,
        project_repo: ProjectRepository,
    ):
        self._canvas_repo = canvas_repo
        self._project_repo = project_repo

    async def execute(self, input: DeleteCanvasNodeInput) -> DeleteCanvasNodeOutput:
        """Execute the use case."""
        # Verify project exists
        project = await self._project_repo.find_by_id(input.project_id)
        if not project:
            raise NotFoundError("Project", str(input.project_id))

        # Get canvas with current version
        canvas = await self._canvas_repo.find_by_project(
            project_id=input.project_id, user_id=input.user_id
        )
        if not canvas:
            raise NotFoundError("Canvas", f"for project {input.project_id}")

        current_version = canvas.version

        # Check if node exists
        node = canvas.find_node(input.node_id)
        if not node:
            raise NotFoundError("Node", input.node_id)

        # Remove node (this also removes related edges)
        canvas.remove_node(input.node_id)

        # Save canvas with version check (optimistic locking)
        try:
            saved_canvas = await self._canvas_repo.save_with_version(
                canvas, expected_version=current_version
            )
        except ConflictError:
            # Retry: reload canvas and check if node still exists
            canvas = await self._canvas_repo.find_by_project(input.project_id)
            if not canvas:
                raise NotFoundError("Canvas", f"for project {input.project_id}")

            # Check if node still exists (might have been deleted by another request)
            node = canvas.find_node(input.node_id)
            if node:
                canvas.remove_node(input.node_id)
            saved_canvas = await self._canvas_repo.save_with_version(
                canvas, expected_version=canvas.version
            )

        return DeleteCanvasNodeOutput(
            success=True,
            updated_at=saved_canvas.updated_at,
            version=saved_canvas.version,
        )
