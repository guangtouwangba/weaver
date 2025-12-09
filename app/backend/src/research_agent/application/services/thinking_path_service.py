"""
Thinking Path Service - Visualizes the user's conversation journey.

This service creates a visual "Thinking Path" that shows:
1. User questions (Question nodes)
2. AI answer summaries (Answer nodes)
3. Key insights extracted from AI responses (Insight nodes)

The goal is to help users visualize their exploration journey through the chat,
not to show the AI's internal reasoning process.
"""

import asyncio
import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.application.prompts.thinking_path_extraction import (
    THINKING_PATH_EXTRACTION_SYSTEM_PROMPT,
    THINKING_PATH_EXTRACTION_USER_PROMPT,
)
from research_agent.domain.entities.canvas import Canvas, CanvasEdge, CanvasNode, CanvasSection
from research_agent.domain.entities.chat import ChatMessage
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.llm.base import ChatMessage as LLMChatMessage
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
NODE_SPACING_X = 380  # Width + gap (horizontal between levels)
NODE_SPACING_Y = 60  # Height + gap (vertical within level, for insights)
INSIGHT_SPACING_Y = 220  # Spacing between insight nodes


@dataclass
class ThinkingPathNode:
    """Represents a node in the thinking path."""

    id: str
    type: str  # "question" | "answer" | "insight"
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

    Creates a visual map of:
    - User questions (Question nodes - blue dashed)
    - AI answer summaries (Answer nodes - green solid)
    - Key insights from answers (Insight nodes - yellow/gold)

    Structure: Question -> Answer -> [Insight, Insight, Insight, ...]
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

        # Track the last question node ID for connecting answers
        self._last_question_node_id: Dict[str, str] = {}  # project_id -> node_id

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

            # Step 3: Create nodes for this message
            new_nodes, new_internal_edges = await self._create_nodes_for_message(
                message=message,
                existing_nodes=existing_nodes,
                existing_messages=existing_messages,
                duplicate_of=duplicate_node_id,
                project_id=project_id,
            )

            if new_nodes:
                result.nodes.extend(new_nodes)
                result.edges.extend(new_internal_edges)

            # Step 4: Connect to previous node in conversation flow
            if new_nodes and message.role == "user":
                # Store the question node ID for later connecting the answer
                self._last_question_node_id[project_id] = new_nodes[0].id
            elif new_nodes and message.role != "user":
                # Connect answer to the previous question
                last_q_id = self._last_question_node_id.get(project_id)
                if last_q_id:
                    edge_id = f"edge-{last_q_id}-{new_nodes[0].id}"
                    result.edges.append(
                        {
                            "id": edge_id,
                            "source": last_q_id,
                            "target": new_nodes[0].id,
                        }
                    )

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

        # Get existing question nodes only
        question_nodes = [
            n for n in existing_nodes if n.type == "question" and n.view_type == "thinking"
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

    async def _create_nodes_for_message(
        self,
        message: ChatMessage,
        existing_nodes: List[CanvasNode],
        existing_messages: List[ChatMessage],
        duplicate_of: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Tuple[List[ThinkingPathNode], List[Dict[str, str]]]:
        """
        Create thinking path node(s) for a chat message.

        For user messages: Creates a single "question" node
        For AI messages: Creates one "answer" node + multiple "insight" nodes
        """
        nodes: List[ThinkingPathNode] = []
        edges: List[Dict[str, str]] = []

        # Calculate base position
        base_x, base_y = self._calculate_node_position(existing_nodes)

        # 1. User Message: Single "Question" Node
        if message.role == "user":
            node_id = f"tp-q-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"

            # Truncate long questions but keep them readable
            content = message.content
            if len(content) > 300:
                content = content[:297] + "..."

            node = ThinkingPathNode(
                id=node_id,
                type="question",
                title="User Question",
                content=content,
                message_ids=[str(message.id)],
                x=base_x,
                y=base_y,
                color="blue",
                analysis_status="analyzed",
                is_duplicate=duplicate_of is not None,
                duplicate_of=duplicate_of,
            )
            nodes.append(node)
            return nodes, edges

        # 2. AI Message: Try to extract summary + insights
        if self._llm_service and message.role != "user":
            try:
                # Find the user question for context
                user_question = "Context not available"
                if existing_messages:
                    last_user_msg = next(
                        (m for m in reversed(existing_messages) if m.role == "user"), None
                    )
                    if last_user_msg:
                        user_question = last_user_msg.content

                extracted_data = await self._extract_answer_and_insights(
                    user_question, message.content
                )

                if extracted_data:
                    return self._convert_to_answer_insight_nodes(
                        extracted_data, message, existing_nodes, base_x, base_y
                    )
            except Exception as e:
                logger.warning(
                    f"[ThinkingPath] Extraction failed, falling back to simple node: {e}"
                )

        # 3. Fallback: Single "Answer" Node (if LLM extraction fails)
        node_id = f"tp-a-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"

        # Truncate long responses
        content = message.content
        if len(content) > 500:
            content = content[:497] + "..."

        node = ThinkingPathNode(
            id=node_id,
            type="answer",
            title="AI Response",
            content=content,
            message_ids=[str(message.id)],
            x=base_x,
            y=base_y,
            color="green",
            analysis_status="analyzed",
        )
        nodes.append(node)
        return nodes, edges

    async def _extract_answer_and_insights(
        self, question: str, response: str
    ) -> Optional[Dict[str, Any]]:
        """Call LLM to extract answer summary and key insights."""
        if not self._llm_service:
            return None

        system_prompt = THINKING_PATH_EXTRACTION_SYSTEM_PROMPT
        user_prompt = THINKING_PATH_EXTRACTION_USER_PROMPT.format(
            question=question, response=response
        )

        messages = [
            LLMChatMessage(role="system", content=system_prompt),
            LLMChatMessage(role="user", content=user_prompt),
        ]

        try:
            chat_response = await self._llm_service.chat(messages)
            content = chat_response.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                # Find the end of the first line (language identifier)
                first_newline = content.find("\n")
                if first_newline != -1:
                    content = content[first_newline + 1 :]
                if content.endswith("```"):
                    content = content[:-3].strip()
                elif "```" in content:
                    content = content[: content.rfind("```")].strip()

            # Parse JSON
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"[ThinkingPath] JSON parse error: {e}, content: {content[:200]}")
            return None
        except Exception as e:
            logger.error(f"[ThinkingPath] LLM extraction error: {e}")
            return None

    def _convert_to_answer_insight_nodes(
        self,
        data: Dict[str, Any],
        message: ChatMessage,
        existing_nodes: List[CanvasNode],
        base_x: float,
        base_y: float,
    ) -> Tuple[List[ThinkingPathNode], List[Dict[str, str]]]:
        """
        Convert extracted summary/insights to Answer + Insight nodes.

        Layout:
        - Answer node at (base_x, base_y)
        - Insight nodes fanned out to the right of Answer
        """
        nodes: List[ThinkingPathNode] = []
        edges: List[Dict[str, str]] = []

        summary = data.get("summary", "AI Response")
        insights = data.get("insights", [])

        # 1. Create Answer Node
        answer_id = f"tp-a-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"

        answer_node = ThinkingPathNode(
            id=answer_id,
            type="answer",
            title="AI Answer",
            content=summary[:400] if len(summary) > 400 else summary,
            message_ids=[str(message.id)],
            x=base_x,
            y=base_y,
            color="green",
            analysis_status="analyzed",
        )
        nodes.append(answer_node)

        # 2. Create Insight Nodes (fanned out to the right)
        if insights:
            num_insights = len(insights)
            # Center the insights vertically around the answer node
            total_height = (num_insights - 1) * INSIGHT_SPACING_Y
            start_y = base_y - (total_height / 2)

            for i, insight in enumerate(insights):
                insight_id = (
                    f"tp-i-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}-{i}"
                )

                insight_title = insight.get("title", f"Insight {i + 1}")
                insight_content = insight.get("content", "")

                # Truncate if needed
                if len(insight_title) > 40:
                    insight_title = insight_title[:37] + "..."
                if len(insight_content) > 200:
                    insight_content = insight_content[:197] + "..."

                insight_node = ThinkingPathNode(
                    id=insight_id,
                    type="insight",
                    title=insight_title,
                    content=insight_content,
                    message_ids=[str(message.id)],
                    x=base_x + NODE_SPACING_X,  # To the right of answer
                    y=start_y + (i * INSIGHT_SPACING_Y),
                    color="yellow",
                    analysis_status="analyzed",
                )
                nodes.append(insight_node)

                # Create edge from answer to insight
                edge_id = f"edge-{answer_id}-{insight_id}"
                edges.append(
                    {
                        "id": edge_id,
                        "source": answer_id,
                        "target": insight_id,
                    }
                )

        return nodes, edges

    def _calculate_node_position(
        self,
        existing_nodes: List[CanvasNode],
    ) -> Tuple[float, float]:
        """
        Calculate position for a new node.

        Uses a left-to-right flow layout:
        - Each Q&A pair forms a column
        - New pairs are placed to the right of existing ones
        """
        # Filter to thinking path nodes only
        tp_nodes = [
            n
            for n in existing_nodes
            if n.view_type == "thinking" or (n.tags and "#thinking-path" in n.tags)
        ]

        if not tp_nodes:
            # First node starts at origin
            return 100, 300

        # Find the rightmost node
        max_x = max(n.x for n in tp_nodes)

        # Count question nodes to determine column
        question_count = len([n for n in tp_nodes if n.type == "question"])

        # Place new question nodes in a new column to the right
        # Place answer nodes at the same X as the last question
        x = 100 + (question_count * NODE_SPACING_X * 2)  # 2x spacing for Q->A->I structure
        y = 300  # Centered vertically

        return x, y

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
            "title": f"Exploration: {question_preview}...",
            "viewType": "thinking",
            "isCollapsed": False,
            "nodeIds": [],
            "x": 50,
            "y": 50,
            "question": first_user_msg.content if first_user_msg else None,
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
        }

        # Process messages in pairs (user question + AI answer)
        all_nodes: List[ThinkingPathNode] = []
        column_index = 0
        last_question_node: Optional[ThinkingPathNode] = None

        for i, message in enumerate(messages_to_process):
            # Calculate position based on column
            if message.role == "user":
                base_x = 100 + (column_index * NODE_SPACING_X * 2)
                base_y = 300
            else:
                # AI answer goes in the same column as the question
                base_x = 100 + (column_index * NODE_SPACING_X * 2) + NODE_SPACING_X
                base_y = 300

            # Create nodes
            new_nodes, new_internal_edges = await self._create_nodes_for_message(
                message=message,
                existing_nodes=[n.to_canvas_node() for n in all_nodes],
                existing_messages=messages_to_process[:i],
                duplicate_of=None,
                project_id=project_id,
            )

            if new_nodes:
                # Override positions for batch layout
                if message.role == "user":
                    new_nodes[0].x = base_x
                    new_nodes[0].y = base_y
                    last_question_node = new_nodes[0]
                else:
                    # Position answer and insights
                    new_nodes[0].x = base_x
                    new_nodes[0].y = base_y

                    # Reposition insight nodes
                    insights = [n for n in new_nodes if n.type == "insight"]
                    if insights:
                        total_height = (len(insights) - 1) * INSIGHT_SPACING_Y
                        start_y = base_y - (total_height / 2)
                        for j, insight in enumerate(insights):
                            insight.x = base_x + NODE_SPACING_X
                            insight.y = start_y + (j * INSIGHT_SPACING_Y)

                    # Connect question to answer
                    if last_question_node:
                        edge_id = f"edge-{last_question_node.id}-{new_nodes[0].id}"
                        result.edges.append(
                            {
                                "id": edge_id,
                                "source": last_question_node.id,
                                "target": new_nodes[0].id,
                            }
                        )

                    # Move to next column after Q&A pair
                    column_index += 1

                # Add nodes to result
                for n in new_nodes:
                    result.section["nodeIds"].append(n.id)
                all_nodes.extend(new_nodes)
                result.nodes.extend(new_nodes)
                result.edges.extend(new_internal_edges)

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

            if project_id in self._last_question_node_id:
                del self._last_question_node_id[project_id]
        else:
            # Clear all cache
            self._embedding_cache.clear()
            self._question_node_cache.clear()
            self._last_question_node_id.clear()

        logger.info(f"[ThinkingPath] Cache cleared for project: {project_id or 'all'}")
