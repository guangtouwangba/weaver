"""Save canvas use case."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from research_agent.domain.entities.canvas import Canvas
from research_agent.domain.repositories.canvas_repo import CanvasRepository
from research_agent.domain.repositories.project_repo import ProjectRepository
from research_agent.shared.exceptions import NotFoundError


@dataclass
class SaveCanvasInput:
    """Input for save canvas use case."""

    project_id: UUID
    data: Dict[str, Any]


@dataclass
class SaveCanvasOutput:
    """Output for save canvas use case."""

    success: bool
    updated_at: datetime


class SaveCanvasUseCase:
    """Use case for saving canvas data."""

    def __init__(
        self,
        canvas_repo: CanvasRepository,
        project_repo: ProjectRepository,
    ):
        self._canvas_repo = canvas_repo
        self._project_repo = project_repo

    async def execute(self, input: SaveCanvasInput) -> SaveCanvasOutput:
        """Execute the use case."""
        # Verify project exists
        project = await self._project_repo.find_by_id(input.project_id)
        if not project:
            raise NotFoundError("Project", str(input.project_id))

        # Create canvas from data
        canvas = Canvas.from_dict(input.data, input.project_id)

        # Save canvas
        saved_canvas = await self._canvas_repo.save(canvas)

        return SaveCanvasOutput(
            success=True,
            updated_at=saved_canvas.updated_at,
        )

