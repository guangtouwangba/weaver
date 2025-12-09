"""Clear canvas use case - removes all nodes, edges, and sections."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from research_agent.domain.entities.canvas import Canvas
from research_agent.domain.repositories.canvas_repo import CanvasRepository
from research_agent.domain.repositories.project_repo import ProjectRepository
from research_agent.shared.exceptions import NotFoundError


@dataclass
class ClearCanvasInput:
    """Input for clear canvas use case."""

    project_id: UUID
    view_type: Optional[str] = None  # 'free' | 'thinking' | None (clear all)


@dataclass
class ClearCanvasOutput:
    """Output for clear canvas use case."""

    success: bool
    updated_at: datetime
    version: int
    cleared_view: Optional[str] = None  # Which view was cleared


class ClearCanvasUseCase:
    """Use case for clearing canvas data (nodes, edges, sections).

    Supports clearing:
    - All canvas data (view_type=None)
    - Only 'free' view data (view_type='free')
    - Only 'thinking' view data (view_type='thinking')
    """

    def __init__(
        self,
        canvas_repo: CanvasRepository,
        project_repo: ProjectRepository,
    ):
        self._canvas_repo = canvas_repo
        self._project_repo = project_repo

    async def execute(self, input: ClearCanvasInput) -> ClearCanvasOutput:
        """Execute the use case."""
        # Verify project exists
        project = await self._project_repo.find_by_id(input.project_id)
        if not project:
            raise NotFoundError("Project", str(input.project_id))

        # Get existing canvas or create empty one
        canvas = await self._canvas_repo.find_by_project(input.project_id)

        if canvas:
            current_version = canvas.version

            if input.view_type:
                # Clear only specific view type
                canvas.clear_view(input.view_type)
            else:
                # Clear all data
                canvas.clear()

            # Save with version check
            saved_canvas = await self._canvas_repo.save_with_version(
                canvas, expected_version=current_version
            )
        else:
            # Create a new empty canvas
            canvas = Canvas.create_empty(input.project_id)
            saved_canvas = await self._canvas_repo.save(canvas)

        return ClearCanvasOutput(
            success=True,
            updated_at=saved_canvas.updated_at,
            version=saved_canvas.version,
            cleared_view=input.view_type,
        )

