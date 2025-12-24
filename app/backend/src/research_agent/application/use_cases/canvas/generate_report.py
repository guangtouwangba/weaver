"""Generate canvas report use case."""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from research_agent.domain.repositories.canvas_repo import CanvasRepository
from research_agent.domain.services.canvas_narrative_service import CanvasNarrativeService
from research_agent.shared.exceptions import NotFoundError
from research_agent.shared.utils.logger import logger


@dataclass
class GenerateReportInput:
    """Input for generate report use case."""

    project_id: UUID
    node_ids: Optional[List[str]] = None
    prompt_instruction: str = "Write a comprehensive summary report based on these notes."


@dataclass
class GenerateReportOutput:
    """Output for generate report use case."""

    report_content: str
    node_order: List[str]  # IDs of nodes in the order they were used


class GenerateCanvasReportUseCase:
    """Use case for generating narrative report from canvas."""

    def __init__(
        self,
        canvas_repo: CanvasRepository,
        narrative_service: CanvasNarrativeService,
    ):
        self._canvas_repo = canvas_repo
        self._narrative_service = narrative_service

    async def execute(self, input: GenerateReportInput) -> GenerateReportOutput:
        """Execute the use case."""
        # 1. Get Canvas
        canvas = await self._canvas_repo.find_by_project(input.project_id)
        if not canvas:
            raise NotFoundError("Canvas", str(input.project_id))

        # 2. Filter Nodes & Edges
        visible_nodes = canvas.get_visible_nodes()
        visible_edges = canvas.get_visible_edges()

        selected_nodes = visible_nodes
        if input.node_ids:
            selected_set = set(input.node_ids)
            selected_nodes = [n for n in visible_nodes if n.id in selected_set]
            # Filter edges: only include edges where both source/target are in selected set
            selected_edges = [
                e for e in visible_edges if e.source in selected_set and e.target in selected_set
            ]
        else:
            selected_edges = visible_edges

        if not selected_nodes:
            return GenerateReportOutput("No nodes selected to generate report.", [])

        # 3. Plan Path (Structure the Narrative)
        ordered_nodes = self._narrative_service.plan_narrative_path(selected_nodes, selected_edges)

        # 4. Generate Report (Write the content)
        report_content = await self._narrative_service.generate_report(
            ordered_nodes, selected_edges, prompt_instruction=input.prompt_instruction
        )

        logger.info(
            f"[GenerateReport] Generated {len(report_content)} chars "
            f"from {len(ordered_nodes)} nodes for project {input.project_id}"
        )

        return GenerateReportOutput(
            report_content=report_content, node_order=[n.id for n in ordered_nodes]
        )
