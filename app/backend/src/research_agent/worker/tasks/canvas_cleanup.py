"""Canvas cleanup task - removes old generation items from canvas."""

from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.database.repositories.sqlalchemy_canvas_repo import (
    SQLAlchemyCanvasRepository,
)
from research_agent.shared.utils.logger import logger
from research_agent.worker.tasks.base import BaseTask


class CanvasCleanupTask(BaseTask):
    """Background task for cleaning up old canvas items.

    This task is triggered after a canvas clear operation.
    It physically removes items from previous generations to free up storage.
    """

    @property
    def task_type(self) -> str:
        return "cleanup_canvas"

    async def execute(self, payload: Dict[str, Any], session: AsyncSession) -> None:
        """
        Execute the canvas cleanup task.

        Args:
            payload: Task payload containing:
                - project_id: UUID of the project
                - generation_threshold: Remove items with generation < threshold
            session: Database session
        """
        project_id_str = payload.get("project_id")
        generation_threshold = payload.get("generation_threshold")

        if not project_id_str:
            raise ValueError("Missing project_id in payload")

        if not generation_threshold:
            raise ValueError("Missing generation_threshold in payload")

        project_id = UUID(project_id_str)

        logger.info(
            f"[CanvasCleanup] Starting cleanup for project {project_id}, "
            f"removing items with generation < {generation_threshold}"
        )

        canvas_repo = SQLAlchemyCanvasRepository(session)

        # Get the canvas
        canvas = await canvas_repo.find_by_project(project_id)

        if not canvas:
            logger.info(f"[CanvasCleanup] No canvas found for project {project_id}")
            return

        # Count items before cleanup
        old_items_count = canvas.get_old_items_count()

        if old_items_count == 0:
            logger.info(f"[CanvasCleanup] No old items to clean up for project {project_id}")
            return

        # Remove old items
        removed_count = canvas.remove_old_items(generation_threshold)

        # Save the cleaned canvas
        await canvas_repo.save(canvas)

        logger.info(
            f"[CanvasCleanup] Cleanup complete for project {project_id}: "
            f"removed {removed_count} items (nodes, edges, sections)"
        )











