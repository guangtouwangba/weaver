"""
ContextEngine - Context Aggregation Engine.

Responsible for collecting and aggregating context required for RAG from multiple sources:
1. Explicitly passed context_nodes (in-memory node data)
2. context_node_ids (requires Canvas database query)
3. context_url_ids (retrieve URL content via ResourceResolver)
4. Entity state in history messages (replay entity state)
"""

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.shared.utils.logger import logger

from .models import ContextRefs, ResolvedContext


class ContextEngine:
    """
    Context Aggregation Engine.

    Usage:
        engine = ContextEngine(session)
        ctx = await engine.resolve(
            project_id=project_id,
            context_nodes=input.context_nodes,
            context_node_ids=input.context_node_ids,
            context_url_ids=input.context_url_ids,
            chat_messages=messages,  # History messages
        )
    """

    # Truncation length for long content
    MAX_CONTENT_LENGTH = 50000

    def __init__(self, session: AsyncSession):
        """
        Initialize ContextEngine.

        Args:
            session: Database session, used to query Canvas and URL content
        """
        self._session = session

    async def _rollback_safely(self) -> None:
        try:
            await self._session.rollback()
        except Exception:
            return

    async def _ensure_clean_transaction(self) -> None:
        """
        Ensure the session is in a clean transaction state.
        Rollback if there's a failed transaction.

        This prevents InFailedSQLTransactionError by detecting when a previous
        SQL statement has failed and the transaction needs to be rolled back.
        """
        try:
            # Check if connection is in a failed transaction by attempting a simple query
            # If it fails with InFailedSQLTransactionError, we need to rollback
            await self._session.execute(text("SELECT 1"))
        except DBAPIError as e:
            if "InFailedSQLTransactionError" in str(e) or "current transaction is aborted" in str(
                e
            ):
                logger.warning("[ContextEngine] Detected failed transaction state, rolling back...")
                await self._session.rollback()
            else:
                raise

    async def resolve(
        self,
        project_id: UUID,
        context_nodes: list[dict[str, Any]] | None = None,
        context_node_ids: list[str] | None = None,
        context_url_ids: list[str] | None = None,
        chat_messages: list[Any] | None = None,
        user_id: str | None = None,
    ) -> ResolvedContext:
        """
        Resolve and aggregate all contexts.

        Processing order:
        1. Build context_refs (for saving to user message)
        2. Reconstruct entity state from history
        3. Merge new attachments from current request into entity state
        4. Retrieve Canvas node content
        5. Retrieve URL content
        6. Merge all text contexts
        7. Determine default video source ID

        Args:
            project_id: Project ID
            context_nodes: Directly passed node data (preferred)
            context_node_ids: List of Canvas node IDs (requires DB query)
            context_url_ids: List of URL content IDs
            chat_messages: List of history messages (used to reconstruct entity state)
            user_id: Optional user ID for data isolation

        Returns:
            ResolvedContext: Object containing all aggregated contexts
        """
        # Step 1: Build context_refs
        context_refs = await self._build_context_refs(
            context_url_ids=context_url_ids,
            context_node_ids=context_node_ids,
            context_nodes=context_nodes,
        )

        # Step 2: Reconstruct entity state from history
        active_entities, current_focus = self._replay_entity_state(chat_messages or [])

        # Step 3: Merge new attachments from current request
        active_entities, current_focus = self._merge_current_attachments(
            context_refs=context_refs,
            active_entities=active_entities,
            current_focus=current_focus,
        )

        # Step 4: Retrieve Canvas node content
        canvas_context, canvas_node_count = await self._resolve_canvas_context(
            project_id=project_id,
            context_nodes=context_nodes,
            context_node_ids=context_node_ids,
            user_id=user_id,
        )

        # Step 5: Retrieve URL content
        url_context, url_count = await self._resolve_url_context(context_url_ids=context_url_ids)

        # Step 6: Merge text contexts
        combined_context = self._merge_text_contexts(canvas_context, url_context)

        # Step 7: Determine default video source ID
        default_video_id = self._resolve_default_video_source(
            current_focus=current_focus,
            context_refs=context_refs,
            active_entities=active_entities,
        )

        return ResolvedContext(
            combined_context=combined_context,
            active_entities=active_entities,
            current_focus=current_focus,
            context_refs_for_user_message=context_refs,
            default_video_source_id=default_video_id,
            canvas_node_count=canvas_node_count,
            url_resource_count=url_count,
        )

    # ========== Private Methods ==========

    async def _build_context_refs(
        self,
        context_url_ids: list[str] | None,
        context_node_ids: list[str] | None,
        context_nodes: list[dict[str, Any]] | None,
    ) -> ContextRefs:
        """
        Build context_refs for saving to user message.

        Only reference information (ID and title) is saved here, not the full content.
        Full content is retrieved in a separate step.
        """
        refs = ContextRefs()

        # Retrieve URL metadata
        if context_url_ids:
            refs.urls = await self._fetch_url_metadata(context_url_ids)

        # Save node IDs
        if context_node_ids:
            refs.node_ids = context_node_ids

        # Save node references (id and title only)
        if context_nodes:
            refs.nodes = [
                {"id": n.get("id"), "title": n.get("title", "Untitled")} for n in context_nodes
            ]

        return refs

    async def _fetch_url_metadata(self, url_ids: list[str]) -> list[dict[str, Any]]:
        """
        Retrieve metadata for URL content (excluding full content).

        Used for saving to user message to display citation sources in the frontend.
        """
        from research_agent.infrastructure.database.repositories.sqlalchemy_url_content_repo import (
            SQLAlchemyUrlContentRepository,
        )

        urls = []
        try:
            # Ensure clean transaction state before DB queries
            await self._ensure_clean_transaction()

            url_repo = SQLAlchemyUrlContentRepository(self._session)
            for url_id in url_ids:
                try:
                    url_content = await url_repo.get_by_id(UUID(url_id))
                    if url_content:
                        urls.append(
                            {
                                "id": str(url_content.id),
                                "title": url_content.title,
                                "platform": url_content.platform,
                                "url": url_content.url,
                            }
                        )
                except Exception as e:
                    logger.warning(f"Failed to fetch URL content {url_id}: {e}")
                    await self._rollback_safely()
                    urls.append({"id": url_id, "title": "URL"})
        except Exception as e:
            logger.error(f"Failed to fetch URL metadata: {e}")
            await self._rollback_safely()
            # Fallback: only save ID
            urls = [{"id": uid, "title": "URL"} for uid in url_ids]

        return urls

    def _replay_entity_state(
        self,
        chat_messages: list[Any],
    ) -> tuple[dict[str, dict[str, Any]], dict[str, Any] | None]:
        """
        Reconstruct entity state from history messages.

        Messages are passed in reverse chronological order (newest first), so they need to be reversed before processing.

        Args:
            chat_messages: List of history messages (newest first)

        Returns:
            tuple: (active_entities, current_focus)
        """
        active_entities: dict[str, dict[str, Any]] = {}
        current_focus: dict[str, Any] | None = None

        # messages are newest-first, allow replay from oldest-first
        for msg in reversed(chat_messages):
            if hasattr(msg, "context_refs") and msg.context_refs:
                if "entities" in msg.context_refs:
                    active_entities.update(msg.context_refs["entities"])
                if "focus" in msg.context_refs:
                    current_focus = msg.context_refs["focus"]

        return active_entities, current_focus

    def _merge_current_attachments(
        self,
        context_refs: ContextRefs,
        active_entities: dict[str, dict[str, Any]],
        current_focus: dict[str, Any] | None,
    ) -> tuple[dict[str, dict[str, Any]], dict[str, Any] | None]:
        """
        Merge new attachments from the current request into entity state.

        If the user attaches new URLs, they become active entities,
        and the focus shifts to the last attached resource.
        """
        if context_refs.urls:
            for url in context_refs.urls:
                platform = (url.get("platform") or "").lower()
                entity = {
                    "id": url["id"],
                    "type": "video" if "video" in platform else "document",
                    "title": url["title"],
                }
                active_entities[url["id"]] = entity
                current_focus = entity  # Focus shifts to new attachment

        return active_entities, current_focus

    async def _resolve_canvas_context(
        self,
        project_id: UUID,
        context_nodes: list[dict[str, Any]] | None,
        context_node_ids: list[str] | None,
        user_id: str | None = None,
    ) -> tuple[str, int]:
        """
        Retrieve text content of Canvas nodes.

        Priority:
        1. Use directly passed context_nodes (no DB query needed)
        2. Fallback to context_node_ids (requires DB query)

        Args:
            project_id: Project ID for canvas lookup
            context_nodes: Directly passed node data
            context_node_ids: List of node IDs to query
            user_id: Optional user ID for data isolation (reserved for future use)

        Returns:
            tuple: (canvas_context_text, node_count)
        """
        context_parts: list[str] = []

        # Priority 1: Use passed node data directly
        if context_nodes:
            for node in context_nodes:
                title = node.get("title", "Untitled")
                content = node.get("content", "")
                if content:
                    context_parts.append(f"## Node: {title}\n{content}")

        # Priority 2: Query node data from DB
        elif context_node_ids:
            try:
                from research_agent.infrastructure.database.repositories.sqlalchemy_canvas_repo import (
                    SQLAlchemyCanvasRepository,
                )

                # Ensure clean transaction state before DB query
                await self._ensure_clean_transaction()

                canvas_repo = SQLAlchemyCanvasRepository(self._session)
                canvas = await canvas_repo.find_by_project(project_id)

                if canvas:
                    for node_id in context_node_ids:
                        node = canvas.find_node(node_id)
                        if node:
                            context_parts.append(f"## Node: {node.title}\n{node.content}")
            except Exception as e:
                logger.error(f"[CanvasContext] Failed to retrieve canvas nodes: {e}", exc_info=True)
                await self._rollback_safely()

        if context_parts:
            return "\n\n".join(context_parts), len(context_parts)
        return "", 0

    async def _resolve_url_context(
        self,
        context_url_ids: list[str] | None,
    ) -> tuple[str, int]:
        """
        Retrieve full text content of URL resources.

        Use ResourceResolver to parse URL IDs and fetch content.
        Long content will be truncated to MAX_CONTENT_LENGTH.

        Returns:
            tuple: (url_context_text, url_count)
        """
        if not context_url_ids:
            return "", 0

        try:
            from research_agent.infrastructure.resource_resolver import ResourceResolver

            # Ensure clean transaction state before DB queries
            await self._ensure_clean_transaction()

            resolver = ResourceResolver(self._session)
            url_uuids = [UUID(uid) for uid in context_url_ids]
            resources = await resolver.resolve_many(url_uuids)

            url_context_parts: list[str] = []

            for resource in resources:
                if resource.has_content:
                    # Truncate content if too long
                    content = resource.display_content
                    if len(content) > self.MAX_CONTENT_LENGTH:
                        content = content[: self.MAX_CONTENT_LENGTH] + "\n\n[Content truncated...]"

                    # Build context with source info
                    source_info = (
                        f"Source: {resource.source_url}\n\n" if resource.source_url else ""
                    )

                    # Get header line
                    formatted = resource.get_formatted_content()
                    header_line = formatted.split("\n", 1)[0] if formatted else "Resource"

                    url_context_parts.append(
                        f"{header_line}\n" f"Source ID: {resource.id}\n" f"{source_info}{content}"
                    )

            if url_context_parts:
                return "\n\n---\n\n".join(url_context_parts), len(url_context_parts)

        except Exception as e:
            logger.error(f"[ResourceContext] Failed to retrieve URL content: {e}", exc_info=True)
            await self._rollback_safely()

        return "", 0

    def _merge_text_contexts(
        self,
        canvas_context: str,
        url_context: str,
    ) -> str:
        """
        Merge text contexts from Canvas and URL.

        If both exist, join with a separator.
        """
        if url_context:
            if canvas_context:
                return canvas_context + "\n\n---\n\n" + url_context
            return url_context
        return canvas_context

    def _resolve_default_video_source(
        self,
        current_focus: dict[str, Any] | None,
        context_refs: ContextRefs,
        active_entities: dict[str, dict[str, Any]],
    ) -> str | None:
        """
        Determine the default video source ID.

        Used for StreamingRefInjector to convert timestamps to video references.

        Priority:
        1. Current focus (if video)
        2. First attached URL
        3. Most recent video entity
        """
        # Priority 1: Current focus is video
        if current_focus and current_focus.get("type") == "video":
            source_id = current_focus.get("id")
            if isinstance(source_id, str):
                return source_id

        # Priority 2: First attached URL
        if context_refs.urls:
            source_id = context_refs.urls[0].get("id")
            if isinstance(source_id, str):
                return source_id

        # Priority 3: Most recent video entity
        for ent in reversed(list(active_entities.values())):
            if ent.get("type") == "video" and ent.get("id"):
                return ent["id"]

        return None
