"""Service for managing output generation with concurrent task support."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.domain.agents.base_agent import OutputEvent, OutputEventType
from research_agent.domain.agents.flashcard_agent import FlashcardAgent
from research_agent.domain.agents.mindmap_agent import MindmapAgent
from research_agent.domain.agents.summary_agent import SummaryAgent
from research_agent.domain.entities.output import (
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

        Returns:
            Dict with task_id and output_id
        """
        task_id = str(uuid4())
        output_id = uuid4()
        project_id_str = str(project_id)

        logger.info(
            f"[OutputService] Starting generation: task={task_id}, "
            f"project={project_id}, type={output_type}"
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
                    document_content = await self._load_document_content(document_ids, session)

                    if not document_content:
                        raise ValueError("No document content available")

                    # Branch based on output type
                    output_type = task_info.output_type

                    if output_type == "summary":
                        # Summary generation
                        await self._run_summary_generation(
                            task_id=task_id,
                            project_id=project_id,
                            output_id=output_id,
                            document_content=document_content,
                            title=title,
                            llm_service=llm_service,
                            session=session,
                        )
                    elif output_type == "flashcards":
                        # Flashcard generation
                        await self._run_flashcard_generation(
                            task_id=task_id,
                            project_id=project_id,
                            output_id=output_id,
                            document_content=document_content,
                            title=title,
                            llm_service=llm_service,
                            session=session,
                        )
                    else:
                        # Mindmap generation (default)
                        await self._run_mindmap_generation(
                            task_id=task_id,
                            project_id=project_id,
                            output_id=output_id,
                            document_content=document_content,
                            title=title,
                            options=options,
                            llm_service=llm_service,
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
        title: Optional[str],
        options: Dict[str, Any],
        llm_service: OpenRouterLLMService,
        session: AsyncSession,
    ) -> None:
        """Run mindmap generation."""
        # Create agent
        # Default to conservative settings to prevent frontend freezing
        # max_depth=2, max_branches=4 → max ~21 nodes (1 + 4 + 16)
        agent = MindmapAgent(
            llm_service=llm_service,
            max_depth=options.get("max_depth", 2),
            max_branches_per_node=options.get("max_branches", 4),
        )

        # Run generation and stream events
        mindmap_data = MindmapData()

        async for event in agent.generate(
            document_content=document_content,
            document_title=title or "Document",
            **options,
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

            if event.type == OutputEventType.EDGE_ADDED and event.edge_data:
                edge = MindmapEdge.from_dict(event.edge_data)
                mindmap_data.add_edge(edge)

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
            message=f"Generated mindmap with {len(mindmap_data.nodes)} nodes",
        )

        logger.info(
            f"[OutputService] Mindmap task complete: {task_id}, " f"nodes={len(mindmap_data.nodes)}"
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

    async def _load_document_content(
        self,
        document_ids: List[UUID],
        session: AsyncSession,
    ) -> str:
        """Load and combine content from documents."""
        document_repo = SQLAlchemyDocumentRepository(session)
        contents: List[str] = []

        for doc_id in document_ids:
            document = await document_repo.find_by_id(doc_id)
            if not document:
                logger.warning(f"[OutputService] Document not found: {doc_id}")
                continue

            # Prefer full_content, fall back to summary
            if document.full_content:
                contents.append(f"# {document.original_filename}\n\n{document.full_content}")
            elif document.summary:
                contents.append(f"# {document.original_filename}\n\n{document.summary}")
            else:
                logger.warning(f"[OutputService] No content for document: {doc_id}")

        return "\n\n---\n\n".join(contents)

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


# Singleton instance
output_generation_service = OutputGenerationService()
