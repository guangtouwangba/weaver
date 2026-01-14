"""Service for managing output generation with concurrent task support."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.domain.agents.action_list_agent import ActionListAgent
from research_agent.domain.agents.article_agent import ArticleAgent
from research_agent.domain.agents.base_agent import OutputEventType
from research_agent.domain.agents.flashcard_agent import FlashcardAgent
from research_agent.domain.agents.mindmap_agent import MindmapAgent
from research_agent.domain.agents.summary_agent import SummaryAgent
from research_agent.domain.entities.output import (
    ActionListData,
    ArticleData,
    FlashcardData,
    MindmapData,
    MindmapEdge,
    MindmapNode,
    Output,
    OutputStatus,
    OutputType,
    SummaryData,
)
from research_agent.infrastructure.database.repositories.sqlalchemy_output_repo import (
    SQLAlchemyOutputRepository,
)
from research_agent.infrastructure.llm.openrouter import OpenRouterLLMService
from research_agent.infrastructure.resource_resolver import ResourceResolver
from research_agent.infrastructure.websocket.output_notification_service import (
    output_notification_service,
)
from research_agent.shared.utils.logger import logger


@dataclass
class TaskInfo:
    """Information about a running task."""

    task_id: str
    project_id: str
    output_id: UUID
    output_type: str
    status: str = "running"
    created_at: datetime = field(default_factory=datetime.utcnow)
    asyncio_task: asyncio.Task | None = None


class OutputGenerationService:
    """
    Service for managing output generation with concurrent task support.

    Features:
    - Task isolation: Each task has independent state
    - Concurrency limiting: Max N concurrent tasks per user/project
    - Cancellation support: Can cancel ongoing tasks
    - WebSocket integration: Streams events to connected clients
    """

    def __init__(self, max_concurrent_per_project: int = 3):
        """
        Initialize the service.

        Args:
            max_concurrent_per_project: Maximum concurrent tasks per project
        """
        self._max_concurrent = max_concurrent_per_project
        # Map: task_id -> TaskInfo
        self._active_tasks: dict[str, TaskInfo] = {}
        # Map: project_id -> Semaphore
        self._project_semaphores: dict[str, asyncio.Semaphore] = {}
        # Lock for task management
        self._lock = asyncio.Lock()

    def _get_semaphore(self, project_id: str) -> asyncio.Semaphore:
        """Get or create semaphore for a project."""
        if project_id not in self._project_semaphores:
            self._project_semaphores[project_id] = asyncio.Semaphore(self._max_concurrent)
        return self._project_semaphores[project_id]

    async def start_generation(
        self,
        project_id: UUID,
        output_type: str,
        source_ids: list[UUID],
        title: str | None,
        options: dict[str, Any],
        session: AsyncSession,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Start a new output generation task.

        Args:
            project_id: Project ID
            output_type: Type of output (mindmap, summary, etc.)
            source_ids: List of document or URL content IDs
            title: Optional title
            options: Generation options
            session: Database session
            user_id: Optional user ID for data isolation

        Returns:
            Dict with task_id and output_id
        """

        # Validate that we have some content source, except for types that use node_data
        # Custom, article, and action_list types can work with canvas node_data instead of documents
        types_with_node_data = ("custom", "article", "action_list")
        has_node_data = options and (options.get("node_data") or options.get("mode"))
        is_type_with_node_data = output_type in types_with_node_data and has_node_data
        has_content_source = bool(source_ids)

        if not has_content_source and not is_type_with_node_data:
            raise ValueError(
                "At least one source ID (document or URL) is required for output generation"
            )

        task_id = str(uuid4())
        output_id = uuid4()
        project_id_str = str(project_id)

        logger.info(
            f"[OutputService] Starting generation: task={task_id}, "
            f"project={project_id}, type={output_type}, sources={len(source_ids)}"
        )

        # Create output record
        output_repo = SQLAlchemyOutputRepository(session)
        output = Output(
            id=output_id,
            project_id=project_id,
            user_id=user_id,
            output_type=OutputType(output_type),
            source_ids=source_ids,
            status=OutputStatus.GENERATING,
            title=title,
        )
        await output_repo.create(output)

        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            project_id=project_id_str,
            output_id=output_id,
            output_type=output_type,
        )

        async with self._lock:
            self._active_tasks[task_id] = task_info

        # Start async generation task
        asyncio_task = asyncio.create_task(
            self._run_generation(
                task_info=task_info,
                source_ids=source_ids,
                title=title,
                options=options,
            )
        )
        task_info.asyncio_task = asyncio_task

        # Notify clients
        await output_notification_service.notify_generation_started(
            project_id=project_id_str,
            task_id=task_id,
            output_type=output_type,
            message=f"Starting {output_type} generation",
        )

        return {
            "task_id": task_id,
            "output_id": output_id,
        }

    async def list_outputs(
        self,
        project_id: UUID,
        output_type: str | None,
        limit: int,
        offset: int,
        session: AsyncSession,
        user_id: str | None = None,
    ) -> tuple[list[Output], int]:
        """List outputs with filtering."""
        repo = SQLAlchemyOutputRepository(session)
        return await repo.find_by_project(
            project_id=project_id,
            output_type=output_type,
            limit=limit,
            offset=offset,
            user_id=user_id,
        )

    async def get_output(
        self,
        project_id: UUID,
        output_id: UUID,
        session: AsyncSession,
        user_id: str | None = None,
    ) -> Output | None:
        """Get output by ID."""
        repo = SQLAlchemyOutputRepository(session)
        output = await repo.find_by_id(output_id)

        # Verify project and user ownership
        if not output or output.project_id != project_id:
            return None

        if user_id and output.user_id and output.user_id != user_id:
            return None

        return output

    async def update_output(
        self,
        project_id: UUID,
        output_id: UUID,
        title: str | None,
        data: dict[str, Any] | None,
        session: AsyncSession,
        user_id: str | None = None,
    ) -> Output | None:
        """Update output."""
        repo = SQLAlchemyOutputRepository(session)
        output = await repo.find_by_id(output_id)

        if not output or output.project_id != project_id:
            return None

        if user_id and output.user_id and output.user_id != user_id:
            return None

        if title is not None:
            output.title = title
        if data is not None:
            output.data = data

        return await repo.update(output)

    async def delete_output(
        self,
        project_id: UUID,
        output_id: UUID,
        session: AsyncSession,
        user_id: str | None = None,
    ) -> bool:
        """Delete output."""
        repo = SQLAlchemyOutputRepository(session)
        output = await repo.find_by_id(output_id)

        if not output or output.project_id != project_id:
            return False

        if user_id and output.user_id and output.user_id != user_id:
            return False

        return await repo.delete(output_id)

    async def start_expand_node(
        self,
        project_id: UUID,
        output_id: UUID,
        node_id: str,
        node_data: dict[str, Any],
        existing_children: list[dict[str, Any]],
        session: AsyncSession,
        user_id: str | None = None,
    ) -> str:
        """Start expanding a node."""
        # Get output to verify existence
        output = await self.get_output(project_id, output_id, session, user_id)
        if not output:
            raise ValueError(f"Output not found: {output_id}")

        task_id = str(uuid4())
        project_id_str = str(project_id)

        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            project_id=project_id_str,
            output_id=output_id,
            output_type="expand_node",
        )

        async with self._lock:
            self._active_tasks[task_id] = task_info

        # Start async task
        asyncio_task = asyncio.create_task(
            self._run_expand_node(
                task_info=task_info,
                node_id=node_id,
                node_data=node_data,
                existing_children=existing_children,
            )
        )
        task_info.asyncio_task = asyncio_task

        return task_id

    async def start_synthesize_nodes(
        self,
        project_id: UUID,
        output_id: UUID,
        node_ids: list[str],
        node_data: list[dict[str, Any]],
        session: AsyncSession,
        mode: str = "group",
        user_id: str | None = None,
    ) -> str:
        """Start synthesizing nodes."""
        # Get output to verify existence
        output = await self.get_output(project_id, output_id, session, user_id)
        if not output:
            raise ValueError(f"Output not found: {output_id}")

        task_id = str(uuid4())
        project_id_str = str(project_id)

        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            project_id=project_id_str,
            output_id=output_id,
            output_type="synthesize_nodes",
        )

        async with self._lock:
            self._active_tasks[task_id] = task_info

        # Start async task
        asyncio_task = asyncio.create_task(
            self._run_synthesize_nodes(
                task_info=task_info,
                node_ids=node_ids,
                node_data=node_data,
                mode=mode,
            )
        )
        task_info.asyncio_task = asyncio_task

        return task_id

    async def cancel_task(
        self,
        project_id: str,
        task_id: str,
    ) -> bool:
        """Cancel a running task."""
        async with self._lock:
            task_info = self._active_tasks.get(task_id)

            if not task_info or task_info.project_id != project_id:
                return False

            if task_info.asyncio_task and not task_info.asyncio_task.done():
                task_info.asyncio_task.cancel()
                task_info.status = "cancelled"

            return True

    async def _run_generation(
        self,
        task_info: TaskInfo,
        source_ids: list[UUID],
        title: str | None,
        options: dict[str, Any],
    ) -> None:
        """
        Run the generation task.

        This runs in a separate asyncio task.
        """
        project_id = task_info.project_id
        task_id = task_info.task_id
        output_id = task_info.output_id

        # Acquire semaphore to limit concurrency
        semaphore = self._get_semaphore(project_id)

        try:
            async with semaphore:
                logger.info(f"[OutputService] Task acquired semaphore: {task_id}")

                # Get settings and create LLM service
                settings = get_settings()
                llm_service = OpenRouterLLMService(
                    api_key=settings.openrouter_api_key,
                    model=settings.llm_model,
                    site_name="Research Agent RAG",
                )

                # Load document content
                from research_agent.infrastructure.database.session import get_async_session

                async with get_async_session() as session:
                    # Branch based on output type
                    output_type = task_info.output_type

                    # Types that use node_data instead of documents
                    types_with_node_data = ("custom", "article", "action_list")
                    has_node_data = options and (options.get("node_data") or options.get("mode"))
                    is_type_with_node_data = output_type in types_with_node_data and has_node_data

                    if is_type_with_node_data:
                        # Use node_data from options instead of documents
                        node_data = options.get("node_data", [])
                        if not node_data:
                            raise ValueError(
                                "node_data is required for custom output type without documents"
                            )

                        # Convert node_data to document_content format for compatibility
                        document_content = "\n\n---\n\n".join(
                            [
                                f"# {nd.get('title', 'Node')}\n\n{nd.get('content', '')}"
                                for nd in node_data
                                if nd.get("content") or nd.get("title")
                            ]
                        )

                        if not document_content:
                            raise ValueError("No valid node content available in node_data")
                    else:
                        # Load resource content via ResourceResolver
                        document_content = await self._load_document_content(source_ids, session)

                    # Debug: Check loaded content
                    logger.info(
                        f"[OutputService] Loaded document_content: length={len(document_content) if document_content else 0}, "
                        f"has_TIME_markers={'[TIME:' in (document_content or '')}, "
                        f"has_PAGE_markers={'[PAGE:' in (document_content or '')}"
                    )

                    if not document_content:
                        raise ValueError("No document content available")

                    if output_type == "summary":
                        # Summary generation with Langfuse trace
                        await self._run_summary_generation(
                            task_id=task_id,
                            project_id=project_id,
                            output_id=output_id,
                            document_content=document_content,
                            title=title,
                            llm_service=llm_service.with_trace("summary-generation"),
                            session=session,
                        )
                    elif output_type == "flashcards":
                        # Flashcard generation with Langfuse trace
                        await self._run_flashcard_generation(
                            task_id=task_id,
                            project_id=project_id,
                            output_id=output_id,
                            document_content=document_content,
                            title=title,
                            llm_service=llm_service.with_trace("flashcard-generation"),
                            session=session,
                        )
                    elif output_type == "article":
                        # Article generation (Magic Cursor) with Langfuse trace
                        await self._run_article_generation(
                            task_id=task_id,
                            project_id=project_id,
                            output_id=output_id,
                            document_content=document_content,
                            title=title,
                            options=options,
                            llm_service=llm_service.with_trace("article-generation"),
                            session=session,
                        )
                    elif output_type == "action_list":
                        # Action list generation (Magic Cursor) with Langfuse trace
                        await self._run_action_list_generation(
                            task_id=task_id,
                            project_id=project_id,
                            output_id=output_id,
                            document_content=document_content,
                            title=title,
                            options=options,
                            llm_service=llm_service.with_trace("action-list-generation"),
                            session=session,
                        )
                    elif output_type == "custom" and options.get("mode"):
                        # Custom type with mode = synthesis with Langfuse trace
                        await self._run_custom_synthesis_generation(
                            task_id=task_id,
                            project_id=project_id,
                            output_id=output_id,
                            document_content=document_content,
                            title=title,
                            options=options,
                            llm_service=llm_service.with_trace("synthesis-generation"),
                            session=session,
                        )
                    else:
                        # Mindmap generation (default) with Langfuse trace
                        await self._run_mindmap_generation(
                            task_id=task_id,
                            project_id=project_id,
                            output_id=output_id,
                            document_content=document_content,
                            source_ids=source_ids,
                            title=title,
                            options=options,
                            llm_service=llm_service.with_trace("mindmap-generation"),
                            session=session,
                        )

        except asyncio.CancelledError:
            logger.info(f"[OutputService] Task cancelled: {task_id}")
            await output_notification_service.notify_generation_error(
                project_id=project_id,
                task_id=task_id,
                error_message="Generation cancelled",
            )

        except Exception as e:
            logger.error(f"[OutputService] Task failed: {task_id}, error={e}", exc_info=True)

            # Update output status
            try:
                from research_agent.infrastructure.database.session import get_async_session

                async with get_async_session() as session:
                    output_repo = SQLAlchemyOutputRepository(session)
                    output = await output_repo.find_by_id(output_id)
                    if output:
                        output.mark_error(str(e))
                        await output_repo.update(output)
            except Exception as update_error:
                logger.error(f"[OutputService] Failed to update error status: {update_error}")

            # Notify error
            await output_notification_service.notify_generation_error(
                project_id=project_id,
                task_id=task_id,
                error_message=str(e),
            )

        finally:
            # Clean up task
            async with self._lock:
                self._active_tasks.pop(task_id, None)

            output_notification_service.cleanup_task(task_id)

    async def _run_mindmap_generation(
        self,
        task_id: str,
        project_id: str,
        output_id: UUID,
        document_content: str,
        source_ids: list[UUID],
        title: str | None,
        options: dict[str, Any],
        llm_service: OpenRouterLLMService,
        session: AsyncSession,
    ) -> None:
        """Run mindmap generation using 2-phase direct generation algorithm.

        Uses the new simplified algorithm:
        1. Direct Generation - Single LLM call generates entire mindmap
        2. Refinement - Single LLM call cleans up duplicates

        Backend returns markdown; frontend parses to nodes/edges.
        """
        from research_agent.application.graphs.mindmap_graph import _parse_markdown_to_nodes
        from research_agent.domain.skills.mindmap_skill import SRP_SKILL

        # Prepare page-annotated content for source references
        annotated_content = await self._load_page_annotated_content(
            source_ids, session, document_content
        )

        # Create agent with new algorithm settings
        agent = MindmapAgent(
            llm_service=llm_service,
            max_depth=options.get("max_depth", 3),  # Default to 3 for new algorithm
            language=options.get("language", "zh"),  # Default to Chinese
            skills=options.get("skills", [SRP_SKILL]),
        )

        # Run generation and stream events
        mindmap_data = MindmapData()
        markdown_content: str | None = None
        document_id_from_event: str | None = None

        # Get the first source ID for source references
        primary_document_id = str(source_ids[0]) if source_ids else None

        async for event in agent.generate(
            document_content=annotated_content,
            document_title=title or "Document",
            document_id=primary_document_id,
            language=options.get("language", "zh"),
            **{k: v for k, v in options.items() if k not in ("language",)},
        ):
            # Check if task was cancelled
            if task_id not in self._active_tasks:
                logger.info(f"[OutputService] Task cancelled: {task_id}")
                return

            # Stream event to clients (frontend will parse markdown)
            await output_notification_service.notify_event(
                project_id=project_id,
                task_id=task_id,
                event=event,
            )

            # Capture markdown from GENERATION_COMPLETE for DB storage
            if event.type == OutputEventType.GENERATION_COMPLETE:
                markdown_content = event.markdown_content
                document_id_from_event = event.document_id

        # Parse markdown to nodes/edges for database storage
        if markdown_content:
            nodes, edges, root_id = _parse_markdown_to_nodes(
                markdown_content, document_id_from_event or primary_document_id
            )
            for node_data in nodes.values():
                node = MindmapNode.from_dict(node_data)
                mindmap_data.add_node(node)
            for edge_data in edges:
                edge = MindmapEdge.from_dict(edge_data)
                mindmap_data.add_edge(edge)
            if root_id:
                mindmap_data.root_id = root_id

        # Save final result
        output_repo = SQLAlchemyOutputRepository(session)
        output = await output_repo.find_by_id(output_id)
        if output:
            output.mark_complete(mindmap_data.to_dict())
            await output_repo.update(output)

        # Note: Don't call notify_generation_complete here!
        # The GENERATION_COMPLETE event with markdownContent was already sent
        # via notify_event in the loop above. Sending another one without
        # markdownContent would cause the frontend to lose the parsed data.

        logger.info(
            f"[OutputService] Mindmap task complete: {task_id}, nodes={len(mindmap_data.nodes)}"
        )

    async def _run_custom_synthesis_generation(
        self,
        task_id: str,
        project_id: str,
        output_id: UUID,
        document_content: str,
        title: str | None,
        options: dict[str, Any],
        llm_service: OpenRouterLLMService,
        session: AsyncSession,
    ) -> None:
        """Run custom synthesis generation from canvas nodes."""
        from research_agent.domain.agents.synthesis_agent import SynthesisAgent

        mode = options.get("mode", "connect")
        node_data = options.get("node_data", [])

        # Extract content from node_data (document_content is already formatted from node_data)
        # Split by "---" separator to get individual node contents
        node_contents = [
            content.strip() for content in document_content.split("\n\n---\n\n") if content.strip()
        ]

        if len(node_contents) < 2:
            raise ValueError("At least 2 nodes required for synthesis")

        # Create agent
        agent = SynthesisAgent(llm_service=llm_service)

        # Initialize mindmap data for storing result
        mindmap_data = MindmapData()

        # Run synthesis and stream events
        async for event in agent.synthesize(
            input_contents=node_contents,
            source_ids=[nd.get("id", "") for nd in node_data if nd.get("id")],
            mode=mode,
        ):
            # Check if task was cancelled
            if task_id not in self._active_tasks:
                logger.info(f"[OutputService] Task cancelled: {task_id}")
                return

            # Stream event to clients
            await output_notification_service.notify_event(
                project_id=project_id,
                task_id=task_id,
                event=event,
            )

            # Collect data for storage
            if event.type == OutputEventType.NODE_ADDED and event.node_data:
                node = MindmapNode.from_dict(event.node_data)
                mindmap_data.add_node(node)

        # Save final result
        output_repo = SQLAlchemyOutputRepository(session)
        output = await output_repo.find_by_id(output_id)
        if output:
            output.mark_complete(mindmap_data.to_dict())
            await output_repo.update(output)

        # Notify completion
        await output_notification_service.notify_generation_complete(
            project_id=project_id,
            task_id=task_id,
            output_id=str(output_id),
            message=f"Synthesis complete with {len(mindmap_data.nodes)} nodes",
        )

        logger.info(
            f"[OutputService] Custom synthesis task complete: {task_id}, nodes={len(mindmap_data.nodes)}"
        )

    async def _run_summary_generation(
        self,
        task_id: str,
        project_id: str,
        output_id: UUID,
        document_content: str,
        title: str | None,
        llm_service: OpenRouterLLMService,
        session: AsyncSession,
    ) -> None:
        """Run summary generation."""
        # Create agent
        agent = SummaryAgent(llm_service=llm_service)

        # Run generation and stream events
        summary_data: SummaryData | None = None

        async for event in agent.generate(
            document_content=document_content,
            document_title=title or "Document",
        ):
            # Check if task was cancelled
            if task_id not in self._active_tasks:
                logger.info(f"[OutputService] Task cancelled: {task_id}")
                return

            # Stream event to clients
            await output_notification_service.notify_event(
                project_id=project_id,
                task_id=task_id,
                event=event,
            )

            # Capture final summary data from GENERATION_COMPLETE event
            if event.type == OutputEventType.GENERATION_COMPLETE and event.node_data:
                summary_data = SummaryData.from_dict(event.node_data)

        # Save final result
        if summary_data:
            output_repo = SQLAlchemyOutputRepository(session)
            output = await output_repo.find_by_id(output_id)
            if output:
                output.mark_complete(summary_data.to_dict())
                await output_repo.update(output)

            # Notify completion
            await output_notification_service.notify_generation_complete(
                project_id=project_id,
                task_id=task_id,
                output_id=str(output_id),
                message=f"Generated summary with {len(summary_data.key_findings)} key findings",
            )

            logger.info(
                f"[OutputService] Summary task complete: {task_id}, "
                f"key_findings={len(summary_data.key_findings)}"
            )
        else:
            logger.error(f"[OutputService] Summary generation returned no data: {task_id}")

    async def _run_flashcard_generation(
        self,
        task_id: str,
        project_id: str,
        output_id: UUID,
        document_content: str,
        title: str | None,
        llm_service: OpenRouterLLMService,
        session: AsyncSession,
    ) -> None:
        """Run flashcard generation."""
        # Create agent
        agent = FlashcardAgent(llm_service=llm_service)

        # Run generation and stream events
        flashcard_data: FlashcardData | None = None

        async for event in agent.generate(
            document_content=document_content,
            document_title=title or "Document",
        ):
            # Check if task was cancelled
            if task_id not in self._active_tasks:
                logger.info(f"[OutputService] Task cancelled: {task_id}")
                return

            # Stream event to clients
            await output_notification_service.notify_event(
                project_id=project_id,
                task_id=task_id,
                event=event,
            )

            # Capture final flashcard data from GENERATION_COMPLETE event
            if event.type == OutputEventType.GENERATION_COMPLETE and event.node_data:
                flashcard_data = FlashcardData.from_dict(event.node_data)

        # Save final result
        if flashcard_data:
            output_repo = SQLAlchemyOutputRepository(session)
            output = await output_repo.find_by_id(output_id)
            if output:
                output.mark_complete(flashcard_data.to_dict())
                await output_repo.update(output)

            # Notify completion
            await output_notification_service.notify_generation_complete(
                project_id=project_id,
                task_id=task_id,
                output_id=str(output_id),
                message=f"Generated {len(flashcard_data.cards)} flashcards",
            )

            logger.info(
                f"[OutputService] Flashcard task complete: {task_id}, "
                f"cards={len(flashcard_data.cards)}"
            )
        else:
            logger.error(f"[OutputService] Flashcard generation returned no data: {task_id}")

    async def _run_article_generation(
        self,
        task_id: str,
        project_id: str,
        output_id: UUID,
        document_content: str,
        title: str | None,
        options: dict[str, Any],
        llm_service: OpenRouterLLMService,
        session: AsyncSession,
    ) -> None:
        """Run article generation (Magic Cursor: Draft Article)."""
        node_data = options.get("node_data", [])
        snapshot_context = options.get("snapshot_context")

        # Create agent
        agent = ArticleAgent(
            llm_service=llm_service,
            skills=options.get("skills", []),
        )

        # Run generation and stream events
        article_data: ArticleData | None = None

        async for event in agent.generate(
            document_content=document_content,
            document_title=title or "Generated Article",
            node_data=node_data,
            snapshot_context=snapshot_context,
        ):
            # Check if task was cancelled
            if task_id not in self._active_tasks:
                logger.info(f"[OutputService] Task cancelled: {task_id}")
                return

            # Stream event to clients
            await output_notification_service.notify_event(
                project_id=project_id,
                task_id=task_id,
                event=event,
            )

            # Capture final article data from GENERATION_COMPLETE event
            if event.type == OutputEventType.GENERATION_COMPLETE and event.node_data:
                article_data = ArticleData.from_dict(event.node_data)

        # Save final result
        if article_data:
            output_repo = SQLAlchemyOutputRepository(session)
            output = await output_repo.find_by_id(output_id)
            if output:
                output.mark_complete(article_data.to_dict())
                await output_repo.update(output)

            # Notify completion
            await output_notification_service.notify_generation_complete(
                project_id=project_id,
                task_id=task_id,
                output_id=str(output_id),
                message=f"Generated article with {len(article_data.sections)} sections",
            )

            logger.info(
                f"[OutputService] Article task complete: {task_id}, "
                f"sections={len(article_data.sections)}"
            )
        else:
            logger.error(f"[OutputService] Article generation returned no data: {task_id}")

    async def _run_action_list_generation(
        self,
        task_id: str,
        project_id: str,
        output_id: UUID,
        document_content: str,
        title: str | None,
        options: dict[str, Any],
        llm_service: OpenRouterLLMService,
        session: AsyncSession,
    ) -> None:
        """Run action list generation (Magic Cursor: Action List)."""
        node_data = options.get("node_data", [])
        snapshot_context = options.get("snapshot_context")

        # Create agent
        agent = ActionListAgent(
            llm_service=llm_service,
            skills=options.get("skills", []),
        )

        # Run generation and stream events
        action_list_data: ActionListData | None = None

        async for event in agent.generate(
            document_content=document_content,
            document_title=title or "Action Items",
            node_data=node_data,
            snapshot_context=snapshot_context,
        ):
            # Check if task was cancelled
            if task_id not in self._active_tasks:
                logger.info(f"[OutputService] Task cancelled: {task_id}")
                return

            # Stream event to clients
            await output_notification_service.notify_event(
                project_id=project_id,
                task_id=task_id,
                event=event,
            )

            # Capture final action list data from GENERATION_COMPLETE event
            if event.type == OutputEventType.GENERATION_COMPLETE and event.node_data:
                action_list_data = ActionListData.from_dict(event.node_data)

        # Save final result
        if action_list_data:
            output_repo = SQLAlchemyOutputRepository(session)
            output = await output_repo.find_by_id(output_id)
            if output:
                output.mark_complete(action_list_data.to_dict())
                await output_repo.update(output)

            # Notify completion
            await output_notification_service.notify_generation_complete(
                project_id=project_id,
                task_id=task_id,
                output_id=str(output_id),
                message=f"Extracted {len(action_list_data.items)} action items",
            )

            logger.info(
                f"[OutputService] Action list task complete: {task_id}, "
                f"items={len(action_list_data.items)}"
            )
        else:
            logger.error(f"[OutputService] Action list generation returned no data: {task_id}")

    async def _load_document_content(
        self,
        source_ids: list[UUID],
        session: AsyncSession,
    ) -> str:
        """
        Load and combine content from documents and URL contents.

        Uses ResourceResolver for unified content loading across all resource types.
        """
        if not source_ids:
            return ""

        # Use ResourceResolver for unified content loading
        resolver = ResourceResolver(session)
        resources = await resolver.resolve_many(source_ids)

        content_parts = []
        for resource in resources:
            content_len = len(resource.content) if resource.content else 0
            transcript_source = resource.metadata.get("transcript_source", "unknown")
            logger.info(
                f"[OutputService] Loaded {resource.type.value} ({resource.platform}): "
                f"{resource.title[:50]}... ({content_len} chars, source={transcript_source})"
            )

            # Note: Video transcription is now handled at upload time in YouTubeExtractor
            # Videos without transcripts will have empty content, which is expected for
            # videos that are too long or failed transcription

            # Use existing content
            formatted = resource.get_formatted_content()
            if formatted:
                content_parts.append(formatted)

        return "\n\n---\n\n".join(content_parts)

    async def _load_page_annotated_content(
        self,
        source_ids: list[UUID],
        session: AsyncSession,
        fallback_content: str,
    ) -> str:
        """
        Load document content with page annotations for source references.

        Attempts to load document chunks (which have page_number) and annotate
        the content with [PAGE:X] markers. For other resources (videos, etc.)
        it uses the standard formatted content. Ensure no content is lost
        even if mixed sources are used.

        Args:
            source_ids: List of source UUIDs (documents or URL contents)
            session: Database session
            fallback_content: Content to use if loading fails completely

        Returns:
            Page-annotated and combined content string
        """
        if not source_ids:
            return fallback_content

        try:
            from sqlalchemy import select

            from research_agent.infrastructure.database.models import ResourceChunkModel

            # Use ResourceResolver to get all resources in order
            resolver = ResourceResolver(session)
            resources = await resolver.resolve_many(source_ids)

            annotated_parts = []

            for resource in resources:
                source_id = resource.id
                # Check for chunks (primarily for documents)
                stmt = (
                    select(ResourceChunkModel)
                    .where(ResourceChunkModel.resource_id == source_id)
                    .where(ResourceChunkModel.resource_type == "document")
                    .order_by(ResourceChunkModel.chunk_index)
                )
                result = await session.execute(stmt)
                chunks = result.scalars().all()

                if chunks:
                    # Group chunks by page number (from metadata)
                    pages: dict[int, list[str]] = {}
                    for chunk in chunks:
                        page_num = (
                            chunk.chunk_metadata.get("page_number", 1)
                            if chunk.chunk_metadata
                            else 1
                        )
                        if page_num not in pages:
                            pages[page_num] = []
                        pages[page_num].append(chunk.content)

                    # Build annotated content for this PDF
                    pdf_annotated = []
                    for page_num in sorted(pages.keys()):
                        page_content = "\n".join(pages[page_num])
                        pdf_annotated.append(f"[PAGE:{page_num}]\n{page_content}")

                    annotated_parts.append("\n\n".join(pdf_annotated))
                else:
                    # No chunks (Video, WebPage, or Document without chunks)
                    # Use formatted content from Resource
                    formatted = resource.get_formatted_content()
                    if formatted:
                        annotated_parts.append(formatted)

            if annotated_parts:
                # Combine all sources with the standard separator
                annotated_content = "\n\n---\n\n".join(annotated_parts)
                logger.info(
                    f"[OutputService] Created combined/annotated content: "
                    f"{len(annotated_parts)} sources, {len(annotated_content)} chars"
                )
                return annotated_content

            # No parts found, use fallback
            return fallback_content

        except Exception as e:
            logger.warning(f"[OutputService] Failed to load page-annotated content: {e}")
            return fallback_content

    async def _run_expand_node(
        self,
        task_info: TaskInfo,
        output: Output,
        node_id: str,
        node_data: dict[str, Any],
        existing_children: list[dict[str, Any]],
        document_content: str,
    ) -> None:
        """Run the expand node task."""
        project_id = task_info.project_id
        task_id = task_info.task_id
        output_id = task_info.output_id

        try:
            settings = get_settings()
            llm_service = OpenRouterLLMService(
                api_key=settings.openrouter_api_key,
                model=settings.llm_model,
                site_name="Research Agent RAG",
            )

            agent = MindmapAgent(llm_service=llm_service)

            # Get existing mindmap data
            mindmap_data = output.get_mindmap_data() or MindmapData()

            async for event in agent.expand_node(
                node_id=node_id,
                node_data=node_data,
                existing_children=existing_children,
                document_content=document_content,
            ):
                if task_id not in self._active_tasks:
                    return

                await output_notification_service.notify_event(
                    project_id=project_id,
                    task_id=task_id,
                    event=event,
                )

                # Collect new nodes/edges
                if event.type == OutputEventType.NODE_ADDED and event.node_data:
                    node = MindmapNode.from_dict(event.node_data)
                    mindmap_data.add_node(node)

                if event.type == OutputEventType.EDGE_ADDED and event.edge_data:
                    edge = MindmapEdge.from_dict(event.edge_data)
                    mindmap_data.add_edge(edge)

            # Update output with new nodes
            from research_agent.infrastructure.database.session import get_async_session

            async with get_async_session() as session:
                output_repo = SQLAlchemyOutputRepository(session)
                output_updated = await output_repo.find_by_id(output_id)
                if output_updated:
                    output_updated.data = mindmap_data.to_dict()
                    await output_repo.update(output_updated)

        except Exception as e:
            logger.error(f"[OutputService] Expand failed: {e}", exc_info=True)
            await output_notification_service.notify_generation_error(
                project_id=project_id,
                task_id=task_id,
                error_message=str(e),
            )

        finally:
            async with self._lock:
                self._active_tasks.pop(task_id, None)
            output_notification_service.cleanup_task(task_id)

    def get_active_task_count(self, project_id: str) -> int:
        """Get number of active tasks for a project."""
        return sum(1 for t in self._active_tasks.values() if t.project_id == project_id)

    def _extract_node_contents(
        self,
        output: Output,
        node_ids: list[str],
    ) -> list[str]:
        """Extract content from nodes in the output data."""
        contents = []
        data = output.data or {}
        nodes = data.get("nodes", [])

        node_map = {n.get("id"): n for n in nodes}

        for node_id in node_ids:
            node = node_map.get(node_id)
            if node:
                # Combine label and content for synthesis
                label = node.get("label", "")
                content = node.get("content", "")
                combined = f"{label}\n{content}".strip()
                if combined:
                    contents.append(combined)

        return contents

    async def _run_synthesize_nodes(
        self,
        task_info: TaskInfo,
        output: Output,
        node_ids: list[str],
        node_contents: list[str],
        mode: str,
    ) -> None:
        """Run the synthesis task."""
        from research_agent.domain.agents.synthesis_agent import SynthesisAgent

        project_id = task_info.project_id
        task_id = task_info.task_id
        output_id = task_info.output_id

        try:
            settings = get_settings()
            llm_service = OpenRouterLLMService(
                api_key=settings.openrouter_api_key,
                model=settings.llm_model,
                site_name="Research Agent RAG",
            )

            agent = SynthesisAgent(llm_service=llm_service)

            # Get existing mindmap data
            mindmap_data = output.get_mindmap_data() or MindmapData()

            async for event in agent.synthesize(
                input_contents=node_contents,
                source_ids=node_ids,
                mode=mode,
            ):
                if task_id not in self._active_tasks:
                    return

                await output_notification_service.notify_event(
                    project_id=project_id,
                    task_id=task_id,
                    event=event,
                )

                # Add synthesized node to mindmap
                if event.type == OutputEventType.NODE_ADDED and event.node_data:
                    node = MindmapNode.from_dict(event.node_data)
                    mindmap_data.add_node(node)

            # Update output with new synthesized node
            from research_agent.infrastructure.database.session import get_async_session

            async with get_async_session() as session:
                output_repo = SQLAlchemyOutputRepository(session)
                output_updated = await output_repo.find_by_id(output_id)
                if output_updated:
                    output_updated.data = mindmap_data.to_dict()
                    await output_repo.update(output_updated)

        except Exception as e:
            logger.error(f"[OutputService] Synthesis failed: {e}", exc_info=True)
            await output_notification_service.notify_generation_error(
                project_id=project_id,
                task_id=task_id,
                error_message=str(e),
            )

        finally:
            async with self._lock:
                self._active_tasks.pop(task_id, None)
            output_notification_service.cleanup_task(task_id)


# Singleton instance
output_generation_service = OutputGenerationService()
