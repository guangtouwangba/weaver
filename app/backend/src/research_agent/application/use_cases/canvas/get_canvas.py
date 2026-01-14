"""Get canvas use case."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from research_agent.domain.repositories.canvas_repo import CanvasRepository


@dataclass
class GetCanvasInput:
    """Input for get canvas use case."""

    project_id: UUID
    user_id: str | None = None


@dataclass
class GetCanvasOutput:
    """Output for get canvas use case."""

    data: dict[str, Any]
    updated_at: datetime | None
    version: int | None = None  # Canvas version


class GetCanvasUseCase:
    """Use case for getting canvas data."""

    def __init__(self, canvas_repo: CanvasRepository):
        self._canvas_repo = canvas_repo

    async def execute(self, input: GetCanvasInput) -> GetCanvasOutput:
        """Execute the use case."""
        canvas = await self._canvas_repo.find_by_project(
            project_id=input.project_id, user_id=input.user_id
        )

        if canvas:
            # Use to_visible_dict() to only return current generation items
            # Old items (from previous clears) are excluded
            return GetCanvasOutput(
                data=canvas.to_visible_dict(),
                updated_at=canvas.updated_at,
                version=canvas.version,
            )

        # Return empty canvas if not found
        return GetCanvasOutput(
            data={
                "nodes": [],
                "edges": [],
                "viewport": {"x": 0, "y": 0, "scale": 1},
                "currentGeneration": 1,
            },
            updated_at=None,
            version=0,
        )
