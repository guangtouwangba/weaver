"""Auto-structure canvas use case."""

from dataclasses import dataclass
from typing import List
from uuid import UUID

from research_agent.domain.entities.canvas import CanvasEdge, CanvasSection
from research_agent.domain.repositories.canvas_repo import CanvasRepository
from research_agent.domain.services.canvas_structure_service import CanvasStructureService
from research_agent.shared.exceptions import NotFoundError
from research_agent.shared.utils.logger import logger


@dataclass
class AutoStructureInput:
    """Input for auto-structure canvas use case."""

    project_id: UUID
    similarity_threshold: float = 0.75


@dataclass
class AutoStructureOutput:
    """Output for auto-structure canvas use case."""

    sections_created: int
    edges_created: int
    data: dict  # Return full canvas dict for frontend update


class AutoStructureCanvasUseCase:
    """Use case for auto-structuring canvas data."""

    def __init__(
        self,
        canvas_repo: CanvasRepository,
        structure_service: CanvasStructureService,
    ):
        self._canvas_repo = canvas_repo
        self._structure_service = structure_service

    async def execute(self, input: AutoStructureInput) -> AutoStructureOutput:
        """Execute the use case."""
        # 1. Get existing canvas
        canvas = await self._canvas_repo.find_by_project(input.project_id)
        if not canvas:
            raise NotFoundError("Canvas", str(input.project_id))

        # 2. Get visible nodes (only structure current generation)
        visible_nodes = canvas.get_visible_nodes()
        if not visible_nodes:
            logger.info("Canvas is empty, nothing to structure.")
            return AutoStructureOutput(0, 0, canvas.to_visible_dict())

        # 3. Cluster Nodes -> Create Sections
        new_sections = await self._structure_service.cluster_nodes(
            visible_nodes, similarity_threshold=input.similarity_threshold
        )

        # 4. Suggest Links -> Create Edges
        # We only look for links that don't exist yet
        visible_edges = canvas.get_visible_edges()
        new_edges = await self._structure_service.suggest_global_links(
            visible_nodes, visible_edges, similarity_threshold=input.similarity_threshold
        )

        # 5. Apply changes to Canvas
        # Add sections
        for section in new_sections:
            canvas.add_section(section)

            # Map nodes to this section?
            # CanvasSection stores node_ids.
            # Does CanvasNode need to know its section_id?
            # Looking at CanvasNode definition: `section_id: Optional[str] = None`
            # Yes, we should update the nodes to point to the new section.
            for node_id in section.node_ids:
                canvas.update_node(node_id, section_id=section.id)

        # Add edges
        for edge in new_edges:
            canvas.add_edge(edge)

        # 6. Save Canvas
        # We use save_with_version (optimistic locking)
        # For simplicity in this use case, we assume no contention or retry logic is up to caller/controller?
        # But SaveCanvasUseCase had retry logic.
        # Ideally we should reuse save logic or implement retry here.
        # Let's simple call save for now, or copy the retry loop if needed.
        # Given this is an async operation triggered by user, a failure can be reported.

        await self._canvas_repo.save_with_version(canvas, expected_version=canvas.version)

        logger.info(
            f"[AutoStructure] Created {len(new_sections)} sections and {len(new_edges)} edges "
            f"for project {input.project_id}"
        )

        return AutoStructureOutput(
            sections_created=len(new_sections),
            edges_created=len(new_edges),
            data=canvas.to_visible_dict(),
        )
