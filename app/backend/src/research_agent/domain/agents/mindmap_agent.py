"""Mindmap generation agent using LangGraph workflow."""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from research_agent.application.graphs.mindmap_graph import MindmapState, mindmap_graph
from research_agent.domain.agents.base_agent import BaseOutputAgent, OutputEvent, OutputEventType
from research_agent.domain.entities.output import MindmapEdge, MindmapNode
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.infrastructure.llm.prompts import PromptLoader
from research_agent.shared.utils.logger import logger

# Layout constants for mindmap nodes
NODE_WIDTH = 200
NODE_HEIGHT = 80

# Template paths
MINDMAP_SYSTEM_TEMPLATE = "agents/mindmap/system.j2"

EXPAND_NODE_TEMPLATE = "agents/mindmap/expand.j2"


class MindmapAgent(BaseOutputAgent):
    """
    Agent for generating mindmaps from document content using LangGraph.

    Generation Strategy (via LangGraph workflow):
    1. Direct Generation - Single LLM call generates entire mindmap from full text
    2. Refinement - Single LLM call cleans up duplicates and improves structure
    3. Parse and stream - Convert markdown to nodes/edges and emit events

    This uses the new 2-phase direct generation algorithm that:
    - Leverages large context windows (up to 500K tokens)
    - Reduces LLM calls from N+log(N) to just 2
    - Produces better results by avoiding information loss from chunking

    The agent maintains backward compatibility with expand_node()
    for post-generation editing operations.
    """

    def __init__(
        self,
        llm_service: LLMService,
        max_depth: int = 3,
        max_tokens_per_request: int = 4000,
        language: str = "zh",
        skills: list[Any] = None,
    ):
        """
        Initialize the mindmap agent.

        Args:
            llm_service: LLM service for text generation
            max_depth: Maximum depth of the mindmap (default 3, used for hint in prompts)
            max_tokens_per_request: Maximum tokens per LLM request
            language: Prompt language ("zh", "en", or "auto")
            skills: Optional list of skills/tools to provide to the agent
        """
        super().__init__(llm_service, max_tokens_per_request)
        self._max_depth = max_depth
        self._language = language
        self._skills = skills or []
        self._prompt_loader = PromptLoader.get_instance()

    @property
    def output_type(self) -> str:
        """Return the output type."""
        return "mindmap"

    async def generate(
        self,
        document_content: str,
        document_title: str | None = None,
        document_id: str | None = None,
        max_depth: int | None = None,
        language: str | None = None,
        skills: list[Any] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[OutputEvent]:
        """
        Generate a mindmap from document content using LangGraph workflow.

        Uses the 2-phase direct generation algorithm:
        1. Direct Generation - Single LLM call generates entire mindmap
        2. Refinement - Single LLM call cleans up duplicates

        Args:
            document_content: Full document text or summary
            document_title: Optional document title
            document_id: Optional document ID for source references
            max_depth: Override default max depth (used as hint in prompts)
            language: Override prompt language ("zh", "en", or "auto")

        Yields:
            OutputEvent instances as generation progresses
        """
        depth = max_depth if max_depth is not None else self._max_depth
        lang = language if language is not None else self._language
        current_skills = skills if skills is not None else self._skills
        title = document_title or "Document"

        logger.info(f"[MindmapAgent] Starting direct generation: depth={depth}, language={lang}")

        # Create an async queue for events
        event_queue: asyncio.Queue[OutputEvent | None] = asyncio.Queue()

        async def emit_event(event: OutputEvent) -> None:
            """Callback to emit events to the queue."""
            await event_queue.put(event)

        # Initialize state for the graph (new 2-phase algorithm)
        initial_state: MindmapState = {
            "document_content": document_content,
            "document_title": title,
            "document_id": document_id,
            "max_depth": depth,
            "language": lang,
            "skills": current_skills,
            "markdown_output": "",
            "nodes": {},
            "edges": [],
            "root_id": None,
            "emit_event": emit_event,  # type: ignore[typeddict-item]
            "llm_service": self._llm,  # type: ignore[typeddict-item]
            "error": None,
        }

        async def run_graph() -> None:
            """Run the graph and signal completion."""
            try:
                await mindmap_graph.ainvoke(initial_state)
            except Exception as e:
                logger.error(f"[MindmapAgent] Graph execution failed: {e}", exc_info=True)
                await event_queue.put(
                    OutputEvent(
                        type=OutputEventType.GENERATION_ERROR,
                        error_message=f"Generation failed: {str(e)}",
                    )
                )
            finally:
                # Signal end of events
                await event_queue.put(None)

        # Start graph execution in background
        graph_task = asyncio.create_task(run_graph())

        # Yield events as they come
        try:
            while True:
                event = await event_queue.get()
                if event is None:
                    break
                yield event
        finally:
            # Ensure graph task completes
            if not graph_task.done():
                graph_task.cancel()
                try:
                    await graph_task
                except asyncio.CancelledError:
                    pass

    # =========================================================================
    # Node Editing Operations (unchanged - procedural)
    # =========================================================================

    async def expand_node(
        self,
        node_id: str,
        node_data: dict[str, Any],
        existing_children: list[dict[str, Any]],
        document_content: str,
    ) -> AsyncIterator[OutputEvent]:
        """
        Generate additional child nodes for a node.

        Args:
            node_id: ID of the node to expand
            node_data: Node data including label and content
            existing_children: Existing child nodes
            document_content: Document content for context

        Yields:
            NODE_ADDED and EDGE_ADDED events for new nodes
        """
        logger.info(f"[MindmapAgent] Expanding node: {node_id}")

        content = self._truncate_content(document_content, max_chars=8000)
        existing_labels = [c.get("label", "") for c in existing_children]

        prompt = self._prompt_loader.render(
            EXPAND_NODE_TEMPLATE,
            content=content,
            node_label=node_data.get("label", ""),
            node_content=node_data.get("content", ""),
            existing_children=", ".join(existing_labels) if existing_labels else "None",
            max_branches=3,  # Generate fewer branches for expansion
            skills=self._skills,
        )

        system_prompt = self._prompt_loader.render(
            MINDMAP_SYSTEM_TEMPLATE,
            skills=self._skills,
        )

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=prompt),
        ]

        try:
            yield self._emit_started("Expanding node")

            response = await self._llm.chat(messages)
            data = self._parse_json_response(response.content)

            if not data or "branches" not in data:
                yield self._emit_error("Failed to generate new branches")
                return

            # Get parent depth for new nodes
            parent_depth = node_data.get("depth", 0)
            new_level = parent_depth + 1

            branches = data["branches"][:3]

            for i, branch in enumerate(branches):
                new_node_id = f"node-{uuid4().hex[:8]}"
                new_node = MindmapNode(
                    id=new_node_id,
                    label=branch.get("label", f"Branch {i + 1}"),
                    content=branch.get("content", ""),
                    depth=new_level,
                    parent_id=node_id,
                    x=0,  # Frontend will apply layout
                    y=0,  # Frontend will apply layout
                    width=NODE_WIDTH,
                    height=NODE_HEIGHT,
                    color=self._get_color_for_level(new_level),
                    status="complete",
                )

                yield self._emit_node_added(new_node_id, new_node.to_dict())

                # Create edge
                edge_id = f"edge-{node_id}-{new_node_id}"
                edge = MindmapEdge(id=edge_id, source=node_id, target=new_node_id)
                yield self._emit_edge_added(edge_id, edge.to_dict())

            yield self._emit_complete(f"Added {len(branches)} new branches")

        except Exception as e:
            logger.error(f"[MindmapAgent] Expand failed: {e}")
            yield self._emit_error(f"Expansion failed: {str(e)}")

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _parse_json_response(self, response: str) -> dict[str, Any] | None:
        """Parse JSON from LLM response, handling markdown code blocks."""
        content = response.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            first_newline = content.find("\n")
            if first_newline != -1:
                content = content[first_newline + 1 :]
            if content.endswith("```"):
                content = content[:-3].strip()
            elif "```" in content:
                content = content[: content.rfind("```")].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"[MindmapAgent] JSON parse error: {e}, content: {content[:200]}")
            return None

    def _get_color_for_level(self, level: int) -> str:
        """Get color for a node based on its depth level."""
        colors = ["primary", "blue", "green", "orange", "purple", "pink"]
        return colors[level % len(colors)]
