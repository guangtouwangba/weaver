"""Service for managing output generation with concurrent task support."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.domain.agents.action_list_agent import ActionListAgent
from research_agent.domain.agents.article_agent import ArticleAgent
from research_agent.domain.agents.base_agent import OutputEvent, OutputEventType
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
from research_agent.infrastructure.database.repositories.sqlalchemy_document_repo import (
    SQLAlchemyDocumentRepository,
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
    asyncio_task: Optional[asyncio.Task] = None


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
        self._active_tasks: Dict[str, TaskInfo] = {}
        # Map: project_id -> Semaphore
        self._project_semaphores: Dict[str, asyncio.Semaphore] = {}
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
        document_ids: List[UUID],
        title: Optional[str],
        options: Dict[str, Any],
        session: AsyncSession,
        url_content_ids: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        """
        Start a new output generation task.

        Args:
            project_id: Project ID
            output_type: Type of output (mindmap, summary, etc.)
            document_ids: Source document IDs
            title: Optional title
            options: Generation options
            session: Database session
            url_content_ids: Optional list of URL content IDs (YouTube, web, etc.)

        Returns:
            Dict with task_id and output_id
        """
        url_content_ids = url_content_ids or []

        # Validate that we have some content source, except for types that use node_data
        # Custom, article, and action_list types can work with canvas node_data instead of documents
        types_with_node_data = ("custom", "article", "action_list")
        has_node_data = options and (options.get("node_data") or options.get("mode"))
        is_type_with_node_data = output_type in types_with_node_data and has_node_data
        has_content_source = document_ids or url_content_ids

        if not has_content_source and not is_type_with_node_data:
            raise ValueError(
                "At least one document ID or URL content ID is required for output generation"
            )

        task_id = str(uuid4())
        output_id = uuid4()
        project_id_str = str(project_id)

        logger.info(
            f"[OutputService] Starting generation: task={task_id}, "
            f"project={project_id}, type={output_type}, docs={len(document_ids)}, urls={len(url_content_ids)}"
        )

        # Create output record
        output_repo = SQLAlchemyOutputRepository(session)
        output = Output(
            id=output_id,
            project_id=project_id,
            output_type=OutputType(output_type),
            document_ids=document_ids,
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
                document_ids=document_ids,
                url_content_ids=url_content_ids,
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

    async def _run_generation(
        self,
        task_info: TaskInfo,
        document_ids: List[UUID],
        title: Optional[str],
        options: Dict[str, Any],
        url_content_ids: Optional[List[UUID]] = None,
    ) -> None:
        """
        Run the generation task.

        This runs in a separate asyncio task.
        """
        url_content_ids = url_content_ids or []
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
                        # Load document content (from both documents and URL contents)
                        document_content = await self._load_document_content(
                            document_ids, session, url_content_ids
                        )

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
                            document_ids=document_ids,
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
        document_ids: List[UUID],
        title: Optional[str],
        options: Dict[str, Any],
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

        # Prepare page-annotated content for source references
        annotated_content = await self._load_page_annotated_content(
            document_ids, session, document_content
        )

        # Create agent with new algorithm settings
        agent = MindmapAgent(
            llm_service=llm_service,
            max_depth=options.get("max_depth", 3),  # Default to 3 for new algorithm
            max_branches_per_node=options.get("max_branches", 4),  # Unused in new algorithm
            language=options.get("language", "zh"),  # Default to Chinese
        )

        # Run generation and stream events
        mindmap_data = MindmapData()
        markdown_content: Optional[str] = None
        document_id_from_event: Optional[str] = None

        # Get the first document ID for source references
        primary_document_id = str(document_ids[0]) if document_ids else None

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
        title: Optional[str],
        options: Dict[str, Any],
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
        title: Optional[str],
        llm_service: OpenRouterLLMService,
        session: AsyncSession,
    ) -> None:
        """Run summary generation."""
        # Create agent
        agent = SummaryAgent(llm_service=llm_service)

        # Run generation and stream events
        summary_data: Optional[SummaryData] = None

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
        title: Optional[str],
        llm_service: OpenRouterLLMService,
        session: AsyncSession,
    ) -> None:
        """Run flashcard generation."""
        # Create agent
        agent = FlashcardAgent(llm_service=llm_service)

        # Run generation and stream events
        flashcard_data: Optional[FlashcardData] = None

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
        title: Optional[str],
        options: Dict[str, Any],
        llm_service: OpenRouterLLMService,
        session: AsyncSession,
    ) -> None:
        """Run article generation (Magic Cursor: Draft Article)."""
        node_data = options.get("node_data", [])
        snapshot_context = options.get("snapshot_context")

        # Create agent
        agent = ArticleAgent(llm_service=llm_service)

        # Run generation and stream events
        article_data: Optional[ArticleData] = None

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
        title: Optional[str],
        options: Dict[str, Any],
        llm_service: OpenRouterLLMService,
        session: AsyncSession,
    ) -> None:
        """Run action list generation (Magic Cursor: Action List)."""
        node_data = options.get("node_data", [])
        snapshot_context = options.get("snapshot_context")

        # Create agent
        agent = ActionListAgent(llm_service=llm_service)

        # Run generation and stream events
        action_list_data: Optional[ActionListData] = None

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
        document_ids: List[UUID],
        session: AsyncSession,
        url_content_ids: Optional[List[UUID]] = None,
    ) -> str:
        """
        Load and combine content from documents and URL contents.

        Uses ResourceResolver for unified content loading across all resource types.
        """
        # Combine all resource IDs
        all_resource_ids = list(document_ids)
        if url_content_ids:
            all_resource_ids.extend(url_content_ids)

        if not all_resource_ids:
            return ""

        # Use ResourceResolver for unified content loading
        resolver = ResourceResolver(session)
        resources = await resolver.resolve_many(all_resource_ids)

        # Check for videos without content and transcribe if needed
        from research_agent.config import get_settings

        settings = get_settings()

        content_parts = []
        for resource in resources:
            content_len = len(resource.content) if resource.content else 0
            logger.info(
                f"[OutputService] Loaded {resource.type.value} ({resource.platform}): "
                f"{resource.title[:50]}... ({content_len} chars)"
            )

            # Check if this is a YouTube video without content
            if (
                resource.type.value == "video"
                and resource.platform == "youtube"
                and not resource.content
            ):
                # Get video_id from metadata
                video_id = resource.metadata.get("video_id")
                has_transcript = resource.metadata.get("has_transcript", False)

                if video_id and not has_transcript:
                    logger.info(
                        f"[OutputService] Video {video_id} has no transcript, "
                        "attempting Gemini audio transcription..."
                    )

                    try:
                        from research_agent.infrastructure.llm.gemini_audio import (
                            transcribe_youtube_video,
                        )

                        result = await transcribe_youtube_video(
                            video_id=video_id,
                            api_key=settings.openrouter_api_key,
                            max_duration_minutes=30,
                        )

                        if result.success and result.transcript:
                            logger.info(
                                f"[OutputService] Gemini transcription successful: "
                                f"{len(result.transcript)} chars"
                            )
                            # Use transcribed content
                            formatted = (
                                f"## Video (youtube): {resource.title}\n\n{result.transcript}"
                            )
                            content_parts.append(formatted)

                            # Update URL content in database with transcript
                            await self._update_url_content_transcript(
                                session, resource.id, result.transcript
                            )
                            continue
                        else:
                            logger.warning(
                                f"[OutputService] Gemini transcription failed: " f"{result.error}"
                            )
                    except Exception as e:
                        logger.error(
                            f"[OutputService] Audio transcription error: {e}", exc_info=True
                        )

            # Use existing content
            formatted = resource.get_formatted_content()
            if formatted:
                content_parts.append(formatted)

        return "\n\n---\n\n".join(content_parts)

    async def _load_page_annotated_content(
        self,
        document_ids: List[UUID],
        session: AsyncSession,
        fallback_content: str,
    ) -> str:
        """
        Load document content with page annotations for source references.

        Attempts to load document chunks (which have page_number) and annotate
        the content with [PAGE:X] markers. Falls back to raw content if chunks
        are not available.

        Args:
            document_ids: List of document UUIDs
            session: Database session
            fallback_content: Content to use if page annotation fails

        Returns:
            Page-annotated content string
        """
        if not document_ids:
            return fallback_content

        try:
            from sqlalchemy import select

            from research_agent.infrastructure.database.models import DocumentChunkModel

            annotated_parts = []

            for doc_id in document_ids:
                # Query chunks for this document, ordered by page_number and chunk_index
                stmt = (
                    select(DocumentChunkModel)
                    .where(DocumentChunkModel.document_id == doc_id)
                    .order_by(DocumentChunkModel.page_number, DocumentChunkModel.chunk_index)
                )
                result = await session.execute(stmt)
                chunks = result.scalars().all()

                if not chunks:
                    # No chunks, use fallback
                    logger.debug(f"[OutputService] No chunks found for document {doc_id}")
                    continue

                # Group chunks by page number
                pages: Dict[int, List[str]] = {}
                for chunk in chunks:
                    page_num = chunk.page_number or 1
                    if page_num not in pages:
                        pages[page_num] = []
                    pages[page_num].append(chunk.content)

                # Build annotated content
                for page_num in sorted(pages.keys()):
                    page_content = "\n".join(pages[page_num])
                    annotated_parts.append(f"[PAGE:{page_num}]\n{page_content}")

            if annotated_parts:
                annotated_content = "\n\n".join(annotated_parts)
                logger.info(
                    f"[OutputService] Created page-annotated content: "
                    f"{len(annotated_parts)} pages, {len(annotated_content)} chars"
                )
                return annotated_content

            # No annotated content, use fallback
            return fallback_content

        except Exception as e:
            logger.warning(f"[OutputService] Failed to load page-annotated content: {e}")
            return fallback_content

    async def _update_url_content_transcript(
        self,
        session: AsyncSession,
        url_content_id: UUID,
        transcript: str,
    ) -> None:
        """Update URL content record with Gemini-transcribed content.

        This caches the transcription result so it doesn't need to be
        re-transcribed on future requests.
        """
        try:
            from research_agent.infrastructure.database.models import UrlContentModel

            url_content = await session.get(UrlContentModel, url_content_id)
            if url_content:
                url_content.content = transcript

                # Update metadata to indicate transcription source
                meta_data = url_content.meta_data or {}
                meta_data["has_transcript"] = True
                meta_data["transcript_source"] = "gemini_audio"
                url_content.meta_data = meta_data

                await session.commit()
                logger.info(
                    f"[OutputService] Saved Gemini transcript for {url_content_id}: "
                    f"{len(transcript)} chars"
                )
        except Exception as e:
            logger.warning(f"[OutputService] Failed to save transcript: {e}")

    async def list_outputs(
        self,
        project_id: UUID,
        output_type: Optional[str],
        limit: int,
        offset: int,
        session: AsyncSession,
    ) -> Tuple[List[Output], int]:
        """List outputs for a project."""
        output_repo = SQLAlchemyOutputRepository(session)
        return await output_repo.find_by_project(
            project_id=project_id,
            output_type=output_type,
            limit=limit,
            offset=offset,
        )

    async def get_output(
        self,
        project_id: UUID,
        output_id: UUID,
        session: AsyncSession,
    ) -> Optional[Output]:
        """Get a specific output."""
        output_repo = SQLAlchemyOutputRepository(session)
        output = await output_repo.find_by_id(output_id)

        # Verify project ownership
        if output and output.project_id != project_id:
            return None

        return output

    async def delete_output(
        self,
        project_id: UUID,
        output_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Delete an output."""
        output_repo = SQLAlchemyOutputRepository(session)
        output = await output_repo.find_by_id(output_id)

        # Verify project ownership
        if not output or output.project_id != project_id:
            return False

        return await output_repo.delete(output_id)

    async def update_output(
        self,
        project_id: UUID,
        output_id: UUID,
        title: Optional[str],
        data: Optional[Dict[str, Any]],
        session: AsyncSession,
    ) -> Optional[Output]:
        """
        Update an existing output's title and/or data.

        Args:
            project_id: Project ID (for ownership verification)
            output_id: Output ID to update
            title: New title (if provided)
            data: New data blob (if provided)
            session: Database session

        Returns:
            Updated Output or None if not found / not authorized
        """
        output_repo = SQLAlchemyOutputRepository(session)
        output = await output_repo.find_by_id(output_id)

        # Verify project ownership
        if not output or output.project_id != project_id:
            return None

        # Build update dict
        update_data: Dict[str, Any] = {}
        if title is not None:
            update_data["title"] = title
        if data is not None:
            update_data["data"] = data

        if not update_data:
            return output  # Nothing to update

        updated = await output_repo.update(output_id, update_data)
        return updated

    async def start_explain_node(
        self,
        project_id: UUID,
        output_id: UUID,
        node_id: str,
        node_data: Dict[str, Any],
        session: AsyncSession,
    ) -> str:
        """
        Start explaining a node.

        Returns task_id for tracking via WebSocket.
        """
        task_id = str(uuid4())
        project_id_str = str(project_id)

        # Verify output exists
        output_repo = SQLAlchemyOutputRepository(session)
        output = await output_repo.find_by_id(output_id)
        if not output or output.project_id != project_id:
            raise ValueError("Output not found")

        # Get document content for context
        document_content = await self._load_document_content(output.document_ids, session)

        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            project_id=project_id_str,
            output_id=output_id,
            output_type="explain",
        )

        async with self._lock:
            self._active_tasks[task_id] = task_info

        # Start async task
        asyncio_task = asyncio.create_task(
            self._run_explain(
                task_info=task_info,
                node_id=node_id,
                node_data=node_data,
                document_content=document_content,
            )
        )
        task_info.asyncio_task = asyncio_task

        return task_id

    async def _run_explain(
        self,
        task_info: TaskInfo,
        node_id: str,
        node_data: Dict[str, Any],
        document_content: str,
    ) -> None:
        """Run the explain node task."""
        project_id = task_info.project_id
        task_id = task_info.task_id

        try:
            settings = get_settings()
            llm_service = OpenRouterLLMService(
                api_key=settings.openrouter_api_key,
                model=settings.llm_model,
                site_name="Research Agent RAG",
            )

            agent = MindmapAgent(llm_service=llm_service)

            async for event in agent.explain_node(
                node_id=node_id,
                node_data=node_data,
                document_content=document_content,
            ):
                if task_id not in self._active_tasks:
                    return

                await output_notification_service.notify_event(
                    project_id=project_id,
                    task_id=task_id,
                    event=event,
                )

        except Exception as e:
            logger.error(f"[OutputService] Explain failed: {e}", exc_info=True)
            await output_notification_service.notify_generation_error(
                project_id=project_id,
                task_id=task_id,
                error_message=str(e),
            )

        finally:
            async with self._lock:
                self._active_tasks.pop(task_id, None)
            output_notification_service.cleanup_task(task_id)

    async def explain_node_stream(
        self,
        project_id: UUID,
        output_id: UUID,
        node_id: str,
        node_data: Dict[str, Any],
        session: AsyncSession,
    ) -> AsyncIterator[str]:
        """
        Stream explanation tokens directly (for SSE).

        Alternative to WebSocket for simpler clients.
        """
        # Verify output exists
        output_repo = SQLAlchemyOutputRepository(session)
        output = await output_repo.find_by_id(output_id)
        if not output or output.project_id != project_id:
            raise ValueError("Output not found")

        # Get document content for context
        document_content = await self._load_document_content(output.document_ids, session)

        settings = get_settings()
        llm_service = OpenRouterLLMService(
            api_key=settings.openrouter_api_key,
            model=settings.llm_model,
            site_name="Research Agent RAG",
        )

        agent = MindmapAgent(llm_service=llm_service)

        async for event in agent.explain_node(
            node_id=node_id,
            node_data=node_data,
            document_content=document_content,
        ):
            if event.type == OutputEventType.TOKEN and event.token:
                yield event.token

    async def start_expand_node(
        self,
        project_id: UUID,
        output_id: UUID,
        node_id: str,
        node_data: Dict[str, Any],
        existing_children: List[Dict[str, Any]],
        session: AsyncSession,
    ) -> str:
        """
        Start expanding a node with additional children.

        Returns task_id for tracking via WebSocket.
        """
        task_id = str(uuid4())
        project_id_str = str(project_id)

        # Verify output exists
        output_repo = SQLAlchemyOutputRepository(session)
        output = await output_repo.find_by_id(output_id)
        if not output or output.project_id != project_id:
            raise ValueError("Output not found")

        # Get document content for context
        document_content = await self._load_document_content(output.document_ids, session)

        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            project_id=project_id_str,
            output_id=output_id,
            output_type="expand",
        )

        async with self._lock:
            self._active_tasks[task_id] = task_info

        # Start async task
        asyncio_task = asyncio.create_task(
            self._run_expand(
                task_info=task_info,
                output=output,
                node_id=node_id,
                node_data=node_data,
                existing_children=existing_children,
                document_content=document_content,
            )
        )
        task_info.asyncio_task = asyncio_task

        return task_id

    async def _run_expand(
        self,
        task_info: TaskInfo,
        output: Output,
        node_id: str,
        node_data: Dict[str, Any],
        existing_children: List[Dict[str, Any]],
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

    async def cancel_task(
        self,
        project_id: str,
        task_id: str,
    ) -> bool:
        """
        Cancel an ongoing task.

        Args:
            project_id: Project ID
            task_id: Task ID to cancel

        Returns:
            True if task was cancelled, False if not found
        """
        async with self._lock:
            task_info = self._active_tasks.get(task_id)

            if not task_info:
                return False

            # Verify project ownership
            if task_info.project_id != project_id:
                return False

            # Cancel the asyncio task
            if task_info.asyncio_task and not task_info.asyncio_task.done():
                task_info.asyncio_task.cancel()

            # Remove from active tasks
            self._active_tasks.pop(task_id, None)

        logger.info(f"[OutputService] Task cancelled: {task_id}")
        return True

    def get_active_task_count(self, project_id: str) -> int:
        """Get number of active tasks for a project."""
        return sum(1 for t in self._active_tasks.values() if t.project_id == project_id)

    async def start_synthesize_nodes(
        self,
        project_id: UUID,
        output_id: UUID,
        node_ids: List[str],
        session: AsyncSession,
        mode: str = "connect",
        node_data: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Start synthesizing multiple nodes into a consolidated insight.

        Args:
            project_id: Project ID
            output_id: Output ID (for context)
            node_ids: List of node IDs to synthesize
            session: Database session
            mode: Synthesis mode (connect, inspire, debate)
            node_data: Optional list of node content dicts (for canvas synthesis)

        Returns:
            task_id for tracking via WebSocket
        """
        from research_agent.domain.agents.synthesis_agent import SynthesisAgent

        task_id = str(uuid4())
        project_id_str = str(project_id)

        # Verify output exists
        output_repo = SQLAlchemyOutputRepository(session)
        output = await output_repo.find_by_id(output_id)
        if not output or output.project_id != project_id:
            raise ValueError("Output not found")

        # Extract node contents - prefer direct node_data if provided
        if node_data:
            # Direct canvas node content
            node_contents = []
            for nd in node_data:
                title = nd.get("title", "")
                content = nd.get("content", "")
                combined = f"{title}\n{content}".strip()
                if combined:
                    node_contents.append(combined)
        else:
            # Fall back to extracting from output's data (mindmap nodes)
            node_contents = self._extract_node_contents(output, node_ids)

        if len(node_contents) < 2:
            raise ValueError("At least 2 valid nodes required for synthesis")

        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            project_id=project_id_str,
            output_id=output_id,
            output_type="synthesis",
            # Store mode in task info if needed, or pass directly
        )

        async with self._lock:
            self._active_tasks[task_id] = task_info

        # Start async task
        asyncio_task = asyncio.create_task(
            self._run_synthesize(
                task_info=task_info,
                output=output,
                node_ids=node_ids,
                node_contents=node_contents,
                mode=mode,
            )
        )
        task_info.asyncio_task = asyncio_task

        return task_id

    def _extract_node_contents(
        self,
        output: Output,
        node_ids: List[str],
    ) -> List[str]:
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

    async def _run_synthesize(
        self,
        task_info: TaskInfo,
        output: Output,
        node_ids: List[str],
        node_contents: List[str],
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
