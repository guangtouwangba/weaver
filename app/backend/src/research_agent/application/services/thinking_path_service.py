"""
Thinking Path Service - Automatically generates thinking path nodes from chat conversations.

This service:
1. Analyzes chat messages to extract conversation structure
2. Detects duplicate/similar questions using embeddings
3. Creates canvas nodes and edges for the thinking path
4. Broadcasts updates via WebSocket for multi-client sync
"""

import asyncio
import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.canvas import Canvas, CanvasEdge, CanvasNode, CanvasSection
from research_agent.domain.entities.chat import ChatMessage
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.llm.base import LLMService
from research_agent.infrastructure.websocket.canvas_notification_service import (
    CanvasEventType,
    canvas_notification_service,
)
from research_agent.shared.utils.logger import logger

# Similarity threshold for duplicate detection
DUPLICATE_THRESHOLD = 0.85

# Maximum messages to analyze at once (for LLM context limit)
MAX_MESSAGES_PER_ANALYSIS = 20

# Node layout constants
NODE_WIDTH = 280
NODE_HEIGHT = 200
NODE_SPACING_X = 320  # Width + gap
NODE_SPACING_Y = 250  # Height + gap
NODES_PER_ROW = 3


@dataclass
class ThinkingPathNode:
    """Represents a node in the thinking path."""

    id: str
    type: str  # "question" | "answer" | "conclusion" | "insight"
    title: str
    content: str
    message_ids: List[str] = field(default_factory=list)
    x: float = 0
    y: float = 0
    color: str = "blue"
    analysis_status: str = "pending"  # "pending" | "analyzed" | "error"
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None  # Node ID if this is a duplicate

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "messageIds": self.message_ids,
            "x": self.x,
            "y": self.y,
            "width": NODE_WIDTH,
            "height": NODE_HEIGHT,
            "color": self.color,
            "tags": ["#thinking-path"],
            "viewType": "thinking",
            "analysisStatus": self.analysis_status,
            "isDuplicate": self.is_duplicate,
            "duplicateOf": self.duplicate_of,
        }

    def to_canvas_node(self, section_id: Optional[str] = None) -> CanvasNode:
        """Convert to CanvasNode entity."""
        return CanvasNode(
            id=self.id,
            type=self.type,
            title=self.title,
            content=self.content,
            x=self.x,
            y=self.y,
            width=NODE_WIDTH,
            height=NODE_HEIGHT,
            color=self.color,
            tags=["#thinking-path"],
            view_type="thinking",
            section_id=section_id,
        )


@dataclass
class ThinkingPathAnalysisResult:
    """Result of thinking path analysis."""

    nodes: List[ThinkingPathNode] = field(default_factory=list)
    edges: List[Dict[str, str]] = field(default_factory=list)
    section: Optional[Dict[str, Any]] = None
    duplicate_mappings: Dict[str, str] = field(
        default_factory=dict
    )  # message_id -> existing_node_id
    error: Optional[str] = None


class ThinkingPathService:
    """
    Service for generating thinking path visualizations from chat conversations.

    Supports:
    - Real-time node generation as messages are sent
    - Duplicate question detection using embeddings
    - Multi-client synchronization via WebSocket
    - Incremental analysis for long conversations
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        llm_service: Optional[LLMService] = None,
    ):
        self._embedding_service = embedding_service
        self._llm_service = llm_service

        # Cache for question embeddings (message_id -> embedding)
        self._embedding_cache: Dict[str, List[float]] = {}

        # Cache for existing question nodes (project_id -> {content_hash -> node_id})
        self._question_node_cache: Dict[str, Dict[str, str]] = {}

    async def process_new_message(
        self,
        project_id: str,
        message: ChatMessage,
        existing_nodes: List[CanvasNode],
        existing_messages: List[ChatMessage],
    ) -> ThinkingPathAnalysisResult:
        """
        Process a new chat message and generate/update thinking path nodes.

        This is the main entry point called after a chat message is saved.

        Args:
            project_id: Project ID
            message: The new chat message
            existing_nodes: Existing canvas nodes (for duplicate detection)
            existing_messages: Recent chat history (for context)

        Returns:
            ThinkingPathAnalysisResult with new nodes/edges
        """
        result = ThinkingPathAnalysisResult()

        try:
            # Step 1: Notify clients that analysis is starting
            await canvas_notification_service.notify_thinking_path_analyzing(
                project_id=project_id,
                message_id=str(message.id),
            )

            # Step 2: Check for duplicate questions (user messages only)
            duplicate_node_id = None
            if message.role == "user":
                duplicate_node_id = await self._detect_duplicate_question(
                    project_id=project_id,
                    question=message.content,
                    message_id=str(message.id),
                    existing_nodes=existing_nodes,
                )

                if duplicate_node_id:
                    result.duplicate_mappings[str(message.id)] = duplicate_node_id
                    logger.info(
                        f"[ThinkingPath] Duplicate detected: message {message.id} -> node {duplicate_node_id}"
                    )

            # Step 3: Create node for this message
            node = await self._create_node_for_message(
                message=message,
                existing_nodes=existing_nodes,
                existing_messages=existing_messages,
                duplicate_of=duplicate_node_id,
            )

            if node:
                result.nodes.append(node)

            # Step 4: Create edges (connect to previous message if applicable)
            if node and existing_messages:
                edges = self._create_edges_for_node(
                    node=node,
                    existing_messages=existing_messages,
                    existing_nodes=existing_nodes,
                    new_nodes=result.nodes,
                )
                result.edges.extend(edges)

            # Step 5: Broadcast result to all clients
            await canvas_notification_service.notify_thinking_path_analyzed(
                project_id=project_id,
                message_id=str(message.id),
                nodes=[n.to_dict() for n in result.nodes],
                edges=result.edges,
                duplicate_of=duplicate_node_id,
            )

            logger.info(
                f"[ThinkingPath] Analysis complete: {len(result.nodes)} nodes, "
                f"{len(result.edges)} edges"
            )

        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            result.error = error_msg
            logger.error(f"[ThinkingPath] {error_msg}", exc_info=True)

            # Notify clients of error
            await canvas_notification_service.notify_thinking_path_error(
                project_id=project_id,
                message_id=str(message.id),
                error_message=error_msg,
            )

        return result

    async def _detect_duplicate_question(
        self,
        project_id: str,
        question: str,
        message_id: str,
        existing_nodes: List[CanvasNode],
    ) -> Optional[str]:
        """
        Detect if a question is similar to an existing question node.

        Uses embedding similarity to find duplicates.

        Returns:
            Node ID of the duplicate question, or None if no duplicate found
        """
        if not existing_nodes:
            return None

        # Get existing question nodes
        question_nodes = [
            n
            for n in existing_nodes
            if n.type in ("question", "answer")
            and n.role_type == "user"
            or n.tags
            and "#thinking-path" in n.tags
        ]

        if not question_nodes:
            return None

        try:
            # Get embedding for the new question
            new_embedding = await self._embedding_service.embed(question)
            self._embedding_cache[message_id] = new_embedding

            # Compare with existing question embeddings
            max_similarity = 0.0
            most_similar_node_id = None

            for node in question_nodes:
                # Skip non-question nodes
                if node.type not in ("question",) and "user" not in node.title.lower():
                    continue

                # Get or compute embedding for existing node
                node_embedding = self._embedding_cache.get(node.id)
                if not node_embedding:
                    node_embedding = await self._embedding_service.embed(node.content)
                    self._embedding_cache[node.id] = node_embedding

                # Compute cosine similarity
                similarity = self._cosine_similarity(new_embedding, node_embedding)

                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_node_id = node.id

            if max_similarity >= DUPLICATE_THRESHOLD:
                logger.info(
                    f"[ThinkingPath] Found duplicate: similarity={max_similarity:.3f}, "
                    f"threshold={DUPLICATE_THRESHOLD}"
                )
                return most_similar_node_id

            return None

        except Exception as e:
            logger.warning(f"[ThinkingPath] Duplicate detection failed: {e}")
            return None

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def _create_node_for_message(
        self,
        message: ChatMessage,
        existing_nodes: List[CanvasNode],
        existing_messages: List[ChatMessage],
        duplicate_of: Optional[str] = None,
    ) -> Optional[ThinkingPathNode]:
        """
        Create a thinking path node for a chat message.
        """
        # Determine node type and appearance based on message role
        if message.role == "user":
            node_type = "question"
            title = "Your Question"
            color = "green"
        else:
            # AI message
            node_type = "answer"
            title = "AI Response"
            color = "blue"

        # Calculate position based on existing nodes
        x, y = self._calculate_node_position(existing_nodes)

        # Generate unique node ID
        node_id = f"tp-node-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"

        node = ThinkingPathNode(
            id=node_id,
            type=node_type,
            title=title,
            content=message.content[:500] if len(message.content) > 500 else message.content,
            message_ids=[str(message.id)],
            x=x,
            y=y,
            color=color,
            analysis_status="analyzed",
            is_duplicate=duplicate_of is not None,
            duplicate_of=duplicate_of,
        )

        return node

    def _calculate_node_position(
        self,
        existing_nodes: List[CanvasNode],
    ) -> Tuple[float, float]:
        """
        Calculate position for a new node.
        Uses a simple grid layout.
        """
        # Filter to thinking path nodes only
        tp_nodes = [
            n
            for n in existing_nodes
            if n.view_type == "thinking" or (n.tags and "#thinking-path" in n.tags)
        ]

        node_count = len(tp_nodes)

        # Grid layout
        row = node_count // NODES_PER_ROW
        col = node_count % NODES_PER_ROW

        x = 100 + col * NODE_SPACING_X
        y = 100 + row * NODE_SPACING_Y

        return x, y

    def _create_edges_for_node(
        self,
        node: ThinkingPathNode,
        existing_messages: List[ChatMessage],
        existing_nodes: List[CanvasNode],
        new_nodes: List[ThinkingPathNode],
    ) -> List[Dict[str, str]]:
        """
        Create edges connecting the new node to relevant existing nodes.
        """
        edges = []

        # Find the previous message's node and connect
        if len(existing_messages) >= 2:
            prev_message = existing_messages[-2]  # Second to last message

            # Find existing node for previous message
            # This is simplified - in production you'd have a message_id -> node_id mapping
            prev_node_id = None

            # Check in existing nodes
            for existing_node in existing_nodes:
                if existing_node.view_type == "thinking":
                    # Simple heuristic: match by content similarity
                    if prev_message.content[:100] in existing_node.content:
                        prev_node_id = existing_node.id
                        break

            if prev_node_id:
                edge_id = f"edge-{prev_node_id}-{node.id}"
                edges.append(
                    {
                        "id": edge_id,
                        "source": prev_node_id,
                        "target": node.id,
                    }
                )

        return edges

    async def analyze_conversation_batch(
        self,
        project_id: str,
        messages: List[ChatMessage],
        start_index: int = 0,
    ) -> ThinkingPathAnalysisResult:
        """
        Analyze a batch of conversation messages.

        This is used for:
        - Initial analysis when enabling auto-generation
        - Catch-up analysis for missed messages

        Args:
            project_id: Project ID
            messages: List of chat messages to analyze
            start_index: Index to start from (for incremental analysis)

        Returns:
            ThinkingPathAnalysisResult with all nodes and edges
        """
        result = ThinkingPathAnalysisResult()

        # Limit batch size
        messages_to_process = messages[start_index : start_index + MAX_MESSAGES_PER_ANALYSIS]

        if not messages_to_process:
            return result

        logger.info(
            f"[ThinkingPath] Batch analysis: {len(messages_to_process)} messages, "
            f"starting from index {start_index}"
        )

        # Create section for this conversation
        section_id = f"section-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        first_user_msg = next(
            (m for m in messages_to_process if m.role == "user"),
            messages_to_process[0] if messages_to_process else None,
        )

        question_preview = first_user_msg.content[:50] if first_user_msg else "Conversation"

        result.section = {
            "id": section_id,
            "title": f"Thinking: {question_preview}...",
            "viewType": "thinking",
            "isCollapsed": False,
            "nodeIds": [],
            "x": 50,
            "y": 50,
            "question": first_user_msg.content if first_user_msg else None,
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
        }

        # Process each message
        prev_node: Optional[ThinkingPathNode] = None

        for i, message in enumerate(messages_to_process):
            # Create node
            node = await self._create_node_for_message(
                message=message,
                existing_nodes=[],  # Simplified for batch
                existing_messages=messages_to_process[:i],
                duplicate_of=None,
            )

            if node:
                # Recalculate position for batch layout
                row = i // NODES_PER_ROW
                col = i % NODES_PER_ROW
                node.x = 100 + col * NODE_SPACING_X
                node.y = 100 + row * NODE_SPACING_Y

                result.nodes.append(node)
                result.section["nodeIds"].append(node.id)

                # Create edge to previous node
                if prev_node:
                    edge_id = f"edge-{prev_node.id}-{node.id}"
                    result.edges.append(
                        {
                            "id": edge_id,
                            "source": prev_node.id,
                            "target": node.id,
                        }
                    )

                prev_node = node

        # Broadcast batch result
        await canvas_notification_service.notify_batch_update(
            project_id=project_id,
            nodes=[n.to_dict() for n in result.nodes],
            edges=result.edges,
            sections=[result.section] if result.section else None,
        )

        logger.info(
            f"[ThinkingPath] Batch analysis complete: {len(result.nodes)} nodes, "
            f"{len(result.edges)} edges"
        )

        return result

    def clear_cache(self, project_id: Optional[str] = None) -> None:
        """
        Clear embedding cache.

        Args:
            project_id: If provided, only clear cache for this project
        """
        if project_id:
            # Clear project-specific cache
            keys_to_remove = [k for k in self._embedding_cache.keys() if k.startswith(project_id)]
            for key in keys_to_remove:
                del self._embedding_cache[key]

            if project_id in self._question_node_cache:
                del self._question_node_cache[project_id]
        else:
            # Clear all cache
            self._embedding_cache.clear()
            self._question_node_cache.clear()

        logger.info(f"[ThinkingPath] Cache cleared for project: {project_id or 'all'}")
