"""Save canvas use case."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from research_agent.domain.entities.canvas import Canvas
from research_agent.domain.repositories.canvas_repo import CanvasRepository
from research_agent.domain.repositories.project_repo import ProjectRepository
from research_agent.shared.exceptions import ConflictError, NotFoundError
from research_agent.shared.utils.logger import logger


@dataclass
class SaveCanvasInput:
    """Input for save canvas use case."""

    project_id: UUID
    project_id: UUID
    data: dict[str, Any]
    user_id: str | None = None


@dataclass
class SaveCanvasOutput:
    """Output for save canvas use case."""

    success: bool
    updated_at: datetime
    version: int  # Canvas version after save


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

        # Get existing canvas to preserve version
        existing_canvas = await self._canvas_repo.find_by_project(
            project_id=input.project_id, user_id=input.user_id
        )
        current_version = existing_canvas.version if existing_canvas else 0

        # Create canvas from data
        canvas = Canvas.from_dict(
            data=input.data, project_id=input.project_id, user_id=input.user_id
        )
        if existing_canvas:
            canvas.version = existing_canvas.version

        # Save canvas with version check (optimistic locking)
        # Retry with exponential backoff on lock conflicts
        max_retries = 3
        base_delay = 0.1  # 100ms
        last_error = None

        for attempt in range(max_retries):
            try:
                saved_canvas = await self._canvas_repo.save_with_version(
                    canvas, expected_version=current_version
                )
                break  # Success, exit retry loop
            except ConflictError as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Wait with exponential backoff before retry
                    delay = base_delay * (2**attempt)
                    logger.debug(
                        f"[Canvas] Lock conflict on attempt {attempt + 1}, retrying in {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)
                    # Reload to get latest version
                    existing_canvas = await self._canvas_repo.find_by_project(input.project_id)
                    current_version = existing_canvas.version if existing_canvas else 0
                    if existing_canvas:
                        canvas.version = existing_canvas.version
        else:
            # All retries exhausted
            logger.warning(
                f"[Canvas] Failed to save canvas after {max_retries} attempts "
                f"for project {input.project_id}"
            )
            raise last_error

        return SaveCanvasOutput(
            success=True,
            updated_at=saved_canvas.updated_at,
            version=saved_canvas.version,
        )
