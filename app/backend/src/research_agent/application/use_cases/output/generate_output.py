"""Use case for generating outputs (mindmap, summary, etc.)."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from research_agent.domain.agents.base_agent import BaseOutputAgent, OutputEvent
from research_agent.domain.agents.mindmap_agent import MindmapAgent
from research_agent.domain.agents.summary_agent import SummaryAgent
from research_agent.domain.entities.output import (
    MindmapData,
    Output,
    OutputStatus,
    OutputType,
    SummaryData,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_document_repo import (
    SQLAlchemyDocumentRepository,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_output_repo import (
    SQLAlchemyOutputRepository,
)
from research_agent.infrastructure.llm.base import LLMService
from research_agent.shared.utils.logger import logger


@dataclass
class GenerateOutputInput:
    """Input for generate output use case."""

    project_id: UUID
    output_type: str
    source_ids: list[UUID]
    title: str | None = None
    options: dict[str, Any] | None = None


@dataclass
class GenerateOutputOutput:
    """Output for generate output use case."""

    output_id: UUID
    task_id: str


class GenerateOutputUseCase:
    """
    Use case for generating outputs from documents.

    Handles:
    1. Creating the output record
    2. Loading document content
    3. Running the appropriate agent
    4. Streaming events
    5. Saving the final result
    """

    def __init__(
        self,
        output_repo: SQLAlchemyOutputRepository,
        document_repo: SQLAlchemyDocumentRepository,
        llm_service: LLMService,
    ):
        self._output_repo = output_repo
        self._document_repo = document_repo
        self._llm_service = llm_service

    async def execute(
        self,
        input: GenerateOutputInput,
    ) -> AsyncIterator[OutputEvent]:
        """
        Execute the use case, yielding events as generation progresses.

        Args:
            input: Generation input parameters

        Yields:
            OutputEvent instances during generation
        """
        output_id = uuid4()

        logger.info(
            f"[GenerateOutput] Starting: project={input.project_id}, "
            f"type={input.output_type}, sources={len(input.source_ids)}"
        )

        # Step 1: Create output record
        output = Output(
            id=output_id,
            project_id=input.project_id,
            output_type=OutputType(input.output_type),
            source_ids=input.source_ids,
            status=OutputStatus.GENERATING,
            title=input.title,
        )
        await self._output_repo.create(output)

        try:
            # Step 2: Load content via ResourceResolver (unified)
            # from research_agent.infrastructure.resource_resolver import ResourceResolver # Removed unused import

            # We need a session, but this use case doesn't have one in __init__
            # This use case seems outdated or assuming a different context.
            # I'll keep the legacy document loading for now but rename the input.
            document_content = await self._load_source_content(input.source_ids)
            document_title = input.title or "Content"

            if not document_content:
                raise ValueError("No document content found")

            # Step 3: Create appropriate agent
            agent = self._create_agent(input.output_type, input.options or {})

            # Step 4: Run generation and collect results
            output_data: Any = None
            if input.output_type == OutputType.MINDMAP:
                output_data = MindmapData()
            elif input.output_type == OutputType.SUMMARY:
                output_data = SummaryData(summary="")

            async for event in agent.generate(
                document_content=document_content,
                document_title=document_title,
                **(input.options or {}),
            ):
                yield event

                # Collect results based on type
                if input.output_type == OutputType.MINDMAP and isinstance(output_data, MindmapData):
                    if event.node_data:
                        from research_agent.domain.entities.output import MindmapNode

                        node = MindmapNode.from_dict(event.node_data)
                        output_data.add_node(node)

                    if event.edge_data:
                        from research_agent.domain.entities.output import MindmapEdge

                        edge = MindmapEdge.from_dict(event.edge_data)
                        output_data.add_edge(edge)

                elif input.output_type == OutputType.SUMMARY:
                    # Summary agent returns full data in GENERATION_COMPLETE event
                    from research_agent.domain.agents.base_agent import OutputEventType

                    if event.type == OutputEventType.GENERATION_COMPLETE and event.node_data:
                        output_data = SummaryData.from_dict(event.node_data)

            # Step 5: Save final result
            if output_data:
                output.mark_complete(output_data.to_dict())
                await self._output_repo.update(output)

            logger.info(f"[GenerateOutput] Complete: output={output_id}")

        except Exception as e:
            logger.error(f"[GenerateOutput] Failed: {e}", exc_info=True)

            # Mark output as failed
            output.mark_error(str(e))
            await self._output_repo.update(output)

            # Yield error event
            from research_agent.domain.agents.base_agent import OutputEventType

            yield OutputEvent(
                type=OutputEventType.GENERATION_ERROR,
                error_message=str(e),
            )

    async def _load_source_content(self, source_ids: list[UUID]) -> str:
        """Load and combine content from sources (legacy backup)."""
        contents: list[str] = []

        for source_id in source_ids:
            document = await self._document_repo.find_by_id(source_id)
            if not document:
                logger.warning(f"[GenerateOutput] Source (document) not found: {source_id}")
                continue

            # Prefer full_content, fall back to summary
            if document.full_content:
                contents.append(f"# {document.original_filename}\n\n{document.full_content}")
            elif document.summary:
                contents.append(f"# {document.original_filename}\n\n{document.summary}")
            else:
                logger.warning(f"[GenerateOutput] No content for source: {source_id}")

        return "\n\n---\n\n".join(contents)

    def _create_agent(self, output_type: str, options: dict[str, Any]) -> BaseOutputAgent:
        """Create the appropriate agent for the output type."""
        if output_type == "mindmap":
            # Default to conservative settings to prevent frontend freezing
            # max_depth=2, max_branches=4 → max ~21 nodes (1 + 4 + 16)
            return MindmapAgent(
                llm_service=self._llm_service,
                max_depth=options.get("max_depth", 2),
                max_branches_per_node=options.get("max_branches", 4),
            )
        elif output_type == "summary":
            return SummaryAgent(
                llm_service=self._llm_service,
            )
        else:
            # For now, all types use MindmapAgent
            # Can extend with SummaryAgent, etc. later
            raise ValueError(f"Unsupported output type: {output_type}")

    @property
    def output_id(self) -> UUID | None:
        """Get the output ID (available after execution starts)."""
        return getattr(self, "_output_id", None)
