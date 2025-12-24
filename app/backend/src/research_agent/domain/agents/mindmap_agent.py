"""Mindmap generation agent."""

import json
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import uuid4

from research_agent.domain.agents.base_agent import BaseOutputAgent, OutputEvent, OutputEventType
from research_agent.domain.entities.output import MindmapData, MindmapEdge, MindmapNode
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.shared.utils.logger import logger

# Layout constants for mindmap nodes
NODE_WIDTH = 200
NODE_HEIGHT = 80
HORIZONTAL_SPACING = 280  # Space between levels
VERTICAL_SPACING = 120  # Space between siblings

# Prompts for mindmap generation
MINDMAP_SYSTEM_PROMPT = """You are an expert at analyzing documents and creating structured mindmaps.
Your task is to extract the key concepts and their hierarchical relationships from the given content.

IMPORTANT: You must respond with ONLY valid JSON, no other text or explanation.
"""

MINDMAP_ROOT_PROMPT = """Analyze the following document and identify the main topic/theme that should be the root of a mindmap.

Document Title: {title}

Document Content:
{content}

Respond with a JSON object containing:
{{
  "label": "Main topic label (brief, 3-5 words max)",
  "content": "A one-sentence summary of the main topic"
}}

Remember: Respond with ONLY the JSON object, nothing else."""

MINDMAP_BRANCHES_PROMPT = """Based on the document content and the current mindmap structure, generate the next level of branches.

Document Content:
{content}

Current Node: {current_node_label}
Current Node Content: {current_node_content}
Depth Level: {depth} (0=root, higher=more specific)

Generate {max_branches} key sub-topics or aspects that branch from "{current_node_label}".
Each branch should be distinct and cover different aspects.

Respond with a JSON object containing:
{{
  "branches": [
    {{
      "label": "Branch label (brief, 3-5 words max)",
      "content": "A brief explanation of this sub-topic"
    }}
  ]
}}

Remember: Respond with ONLY the JSON object, nothing else."""

EXPLAIN_NODE_PROMPT = """Explain the following concept in the context of the document.

Document Content:
{content}

Node to Explain: {node_label}
Node Description: {node_content}

Provide a clear, detailed explanation of this concept. Include:
1. What it means in the context of the document
2. Why it's important
3. How it relates to the overall topic

Keep your explanation concise but informative (2-3 paragraphs)."""

EXPAND_NODE_PROMPT = """Generate additional sub-topics for the following node.

Document Content:
{content}

Node to Expand: {node_label}
Node Description: {node_content}

Existing Children (avoid duplicating these):
{existing_children}

Generate {max_branches} new, distinct sub-topics that haven't been covered yet.

Respond with a JSON object containing:
{{
  "branches": [
    {{
      "label": "Branch label (brief, 3-5 words max)",
      "content": "A brief explanation of this sub-topic"
    }}
  ]
}}

Remember: Respond with ONLY the JSON object, nothing else."""


class MindmapAgent(BaseOutputAgent):
    """
    Agent for generating mindmaps from document content.

    Generation Strategy:
    1. Analyze document to extract main theme (root node)
    2. Generate Level 1 branches (main topics)
    3. For each branch, generate Level 2 sub-topics
    4. Continue until max_depth reached

    Each level is generated and streamed before proceeding to next.
    """

    def __init__(
        self,
        llm_service: LLMService,
        max_depth: int = 3,
        max_branches_per_node: int = 5,
        max_tokens_per_request: int = 4000,
    ):
        """
        Initialize the mindmap agent.

        Args:
            llm_service: LLM service for text generation
            max_depth: Maximum depth of the mindmap (0 = root only)
            max_branches_per_node: Maximum branches per node
            max_tokens_per_request: Maximum tokens per LLM request
        """
        super().__init__(llm_service, max_tokens_per_request)
        self._max_depth = max_depth
        self._max_branches = max_branches_per_node

    @property
    def output_type(self) -> str:
        """Return the output type."""
        return "mindmap"

    async def generate(
        self,
        document_content: str,
        document_title: Optional[str] = None,
        max_depth: Optional[int] = None,
        max_branches: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[OutputEvent]:
        """
        Generate a mindmap from document content.

        Args:
            document_content: Full document text or summary
            document_title: Optional document title
            max_depth: Override default max depth
            max_branches: Override default max branches per node

        Yields:
            OutputEvent instances as generation progresses
        """
        depth = max_depth if max_depth is not None else self._max_depth
        branches = max_branches if max_branches is not None else self._max_branches
        title = document_title or "Document"

        logger.info(f"[MindmapAgent] Starting generation: depth={depth}, branches={branches}")

        # Emit started event
        yield self._emit_started(f"Generating mindmap for: {title}")

        # Truncate content if needed
        content = self._truncate_content(document_content)

        try:
            # Initialize mindmap data
            mindmap = MindmapData()

            # Step 1: Generate root node
            yield self._emit_progress(0.1, current_level=0, total_levels=depth + 1, message="Generating root node")

            root_node = await self._generate_root_node(content, title)
            if not root_node:
                yield self._emit_error("Failed to generate root node")
                return

            mindmap.add_node(root_node)
            yield self._emit_node_added(root_node.id, root_node.to_dict())

            # Step 2: Generate branches level by level
            current_level_nodes = [root_node]

            for level in range(1, depth + 1):
                progress = 0.1 + (0.8 * level / depth)
                yield self._emit_progress(
                    progress,
                    current_level=level,
                    total_levels=depth + 1,
                    message=f"Generating level {level} branches",
                )

                next_level_nodes: List[MindmapNode] = []

                for parent_node in current_level_nodes:
                    # Generate branches for this parent
                    async for event in self._generate_branches(
                        content,
                        parent_node,
                        mindmap,
                        level,
                        branches,
                    ):
                        yield event

                        # Collect new nodes for next level
                        if event.type == OutputEventType.NODE_ADDED and event.node_data:
                            new_node = MindmapNode.from_dict(event.node_data)
                            next_level_nodes.append(new_node)

                yield self._emit_level_complete(level, depth + 1)
                current_level_nodes = next_level_nodes

                # Stop if no more nodes to expand
                if not current_level_nodes:
                    break

            # Step 3: Complete
            yield self._emit_progress(1.0, message="Mindmap generation complete")
            yield self._emit_complete(f"Generated mindmap with {len(mindmap.nodes)} nodes")

            logger.info(
                f"[MindmapAgent] Generation complete: {len(mindmap.nodes)} nodes, {len(mindmap.edges)} edges"
            )

        except Exception as e:
            logger.error(f"[MindmapAgent] Generation failed: {e}", exc_info=True)
            yield self._emit_error(f"Generation failed: {str(e)}")

    async def _generate_root_node(
        self,
        content: str,
        title: str,
    ) -> Optional[MindmapNode]:
        """Generate the root node of the mindmap."""
        prompt = MINDMAP_ROOT_PROMPT.format(title=title, content=content[:8000])

        messages = [
            ChatMessage(role="system", content=MINDMAP_SYSTEM_PROMPT),
            ChatMessage(role="user", content=prompt),
        ]

        try:
            response = await self._llm.chat(messages)
            data = self._parse_json_response(response.content)

            if not data or "label" not in data:
                logger.warning("[MindmapAgent] Invalid root node response")
                return None

            node_id = f"node-{uuid4().hex[:8]}"
            return MindmapNode(
                id=node_id,
                label=data["label"],
                content=data.get("content", ""),
                depth=0,
                parent_id=None,
                x=400,  # Center position
                y=300,
                width=NODE_WIDTH,
                height=NODE_HEIGHT,
                color="primary",
                status="complete",
            )

        except Exception as e:
            logger.error(f"[MindmapAgent] Failed to generate root: {e}")
            return None

    async def _generate_branches(
        self,
        content: str,
        parent_node: MindmapNode,
        mindmap: MindmapData,
        level: int,
        max_branches: int,
    ) -> AsyncIterator[OutputEvent]:
        """Generate branches for a parent node."""
        prompt = MINDMAP_BRANCHES_PROMPT.format(
            content=content[:6000],
            current_node_label=parent_node.label,
            current_node_content=parent_node.content,
            depth=level,
            max_branches=max_branches,
        )

        messages = [
            ChatMessage(role="system", content=MINDMAP_SYSTEM_PROMPT),
            ChatMessage(role="user", content=prompt),
        ]

        try:
            response = await self._llm.chat(messages)
            data = self._parse_json_response(response.content)

            if not data or "branches" not in data:
                logger.warning(f"[MindmapAgent] Invalid branches response for {parent_node.id}")
                return

            branches = data["branches"][:max_branches]

            # Calculate positions for child nodes
            positions = self._calculate_child_positions(parent_node, len(branches))

            for i, branch in enumerate(branches):
                # Emit node generating event
                node_id = f"node-{uuid4().hex[:8]}"
                yield self._emit_node_generating(node_id, {"label": branch.get("label", "")})

                # Create node
                x, y = positions[i]
                node = MindmapNode(
                    id=node_id,
                    label=branch.get("label", f"Branch {i + 1}"),
                    content=branch.get("content", ""),
                    depth=level,
                    parent_id=parent_node.id,
                    x=x,
                    y=y,
                    width=NODE_WIDTH,
                    height=NODE_HEIGHT,
                    color=self._get_color_for_level(level),
                    status="complete",
                )

                mindmap.add_node(node)
                yield self._emit_node_added(node_id, node.to_dict())

                # Create edge
                edge_id = f"edge-{parent_node.id}-{node_id}"
                edge = MindmapEdge(
                    id=edge_id,
                    source=parent_node.id,
                    target=node_id,
                    label="",
                )
                mindmap.add_edge(edge)
                yield self._emit_edge_added(edge_id, edge.to_dict())

        except Exception as e:
            logger.error(f"[MindmapAgent] Failed to generate branches: {e}")
            yield self._emit_error(f"Failed to generate branches: {str(e)}")

    async def explain_node(
        self,
        node_id: str,
        node_data: Dict[str, Any],
        document_content: str,
    ) -> AsyncIterator[OutputEvent]:
        """
        Stream explanation for a node.

        Args:
            node_id: ID of the node to explain
            node_data: Node data including label and content
            document_content: Document content for context

        Yields:
            TOKEN events for each generated token
        """
        logger.info(f"[MindmapAgent] Explaining node: {node_id}")

        content = self._truncate_content(document_content, max_chars=10000)
        prompt = EXPLAIN_NODE_PROMPT.format(
            content=content,
            node_label=node_data.get("label", ""),
            node_content=node_data.get("content", ""),
        )

        messages = [
            ChatMessage(role="system", content="You are a helpful assistant that explains concepts clearly."),
            ChatMessage(role="user", content=prompt),
        ]

        try:
            async for token in self._llm.chat_stream(messages):
                yield self._emit_token(token)

            yield self._emit_complete("Explanation complete")

        except Exception as e:
            logger.error(f"[MindmapAgent] Explain failed: {e}")
            yield self._emit_error(f"Explanation failed: {str(e)}")

    async def expand_node(
        self,
        node_id: str,
        node_data: Dict[str, Any],
        existing_children: List[Dict[str, Any]],
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

        prompt = EXPAND_NODE_PROMPT.format(
            content=content,
            node_label=node_data.get("label", ""),
            node_content=node_data.get("content", ""),
            existing_children=", ".join(existing_labels) if existing_labels else "None",
            max_branches=3,  # Generate fewer branches for expansion
        )

        messages = [
            ChatMessage(role="system", content=MINDMAP_SYSTEM_PROMPT),
            ChatMessage(role="user", content=prompt),
        ]

        try:
            yield self._emit_started("Expanding node")

            response = await self._llm.chat(messages)
            data = self._parse_json_response(response.content)

            if not data or "branches" not in data:
                yield self._emit_error("Failed to generate new branches")
                return

            # Calculate positions based on existing children
            parent_x = node_data.get("x", 400)
            parent_y = node_data.get("y", 300)
            parent_depth = node_data.get("depth", 0)
            new_level = parent_depth + 1

            num_existing = len(existing_children)
            branches = data["branches"][:3]

            for i, branch in enumerate(branches):
                node_index = num_existing + i
                x = parent_x + HORIZONTAL_SPACING
                y = parent_y + (node_index - num_existing / 2) * VERTICAL_SPACING

                new_node_id = f"node-{uuid4().hex[:8]}"
                new_node = MindmapNode(
                    id=new_node_id,
                    label=branch.get("label", f"Branch {node_index + 1}"),
                    content=branch.get("content", ""),
                    depth=new_level,
                    parent_id=node_id,
                    x=x,
                    y=y,
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

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        content = response.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            # Find the end of the first line (language identifier)
            first_newline = content.find("\n")
            if first_newline != -1:
                content = content[first_newline + 1:]
            if content.endswith("```"):
                content = content[:-3].strip()
            elif "```" in content:
                content = content[:content.rfind("```")].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"[MindmapAgent] JSON parse error: {e}, content: {content[:200]}")
            return None

    def _calculate_child_positions(
        self,
        parent: MindmapNode,
        num_children: int,
    ) -> List[tuple[float, float]]:
        """Calculate positions for child nodes."""
        positions: List[tuple[float, float]] = []

        # Position children to the right of parent
        x = parent.x + HORIZONTAL_SPACING

        # Center children vertically around parent
        total_height = (num_children - 1) * VERTICAL_SPACING
        start_y = parent.y - (total_height / 2)

        for i in range(num_children):
            y = start_y + (i * VERTICAL_SPACING)
            positions.append((x, y))

        return positions

    def _get_color_for_level(self, level: int) -> str:
        """Get color for a node based on its depth level."""
        colors = ["primary", "blue", "green", "orange", "purple", "pink"]
        return colors[level % len(colors)]

