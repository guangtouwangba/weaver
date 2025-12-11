"""Clear canvas use case - removes all nodes, edges, and sections.

Uses an async-friendly approach with generation IDs:
1. Increments the canvas generation (instant)
2. Old items become invisible but remain in storage
3. A background task cleans up old items later
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from research_agent.domain.entities.canvas import Canvas
from research_agent.domain.entities.task import TaskType
from research_agent.domain.repositories.canvas_repo import CanvasRepository
from research_agent.domain.repositories.project_repo import ProjectRepository
from research_agent.shared.exceptions import NotFoundError
from research_agent.worker.service import TaskQueueService


@dataclass
class ClearCanvasInput:
    """Input for clear canvas use case."""

    project_id: UUID
    view_type: Optional[str] = None  # 'free' | 'thinking' | None (clear all)
    schedule_cleanup: bool = True  # Whether to schedule async cleanup task


@dataclass
class ClearCanvasOutput:
    """Output for clear canvas use case."""

    success: bool
    updated_at: datetime
    version: int
    generation: int  # Current generation after clear
    cleared_view: Optional[str] = None  # Which view was cleared
    pending_cleanup: int = 0  # Number of items pending cleanup
    cleanup_task_id: Optional[str] = None  # Background task ID if scheduled


class ClearCanvasUseCase:
    """Use case for clearing canvas data (nodes, edges, sections).

    Uses generation-based async clearing:
    - Incrementing generation makes old items invisible instantly
    - Old items remain in storage until background cleanup
    - Users can immediately add new items without waiting

    Supports clearing:
    - All canvas data (view_type=None)
    - Only 'free' view data (view_type='free')
    - Only 'thinking' view data (view_type='thinking')
    """

    def __init__(
        self,
        canvas_repo: CanvasRepository,
        project_repo: ProjectRepository,
        task_queue_service: Optional[TaskQueueService] = None,
    ):
        self._canvas_repo = canvas_repo
        self._project_repo = project_repo
        self._task_queue_service = task_queue_service

    async def execute(self, input: ClearCanvasInput) -> ClearCanvasOutput:
        """Execute the use case."""
        # Verify project exists
        project = await self._project_repo.find_by_id(input.project_id)
        if not project:
            raise NotFoundError("Project", str(input.project_id))

        # Get existing canvas or create empty one
        canvas = await self._canvas_repo.find_by_project(input.project_id)
        cleanup_task_id = None

        if canvas:
            current_version = canvas.version

            if input.view_type:
                # Clear only specific view type (async-friendly)
                previous_generation = canvas.clear_view(input.view_type)
            else:
                # Clear all data (async-friendly)
                previous_generation = canvas.clear()

            # Count items pending cleanup
            pending_cleanup = canvas.get_old_items_count()

            # Save with version check
            saved_canvas = await self._canvas_repo.save_with_version(
                canvas, expected_version=current_version
            )

            # Schedule background cleanup task if there are items to clean
            if input.schedule_cleanup and pending_cleanup > 0 and self._task_queue_service:
                task = await self._task_queue_service.push(
                    task_type=TaskType.CLEANUP_CANVAS,
                    payload={
                        "project_id": str(input.project_id),
                        "generation_threshold": saved_canvas.current_generation,
                    },
                    priority=0,  # Low priority - cleanup is not urgent
                    max_attempts=3,
                )
                cleanup_task_id = str(task.id)
        else:
            # Create a new empty canvas
            canvas = Canvas.create_empty(input.project_id)
            saved_canvas = await self._canvas_repo.save(canvas)
            pending_cleanup = 0

        return ClearCanvasOutput(
            success=True,
            updated_at=saved_canvas.updated_at,
            version=saved_canvas.version,
            generation=saved_canvas.current_generation,
            cleared_view=input.view_type,
            pending_cleanup=pending_cleanup,
            cleanup_task_id=cleanup_task_id,
        )
