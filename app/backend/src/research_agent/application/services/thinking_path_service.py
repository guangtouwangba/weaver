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
    EDGE_RELATION_CLASSIFICATION_SYSTEM_PROMPT,
    EDGE_RELATION_CLASSIFICATION_USER_PROMPT,
    EDGE_RELATION_DEFAULT_LABELS,
    EDGE_RELATION_KEYWORDS,
    THINKING_GRAPH_EXTRACTION_SYSTEM_PROMPT,
    THINKING_GRAPH_EXTRACTION_USER_PROMPT,
    THINKING_GRAPH_INTENT_CLASSIFICATION_PROMPT,
    THINKING_GRAPH_INTENT_USER_PROMPT,
    THINKING_PATH_EXTRACTION_SYSTEM_PROMPT,
    THINKING_PATH_EXTRACTION_USER_PROMPT,
)
from research_agent.domain.entities.canvas import Canvas, CanvasEdge, CanvasNode, CanvasSection
from research_agent.domain.entities.chat import ChatMessage
from research_agent.domain.entities.thinking_path import EdgeRelationType
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

# Similarity thresholds by node type
DUPLICATE_THRESHOLDS = {
    "question": 0.85,
    "answer": 0.90,
    "insight": 0.88,
    "thinking_step": 0.85,
    "thinking_branch": 0.80,
}

# Maximum messages to analyze at once (for LLM context limit)
MAX_MESSAGES_PER_ANALYSIS = 20

# Node layout constants
NODE_WIDTH = 280
NODE_HEIGHT = 200
NODE_SPACING_X = 380  # Width + gap (horizontal between levels)
NODE_SPACING_Y = 60  # Height + gap (vertical within level, for insights)
INSIGHT_SPACING_Y = 220  # Spacing between insight nodes

# Intent types for thinking graph
INTENT_CONTINUATION = "continuation"
INTENT_BRANCH = "branch"
INTENT_NEW_TOPIC = "new_topic"


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


@dataclass
class TopicContext:
    """
    Represents a topic context in the thinking graph.

    A topic is a branch of exploration in the conversation.
    Multiple topics can exist, and users can branch from any point.
    """

    topic_id: str
    root_message_id: str
    keywords: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    last_node_id: str = ""
    depth: int = 0
    parent_topic_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "root_message_id": self.root_message_id,
            "keywords": self.keywords,
            "last_node_id": self.last_node_id,
            "depth": self.depth,
            "parent_topic_id": self.parent_topic_id,
        }


@dataclass
class IntentClassificationResult:
    """Result of message intent classification."""

    intent: str  # "continuation" | "branch" | "new_topic"
    confidence: float = 0.0
    parent_topic_id: Optional[str] = None
    reasoning: str = ""


@dataclass
class ThinkingStepExtraction:
    """Extracted thinking step from a message exchange."""

    claim: str = ""
    reason: str = ""
    evidence: str = ""
    uncertainty: str = ""
    decision: str = ""
    related_concepts: List[str] = field(default_factory=list)
    suggested_branches: List[Dict[str, str]] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


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

        # === Thinking Graph: Topic Context Tracking ===
        # Store topic contexts per project (project_id -> List[TopicContext])
        self._topic_contexts: Dict[str, List[TopicContext]] = {}

        # Track the active topic per project (project_id -> topic_id)
        # This is the topic that new "continuation" messages will attach to
        self._active_topic: Dict[str, str] = {}

        # Cache for topic embeddings (topic_id -> embedding)
        self._topic_embedding_cache: Dict[str, List[float]] = {}

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

            # Step 3: For AI messages, first create a question node for the preceding user message
            # This ensures Q->A connection even when backend only processes AI messages
            question_node = None
            related_insight_id = None
            if message.role != "user" and existing_messages:
                # Find the last user message
                last_user_msg = next(
                    (m for m in reversed(existing_messages) if m.role == "user"), None
                )
                if last_user_msg:
                    # Check if we already have a question node stored
                    last_q_id = self._last_question_node_id.get(project_id)
                    if not last_q_id:
                        # Check if this question is a follow-up to an existing insight
                        related_insight_id = await self._find_related_insight(
                            question=last_user_msg.content,
                            existing_nodes=existing_nodes,
                        )

                        # Create a question node for the user message
                        question_nodes, _ = await self._create_nodes_for_message(
                            message=last_user_msg,
                            existing_nodes=existing_nodes,
                            existing_messages=existing_messages[:-1]
                            if len(existing_messages) > 1
                            else [],
                            duplicate_of=None,
                            project_id=project_id,
                        )
                        if question_nodes:
                            question_node = question_nodes[0]
                            result.nodes.append(question_node)
                            self._last_question_node_id[project_id] = question_node.id
                            logger.info(
                                f"[ThinkingPath] Created question node: {question_node.id} for user message"
                            )

                            # If this question is related to a previous insight, create a branch edge
                            if related_insight_id:
                                # Use prompts_question relation for insight → question
                                edge = self._create_edge_with_relation(
                                    source_id=related_insight_id,
                                    target_id=question_node.id,
                                    relation_type=EdgeRelationType.PROMPTS_QUESTION.value,
                                    label=EDGE_RELATION_DEFAULT_LABELS["prompts_question"],
                                    edge_type="branch",  # Keep type for styling compatibility
                                )
                                result.edges.append(edge)
                                logger.info(
                                    f"[ThinkingPath] Created branch edge from insight {related_insight_id} "
                                    f"to question {question_node.id} (relation: prompts_question)"
                                )

                            # Check for topic progression (question following up on previous question)
                            related_question_id = await self._find_related_question(
                                question=last_user_msg.content,
                                existing_nodes=existing_nodes,
                                exclude_node_id=question_node.id,
                            )
                            if related_question_id:
                                # Use prompts_question for Q → Q' progression
                                edge = self._create_edge_with_relation(
                                    source_id=related_question_id,
                                    target_id=question_node.id,
                                    relation_type=EdgeRelationType.PROMPTS_QUESTION.value,
                                    label=EDGE_RELATION_DEFAULT_LABELS["prompts_question"],
                                    edge_type="progression",  # Keep type for styling
                                )
                                result.edges.append(edge)
                                logger.info(
                                    f"[ThinkingPath] Created topic progression edge from question "
                                    f"{related_question_id} to question {question_node.id} (relation: prompts_question)"
                                )

            # Step 4: Create nodes for this message
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

            # Step 5: Connect to previous node in conversation flow
            if new_nodes and message.role == "user":
                # Store the question node ID for later connecting the answer
                self._last_question_node_id[project_id] = new_nodes[0].id
            elif new_nodes and message.role != "user":
                # Connect answer to the previous question
                last_q_id = self._last_question_node_id.get(project_id)
                if last_q_id:
                    # Use answers relation for Q → A
                    edge = self._create_edge_with_relation(
                        source_id=last_q_id,
                        target_id=new_nodes[0].id,
                        relation_type=EdgeRelationType.ANSWERS.value,
                        label=EDGE_RELATION_DEFAULT_LABELS["answers"],
                    )
                    result.edges.append(edge)
                    logger.info(
                        f"[ThinkingPath] Created edge from question {last_q_id} to answer {new_nodes[0].id} "
                        f"(relation: answers)"
                    )

            # Step 6: Broadcast result to all clients
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

    async def _find_related_insight(
        self,
        question: str,
        existing_nodes: List[CanvasNode],
        threshold: float = 0.75,
    ) -> Optional[str]:
        """
        Find an insight node that the new question is following up on.

        This detects "branch" relationships where a user asks about something
        mentioned in a previous answer's insights.

        Args:
            question: The new user question
            existing_nodes: Existing canvas nodes
            threshold: Similarity threshold (default 0.75 for branch detection)

        Returns:
            Node ID of the related insight, or None if no relation found
        """
        if not existing_nodes:
            return None

        # Get existing insight nodes only
        insight_nodes = [
            n
            for n in existing_nodes
            if n.type == "insight"
            and (n.view_type == "thinking" or "#thinking-path" in (n.tags or []))
        ]

        if not insight_nodes:
            return None

        try:
            # Get embedding for the new question
            question_embedding = await self._embedding_service.embed(question)

            # Find the most similar insight
            max_similarity = 0.0
            most_similar_insight_id = None

            for node in insight_nodes:
                # Use both title and content for matching
                node_text = f"{node.title} {node.content}"

                # Get or compute embedding for existing node
                cache_key = f"insight-{node.id}"
                node_embedding = self._embedding_cache.get(cache_key)
                if not node_embedding:
                    node_embedding = await self._embedding_service.embed(node_text)
                    self._embedding_cache[cache_key] = node_embedding

                # Compute cosine similarity
                similarity = self._cosine_similarity(question_embedding, node_embedding)

                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_insight_id = node.id

            if max_similarity >= threshold and most_similar_insight_id:
                logger.info(
                    f"[ThinkingPath] Found related insight: {most_similar_insight_id}, "
                    f"similarity={max_similarity:.3f}, threshold={threshold}"
                )
                return most_similar_insight_id

            return None

        except Exception as e:
            logger.warning(f"[ThinkingPath] Related insight detection failed: {e}")
            return None

    async def _find_related_question(
        self,
        question: str,
        existing_nodes: List[CanvasNode],
        exclude_node_id: Optional[str] = None,
        threshold: float = 0.65,
    ) -> Optional[str]:
        """
        Find a previous question node that the new question is a follow-up to.

        This detects topic progression where a user asks deeper questions
        about the same topic (e.g., "what is X?" -> "what are X's features?").

        Args:
            question: The new user question
            existing_nodes: Existing canvas nodes
            exclude_node_id: Node ID to exclude (e.g., the current node itself)
            threshold: Similarity threshold (default 0.65 for topic progression)

        Returns:
            Node ID of the related question, or None if no relation found
        """
        if not existing_nodes:
            return None

        # Get existing question nodes only (not duplicates)
        question_nodes = [
            n
            for n in existing_nodes
            if n.type == "question"
            and (n.view_type == "thinking" or "#thinking-path" in (n.tags or []))
            and n.id != exclude_node_id
        ]

        if not question_nodes:
            return None

        try:
            # Get embedding for the new question
            question_embedding = await self._embedding_service.embed(question)

            # Find the most similar question (but not duplicate - those are handled separately)
            candidates = []

            for node in question_nodes:
                # Use both title and content for matching
                node_text = f"{node.title} {node.content}"

                # Get or compute embedding for existing node
                cache_key = f"question-{node.id}"
                node_embedding = self._embedding_cache.get(cache_key)
                if not node_embedding:
                    node_embedding = await self._embedding_service.embed(node_text)
                    self._embedding_cache[cache_key] = node_embedding

                # Compute cosine similarity
                similarity = self._cosine_similarity(question_embedding, node_embedding)

                # Only consider if above threshold but below duplicate threshold (0.9)
                if threshold <= similarity < 0.9:
                    candidates.append((node.id, similarity))

            if candidates:
                # Sort by similarity (highest first) and return the best match
                candidates.sort(key=lambda x: x[1], reverse=True)
                best_match_id, best_similarity = candidates[0]
                logger.info(
                    f"[ThinkingPath] Found related question for topic progression: "
                    f"{best_match_id}, similarity={best_similarity:.3f}"
                )
                return best_match_id

            return None

        except Exception as e:
            logger.warning(f"[ThinkingPath] Related question detection failed: {e}")
            return None

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

    # =========================================================================
    # EDGE RELATION CLASSIFICATION
    # =========================================================================

    async def _classify_edge_relation(
        self,
        source_node: ThinkingPathNode,
        target_node: ThinkingPathNode,
        context: str = "",
    ) -> Tuple[str, str]:
        """
        Classify the semantic relationship between two nodes.

        Uses a combination of:
        1. Node type heuristics (fast path) - No LLM call needed
        2. Keyword detection (medium path) - Pattern matching
        3. LLM classification (slow path) - For ambiguous cases

        Args:
            source_node: The source node
            target_node: The target node
            context: Optional conversation context

        Returns:
            Tuple of (relation_type, label)
        """
        # === Fast Path: Node type heuristics ===
        source_type = source_node.type
        target_type = target_node.type

        # Q → A = answers
        if source_type == "question" and target_type == "answer":
            return (EdgeRelationType.ANSWERS.value, EDGE_RELATION_DEFAULT_LABELS["answers"])

        # A → Q = prompts_question (follow-up)
        if source_type == "answer" and target_type == "question":
            return (
                EdgeRelationType.PROMPTS_QUESTION.value,
                EDGE_RELATION_DEFAULT_LABELS["prompts_question"],
            )

        # A → Insight = derives
        if source_type == "answer" and target_type == "insight":
            return (EdgeRelationType.DERIVES.value, EDGE_RELATION_DEFAULT_LABELS["derives"])

        # Insight → Q = prompts_question (branch from insight)
        if source_type == "insight" and target_type == "question":
            return (
                EdgeRelationType.PROMPTS_QUESTION.value,
                EDGE_RELATION_DEFAULT_LABELS["prompts_question"],
            )

        # === Medium Path: Keyword detection ===
        combined_content = f"{source_node.content} {target_node.content}".lower()

        # Check for causal relationship
        if any(kw in combined_content for kw in EDGE_RELATION_KEYWORDS.get("causes", [])):
            return (EdgeRelationType.CAUSES.value, EDGE_RELATION_DEFAULT_LABELS["causes"])

        # Check for comparison
        if any(kw in combined_content for kw in EDGE_RELATION_KEYWORDS.get("compares", [])):
            return (EdgeRelationType.COMPARES.value, EDGE_RELATION_DEFAULT_LABELS["compares"])

        # Check for revision
        if any(kw in combined_content for kw in EDGE_RELATION_KEYWORDS.get("revises", [])):
            return (EdgeRelationType.REVISES.value, EDGE_RELATION_DEFAULT_LABELS["revises"])

        # Check for parking
        if any(kw in combined_content for kw in EDGE_RELATION_KEYWORDS.get("parks", [])):
            return (EdgeRelationType.PARKS.value, EDGE_RELATION_DEFAULT_LABELS["parks"])

        # === Slow Path: LLM classification (if available) ===
        if self._llm_service:
            try:
                result = await self._llm_classify_edge_relation(source_node, target_node, context)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"[ThinkingPath] LLM edge classification failed: {e}")

        # Default fallback
        return (EdgeRelationType.CUSTOM.value, EDGE_RELATION_DEFAULT_LABELS["custom"])

    async def _llm_classify_edge_relation(
        self,
        source_node: ThinkingPathNode,
        target_node: ThinkingPathNode,
        context: str = "",
    ) -> Optional[Tuple[str, str]]:
        """
        Use LLM to classify edge relationship.

        Args:
            source_node: The source node
            target_node: The target node
            context: Optional conversation context

        Returns:
            Tuple of (relation_type, label) or None if classification fails
        """
        if not self._llm_service:
            return None

        user_prompt = EDGE_RELATION_CLASSIFICATION_USER_PROMPT.format(
            source_type=source_node.type,
            source_title=source_node.title,
            source_content=source_node.content[:500],  # Truncate for token limit
            target_type=target_node.type,
            target_title=target_node.title,
            target_content=target_node.content[:500],
            context=context[:300] if context else "No additional context",
        )

        messages = [
            LLMChatMessage(role="system", content=EDGE_RELATION_CLASSIFICATION_SYSTEM_PROMPT),
            LLMChatMessage(role="user", content=user_prompt),
        ]

        try:
            response = await self._llm_service.chat(messages)
            content = response.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                first_newline = content.find("\n")
                if first_newline != -1:
                    content = content[first_newline + 1 :]
                if content.endswith("```"):
                    content = content[:-3].strip()
                elif "```" in content:
                    content = content[: content.rfind("```")].strip()

            # Parse JSON response
            data = json.loads(content)
            relation_type = data.get("relation_type", "custom")
            label = data.get("label", EDGE_RELATION_DEFAULT_LABELS.get(relation_type, ""))

            # Validate relation type
            valid_types = [e.value for e in EdgeRelationType]
            if relation_type not in valid_types:
                logger.warning(f"[ThinkingPath] Invalid relation type from LLM: {relation_type}")
                return None

            logger.info(
                f"[ThinkingPath] LLM classified edge: {relation_type} ({label}), "
                f"confidence={data.get('confidence', 0):.2f}"
            )
            return (relation_type, label)

        except json.JSONDecodeError as e:
            logger.warning(f"[ThinkingPath] Failed to parse LLM response: {e}")
            return None
        except Exception as e:
            logger.warning(f"[ThinkingPath] LLM edge classification error: {e}")
            return None

    def _create_edge_with_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        label: str,
        edge_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an edge dictionary with relation metadata.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            relation_type: The semantic relation type
            label: Display label for the edge
            edge_type: Optional edge type (branch, progression) for styling

        Returns:
            Edge dictionary with all metadata
        """
        edge_id = f"edge-{source_id}-{target_id}"

        edge = {
            "id": edge_id,
            "source": source_id,
            "target": target_id,
            "relationType": relation_type,
            "label": label,
        }

        # Add type if specified (for backward compatibility with branch/progression)
        if edge_type:
            edge["type"] = edge_type

        # Add direction hint for bidirectional relations
        if relation_type == EdgeRelationType.COMPARES.value:
            edge["direction"] = "bidirectional"

        return edge

    # =========================================================================
    # ENHANCED DUPLICATE DETECTION (Node-level, Path-level, Concept-level)
    # =========================================================================

    async def _detect_duplicate_node(
        self,
        project_id: str,
        content: str,
        node_type: str,
        existing_nodes: List[CanvasNode],
    ) -> Optional[Tuple[str, float]]:
        """
        Generic duplicate detection for any node type.

        Uses type-specific similarity thresholds for better accuracy.

        Args:
            project_id: Project ID
            content: Content to check for duplicates
            node_type: Type of node ("question", "answer", "insight", "thinking_step", etc.)
            existing_nodes: Existing canvas nodes to compare against

        Returns:
            Tuple of (duplicate_node_id, similarity_score) if duplicate found, None otherwise
        """
        if not existing_nodes:
            return None

        # Filter to matching node types (for thinking path nodes)
        matching_nodes = [
            n
            for n in existing_nodes
            if n.type == node_type
            and (n.view_type == "thinking" or "#thinking-path" in (n.tags or []))
        ]

        if not matching_nodes:
            return None

        # Get type-specific threshold
        threshold = DUPLICATE_THRESHOLDS.get(node_type, DUPLICATE_THRESHOLD)

        try:
            # Get embedding for the new content
            content_embedding = await self._embedding_service.embed(content)

            # Compare with existing node embeddings
            max_similarity = 0.0
            most_similar_node_id = None

            for node in matching_nodes:
                # Get or compute embedding for existing node
                node_embedding = self._embedding_cache.get(node.id)
                if not node_embedding:
                    node_embedding = await self._embedding_service.embed(node.content)
                    self._embedding_cache[node.id] = node_embedding

                similarity = self._cosine_similarity(content_embedding, node_embedding)

                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_node_id = node.id

            if max_similarity >= threshold and most_similar_node_id:
                logger.info(
                    f"[ThinkingPath] Duplicate {node_type} found: "
                    f"similarity={max_similarity:.3f}, threshold={threshold}"
                )
                return (most_similar_node_id, max_similarity)

            return None
        except Exception as e:
            logger.warning(f"[ThinkingPath] Duplicate node detection failed: {e}")
            return None

    async def _detect_similar_path(
        self,
        project_id: str,
        question_sequence: List[str],
        existing_nodes: List[CanvasNode],
        existing_edges: List[Dict[str, str]],
    ) -> Optional[Tuple[str, float]]:
        """
        Detect if a sequence of questions matches an existing path.

        This is useful for identifying when users are asking the same sequence
        of questions they asked before (e.g., same research methodology).

        Args:
            project_id: Project ID
            question_sequence: List of question contents in order
            existing_nodes: Existing canvas nodes
            existing_edges: Existing edges (to build paths)

        Returns:
            Tuple of (path_root_node_id, similarity_score) if similar path found
        """
        if len(question_sequence) < 2:
            # Need at least 2 questions to form a path
            return None

        # Build adjacency list from edges
        adjacency: Dict[str, List[str]] = {}
        for edge in existing_edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            if source and target:
                if source not in adjacency:
                    adjacency[source] = []
                adjacency[source].append(target)

        # Get question nodes and build node lookup
        question_nodes = [
            n for n in existing_nodes if n.type == "question" and n.view_type == "thinking"
        ]
        node_lookup = {n.id: n for n in question_nodes}

        # Find root question nodes (nodes that are not targets of any edge)
        all_targets = set()
        for edge in existing_edges:
            all_targets.add(edge.get("target", ""))

        root_nodes = [n for n in question_nodes if n.id not in all_targets]

        if not root_nodes:
            return None

        # Create embedding for the new question sequence
        try:
            # Concatenate questions for path embedding
            sequence_text = " -> ".join(question_sequence)
            sequence_embedding = await self._embedding_service.embed(sequence_text)

            # Compare with existing paths starting from each root
            max_similarity = 0.0
            most_similar_root_id = None

            for root in root_nodes:
                # Build path from this root
                path_questions = self._build_path_from_node(root.id, node_lookup, adjacency)

                if len(path_questions) < 2:
                    continue

                # Create embedding for existing path
                path_text = " -> ".join(path_questions)
                path_cache_key = f"path-{root.id}"

                if path_cache_key not in self._embedding_cache:
                    path_embedding = await self._embedding_service.embed(path_text)
                    self._embedding_cache[path_cache_key] = path_embedding

                path_embedding = self._embedding_cache[path_cache_key]
                similarity = self._cosine_similarity(sequence_embedding, path_embedding)

                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_root_id = root.id

            # Use a slightly lower threshold for path similarity
            path_threshold = 0.80
            if max_similarity >= path_threshold and most_similar_root_id:
                logger.info(
                    f"[ThinkingPath] Similar path found: root={most_similar_root_id}, "
                    f"similarity={max_similarity:.3f}"
                )
                return (most_similar_root_id, max_similarity)

            return None
        except Exception as e:
            logger.warning(f"[ThinkingPath] Path similarity detection failed: {e}")
            return None

    def _build_path_from_node(
        self,
        node_id: str,
        node_lookup: Dict[str, CanvasNode],
        adjacency: Dict[str, List[str]],
        max_depth: int = 10,
    ) -> List[str]:
        """
        Build a path (sequence of question contents) starting from a node.

        Args:
            node_id: Starting node ID
            node_lookup: Dict of node_id -> CanvasNode
            adjacency: Adjacency list (source -> [targets])
            max_depth: Maximum depth to traverse

        Returns:
            List of question contents in path order
        """
        path = []
        current_id = node_id
        visited = set()

        while current_id and len(path) < max_depth:
            if current_id in visited:
                break
            visited.add(current_id)

            node = node_lookup.get(current_id)
            if node and node.type == "question":
                path.append(node.content)

            # Get next node (follow first edge, skip answer nodes to get to next question)
            children = adjacency.get(current_id, [])
            current_id = None

            for child_id in children:
                child = node_lookup.get(child_id)
                if child and child.type == "question":
                    current_id = child_id
                    break
                elif child_id in adjacency:
                    # This might be an answer node, check its children
                    for grandchild_id in adjacency.get(child_id, []):
                        grandchild = node_lookup.get(grandchild_id)
                        if grandchild and grandchild.type == "question":
                            current_id = grandchild_id
                            break
                    if current_id:
                        break

        return path

    async def detect_and_merge_concept(
        self,
        project_id: str,
        concept: str,
        existing_concepts: List[str],
    ) -> Tuple[str, bool]:
        """
        Detect if a concept is similar to an existing concept and should be merged.

        This helps prevent concept explosion in the thinking graph by merging
        synonymous or very similar concepts (e.g., "ML" and "Machine Learning").

        Args:
            project_id: Project ID
            concept: New concept to check
            existing_concepts: List of existing concept strings

        Returns:
            Tuple of (canonical_concept, was_merged)
            - If merged: returns the existing concept it was merged into
            - If new: returns the original concept
        """
        if not existing_concepts:
            return (concept, False)

        try:
            # Get embedding for the new concept
            concept_embedding = await self._embedding_service.embed(concept)

            # Compare with existing concepts
            concept_threshold = 0.88  # High threshold for concept merging
            max_similarity = 0.0
            most_similar_concept = None

            for existing in existing_concepts:
                cache_key = f"concept-{existing}"
                if cache_key not in self._embedding_cache:
                    existing_embedding = await self._embedding_service.embed(existing)
                    self._embedding_cache[cache_key] = existing_embedding

                existing_embedding = self._embedding_cache[cache_key]
                similarity = self._cosine_similarity(concept_embedding, existing_embedding)

                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_concept = existing

            if max_similarity >= concept_threshold and most_similar_concept:
                logger.info(
                    f"[ThinkingPath] Concept merged: '{concept}' -> '{most_similar_concept}', "
                    f"similarity={max_similarity:.3f}"
                )
                return (most_similar_concept, True)

            return (concept, False)
        except Exception as e:
            logger.warning(f"[ThinkingPath] Concept merge detection failed: {e}")
            return (concept, False)

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

            # Title is the question itself (truncated if needed)
            question_title = message.content.strip()
            if len(question_title) > 25:
                question_title = question_title[:22] + "..."

            node = ThinkingPathNode(
                id=node_id,
                type="question",
                title=question_title,
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

        # Extract title, summary, and insights from LLM response
        answer_title = data.get("title", "AI Answer")
        summary = data.get("summary", "AI Response")
        insights = data.get("insights", [])

        # Ensure title is not too long (max 25 chars for display)
        if len(answer_title) > 25:
            answer_title = answer_title[:22] + "..."

        # 1. Create Answer Node
        answer_id = f"tp-a-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"

        answer_node = ThinkingPathNode(
            id=answer_id,
            type="answer",
            title=answer_title,
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

                # Create edge from answer to insight (derives relation)
                edge = self._create_edge_with_relation(
                    source_id=answer_id,
                    target_id=insight_id,
                    relation_type=EdgeRelationType.DERIVES.value,
                    label=EDGE_RELATION_DEFAULT_LABELS["derives"],
                )
                edges.append(edge)

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

    # =========================================================================
    # THINKING GRAPH: Intent Classification & Topic Management
    # =========================================================================

    async def _classify_message_intent(
        self,
        project_id: str,
        message: ChatMessage,
        recent_messages: List[ChatMessage],
    ) -> IntentClassificationResult:
        """
        Classify the intent of a message to determine how it connects to the thinking graph.

        Uses LLM to determine if the message is:
        - continuation: Follows up on the active topic
        - branch: Explores a related but different aspect
        - new_topic: Starts a completely new discussion

        Returns:
            IntentClassificationResult with intent type and optional parent topic
        """
        # Default to continuation if no LLM service
        if not self._llm_service:
            return IntentClassificationResult(
                intent=INTENT_CONTINUATION,
                confidence=0.5,
                reasoning="No LLM service available, defaulting to continuation",
            )

        # Get active topics for context
        topics = self._topic_contexts.get(project_id, [])
        active_topics_text = ""
        if topics:
            topics_list = []
            for t in topics[-5:]:  # Last 5 topics
                topics_list.append(f"- Topic {t.topic_id}: keywords={t.keywords}")
            active_topics_text = "\n".join(topics_list)
        else:
            active_topics_text = "No active topics yet."

        # Format recent conversation
        conv_history = ""
        for msg in recent_messages[-6:]:  # Last 6 messages
            role = "User" if msg.role == "user" else "AI"
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            conv_history += f"{role}: {content}\n"

        # Call LLM for intent classification
        system_prompt = THINKING_GRAPH_INTENT_CLASSIFICATION_PROMPT
        user_prompt = THINKING_GRAPH_INTENT_USER_PROMPT.format(
            active_topics=active_topics_text,
            conversation_history=conv_history,
            current_message=message.content,
        )

        messages = [
            LLMChatMessage(role="system", content=system_prompt),
            LLMChatMessage(role="user", content=user_prompt),
        ]

        try:
            response = await self._llm_service.chat(messages)
            content = response.content.strip()

            # Parse JSON response
            if content.startswith("```"):
                first_newline = content.find("\n")
                if first_newline != -1:
                    content = content[first_newline + 1 :]
                if content.endswith("```"):
                    content = content[:-3].strip()

            data = json.loads(content)

            return IntentClassificationResult(
                intent=data.get("intent", INTENT_CONTINUATION),
                confidence=data.get("confidence", 0.7),
                parent_topic_id=data.get("parent_topic_id"),
                reasoning=data.get("reasoning", ""),
            )
        except Exception as e:
            logger.warning(f"[ThinkingPath] Intent classification failed: {e}")
            return IntentClassificationResult(
                intent=INTENT_CONTINUATION,
                confidence=0.5,
                reasoning=f"Classification failed: {str(e)}",
            )

    async def _find_related_topic(
        self,
        project_id: str,
        message_content: str,
        threshold: float = 0.7,
    ) -> Optional[TopicContext]:
        """
        Find an existing topic that's semantically related to the message.

        Uses embedding similarity to find the most related topic.

        Returns:
            TopicContext if a related topic is found, None otherwise
        """
        topics = self._topic_contexts.get(project_id, [])
        if not topics:
            return None

        try:
            # Get embedding for the message
            message_embedding = await self._embedding_service.embed(message_content)

            # Find the most similar topic
            max_similarity = 0.0
            most_similar_topic = None

            for topic in topics:
                # Get or compute topic embedding
                if topic.topic_id not in self._topic_embedding_cache:
                    # Use keywords to create topic embedding
                    topic_text = " ".join(topic.keywords)
                    if topic_text:
                        topic_embedding = await self._embedding_service.embed(topic_text)
                        self._topic_embedding_cache[topic.topic_id] = topic_embedding
                    else:
                        continue

                topic_embedding = self._topic_embedding_cache.get(topic.topic_id)
                if not topic_embedding:
                    continue

                similarity = self._cosine_similarity(message_embedding, topic_embedding)

                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_topic = topic

            if max_similarity >= threshold and most_similar_topic:
                logger.info(
                    f"[ThinkingPath] Found related topic: {most_similar_topic.topic_id}, "
                    f"similarity={max_similarity:.3f}"
                )
                return most_similar_topic

            return None
        except Exception as e:
            logger.warning(f"[ThinkingPath] Failed to find related topic: {e}")
            return None

    def _create_new_topic(
        self,
        project_id: str,
        message_id: str,
        keywords: List[str],
        parent_topic_id: Optional[str] = None,
    ) -> TopicContext:
        """
        Create a new topic context.

        Args:
            project_id: Project ID
            message_id: ID of the message that starts this topic
            keywords: Keywords extracted from the message
            parent_topic_id: ID of the parent topic (if branching)

        Returns:
            The newly created TopicContext
        """
        topic_id = f"topic-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"

        # Determine depth based on parent
        depth = 0
        if parent_topic_id:
            parent_topic = self._get_topic_by_id(project_id, parent_topic_id)
            if parent_topic:
                depth = parent_topic.depth + 1

        topic = TopicContext(
            topic_id=topic_id,
            root_message_id=message_id,
            keywords=keywords,
            depth=depth,
            parent_topic_id=parent_topic_id,
        )

        # Add to topic contexts
        if project_id not in self._topic_contexts:
            self._topic_contexts[project_id] = []
        self._topic_contexts[project_id].append(topic)

        # Set as active topic
        self._active_topic[project_id] = topic_id

        logger.info(
            f"[ThinkingPath] Created new topic: {topic_id}, depth={depth}, parent={parent_topic_id}"
        )

        return topic

    def _get_topic_by_id(
        self,
        project_id: str,
        topic_id: str,
    ) -> Optional[TopicContext]:
        """Get a topic by its ID."""
        topics = self._topic_contexts.get(project_id, [])
        return next((t for t in topics if t.topic_id == topic_id), None)

    def _get_active_topic(self, project_id: str) -> Optional[TopicContext]:
        """Get the currently active topic for a project."""
        active_id = self._active_topic.get(project_id)
        if not active_id:
            return None
        return self._get_topic_by_id(project_id, active_id)

    def set_active_topic(self, project_id: str, topic_id: Optional[str]) -> None:
        """
        Set the active topic for a project.

        This is called from the frontend when user clicks on a node to set it as
        the "fork point" for new messages.

        Args:
            project_id: Project ID
            topic_id: Topic ID to set as active, or None to start a new topic
        """
        if topic_id:
            self._active_topic[project_id] = topic_id
        else:
            # Clear active topic - next message will create a new topic
            self._active_topic.pop(project_id, None)

        logger.info(f"[ThinkingPath] Active topic set to: {topic_id or 'None (new topic)'}")

    async def _extract_thinking_step(
        self,
        user_message: str,
        ai_response: str,
        context: str = "",
    ) -> Optional[ThinkingStepExtraction]:
        """
        Extract a structured thinking step from a message exchange.

        Uses the new THINKING_GRAPH_EXTRACTION prompt to get:
        - Structured step fields (claim, reason, evidence, etc.)
        - Related concepts
        - Suggested branches
        - Keywords for semantic matching

        Returns:
            ThinkingStepExtraction or None if extraction fails
        """
        if not self._llm_service:
            return None

        system_prompt = THINKING_GRAPH_EXTRACTION_SYSTEM_PROMPT
        user_prompt = THINKING_GRAPH_EXTRACTION_USER_PROMPT.format(
            user_message=user_message,
            ai_response=ai_response,
            context=context,
        )

        messages = [
            LLMChatMessage(role="system", content=system_prompt),
            LLMChatMessage(role="user", content=user_prompt),
        ]

        try:
            response = await self._llm_service.chat(messages)
            content = response.content.strip()

            # Parse JSON response
            if content.startswith("```"):
                first_newline = content.find("\n")
                if first_newline != -1:
                    content = content[first_newline + 1 :]
                if content.endswith("```"):
                    content = content[:-3].strip()

            data = json.loads(content)
            step = data.get("step", {})

            return ThinkingStepExtraction(
                claim=step.get("claim", ""),
                reason=step.get("reason", ""),
                evidence=step.get("evidence", ""),
                uncertainty=step.get("uncertainty", ""),
                decision=step.get("decision", ""),
                related_concepts=data.get("related_concepts", []),
                suggested_branches=data.get("suggested_branches", []),
                keywords=data.get("keywords", []),
            )
        except Exception as e:
            logger.warning(f"[ThinkingPath] Thinking step extraction failed: {e}")
            return None

    def get_topic_contexts(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all topic contexts for a project.

        Returns:
            List of topic context dictionaries
        """
        topics = self._topic_contexts.get(project_id, [])
        return [t.to_dict() for t in topics]

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

            # Clear topic tracking
            if project_id in self._topic_contexts:
                del self._topic_contexts[project_id]
            if project_id in self._active_topic:
                del self._active_topic[project_id]

            # Clear topic embedding cache
            topics_to_clear = [
                k for k in self._topic_embedding_cache.keys() if k.startswith(f"topic-")
            ]
            for key in topics_to_clear:
                del self._topic_embedding_cache[key]
        else:
            # Clear all cache
            self._embedding_cache.clear()
            self._question_node_cache.clear()
            self._last_question_node_id.clear()
            self._topic_contexts.clear()
            self._active_topic.clear()
            self._topic_embedding_cache.clear()

        logger.info(f"[ThinkingPath] Cache cleared for project: {project_id or 'all'}")
