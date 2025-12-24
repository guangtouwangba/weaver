"""Base class for output generation agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import UUID

from research_agent.infrastructure.llm.base import LLMService
from research_agent.shared.utils.logger import logger


class OutputEventType(str, Enum):
    """Event types for output generation streaming."""

    # Generation lifecycle events
    GENERATION_STARTED = "generation_started"
    GENERATION_PROGRESS = "generation_progress"
    GENERATION_COMPLETE = "generation_complete"
    GENERATION_ERROR = "generation_error"

    # Mindmap-specific events
    NODE_GENERATING = "node_generating"
    NODE_ADDED = "node_added"
    NODE_UPDATED = "node_updated"
    EDGE_ADDED = "edge_added"
    LEVEL_COMPLETE = "level_complete"

    # Token streaming (for explain)
    TOKEN = "token"


@dataclass
class OutputEvent:
    """Event emitted during output generation."""

    type: OutputEventType
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Node-related fields
    node_id: Optional[str] = None
    node_data: Optional[Dict[str, Any]] = None

    # Edge-related fields
    edge_id: Optional[str] = None
    edge_data: Optional[Dict[str, Any]] = None

    # Progress-related fields
    progress: Optional[float] = None  # 0.0 - 1.0
    current_level: Optional[int] = None
    total_levels: Optional[int] = None

    # Token streaming
    token: Optional[str] = None

    # Error-related fields
    error_message: Optional[str] = None

    # Generic message
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        result: Dict[str, Any] = {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
        }

        if self.node_id is not None:
            result["nodeId"] = self.node_id
        if self.node_data is not None:
            result["nodeData"] = self.node_data
        if self.edge_id is not None:
            result["edgeId"] = self.edge_id
        if self.edge_data is not None:
            result["edgeData"] = self.edge_data
        if self.progress is not None:
            result["progress"] = self.progress
        if self.current_level is not None:
            result["currentLevel"] = self.current_level
        if self.total_levels is not None:
            result["totalLevels"] = self.total_levels
        if self.token is not None:
            result["token"] = self.token
        if self.error_message is not None:
            result["errorMessage"] = self.error_message
        if self.message is not None:
            result["message"] = self.message

        return result


class BaseOutputAgent(ABC):
    """
    Base class for output generation agents.

    An output agent generates structured outputs (mindmaps, summaries, etc.)
    from document content, streaming events as it generates.

    Subclasses should implement:
    - generate(): Main generation logic
    - explain_node(): Explain a specific node (optional)
    - expand_node(): Expand a node with children (optional)
    """

    def __init__(
        self,
        llm_service: LLMService,
        max_tokens_per_request: int = 4000,
    ):
        """
        Initialize the agent.

        Args:
            llm_service: LLM service for text generation
            max_tokens_per_request: Maximum tokens to send per LLM request
        """
        self._llm = llm_service
        self._max_tokens = max_tokens_per_request

    @property
    @abstractmethod
    def output_type(self) -> str:
        """Return the output type this agent generates (e.g., 'mindmap', 'summary')."""
        pass

    @abstractmethod
    async def generate(
        self,
        document_content: str,
        document_title: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[OutputEvent]:
        """
        Generate output from document content.

        Args:
            document_content: Full document text or summary
            document_title: Optional document title for context
            **kwargs: Additional agent-specific parameters

        Yields:
            OutputEvent instances as generation progresses
        """
        pass

    async def explain_node(
        self,
        node_id: str,
        node_data: Dict[str, Any],
        document_content: str,
    ) -> AsyncIterator[OutputEvent]:
        """
        Explain a node's content.

        Default implementation streams explanation tokens.
        Subclasses can override for custom behavior.

        Args:
            node_id: ID of the node to explain
            node_data: Node data including label and content
            document_content: Document content for context

        Yields:
            OutputEvent with TOKEN type for each generated token
        """
        logger.info(f"[{self.output_type}Agent] Explaining node: {node_id}")

        # Default implementation - can be overridden
        yield OutputEvent(
            type=OutputEventType.GENERATION_ERROR,
            error_message="explain_node not implemented for this agent",
        )

    async def expand_node(
        self,
        node_id: str,
        node_data: Dict[str, Any],
        existing_children: List[Dict[str, Any]],
        document_content: str,
    ) -> AsyncIterator[OutputEvent]:
        """
        Expand a node by generating child nodes.

        Default implementation yields an error.
        Subclasses can override for custom behavior.

        Args:
            node_id: ID of the node to expand
            node_data: Node data including label and content
            existing_children: Existing child nodes to avoid duplicates
            document_content: Document content for context

        Yields:
            OutputEvent instances for new nodes and edges
        """
        logger.info(f"[{self.output_type}Agent] Expanding node: {node_id}")

        # Default implementation - can be overridden
        yield OutputEvent(
            type=OutputEventType.GENERATION_ERROR,
            error_message="expand_node not implemented for this agent",
        )

    def _truncate_content(self, content: str, max_chars: int = 50000) -> str:
        """
        Truncate content to fit within token limits.

        A rough estimate: 1 token ≈ 4 characters for English text.

        Args:
            content: Content to truncate
            max_chars: Maximum characters to keep

        Returns:
            Truncated content
        """
        if len(content) <= max_chars:
            return content

        # Keep first 80% and last 10% of max_chars
        front_chars = int(max_chars * 0.8)
        back_chars = int(max_chars * 0.1)

        truncated = content[:front_chars]
        truncated += "\n\n[... content truncated for length ...]\n\n"
        truncated += content[-back_chars:]

        logger.info(
            f"[{self.output_type}Agent] Truncated content from {len(content)} to {len(truncated)} chars"
        )

        return truncated

    def _emit_started(self, message: str = "Generation started") -> OutputEvent:
        """Create a generation started event."""
        return OutputEvent(type=OutputEventType.GENERATION_STARTED, message=message)

    def _emit_progress(
        self,
        progress: float,
        current_level: Optional[int] = None,
        total_levels: Optional[int] = None,
        message: Optional[str] = None,
    ) -> OutputEvent:
        """Create a progress event."""
        return OutputEvent(
            type=OutputEventType.GENERATION_PROGRESS,
            progress=progress,
            current_level=current_level,
            total_levels=total_levels,
            message=message,
        )

    def _emit_complete(self, message: str = "Generation complete") -> OutputEvent:
        """Create a generation complete event."""
        return OutputEvent(type=OutputEventType.GENERATION_COMPLETE, message=message)

    def _emit_error(self, error_message: str) -> OutputEvent:
        """Create an error event."""
        return OutputEvent(
            type=OutputEventType.GENERATION_ERROR,
            error_message=error_message,
        )

    def _emit_node_generating(
        self,
        node_id: str,
        node_data: Dict[str, Any],
    ) -> OutputEvent:
        """Create a node generating event."""
        return OutputEvent(
            type=OutputEventType.NODE_GENERATING,
            node_id=node_id,
            node_data=node_data,
        )

    def _emit_node_added(
        self,
        node_id: str,
        node_data: Dict[str, Any],
    ) -> OutputEvent:
        """Create a node added event."""
        return OutputEvent(
            type=OutputEventType.NODE_ADDED,
            node_id=node_id,
            node_data=node_data,
        )

    def _emit_edge_added(
        self,
        edge_id: str,
        edge_data: Dict[str, Any],
    ) -> OutputEvent:
        """Create an edge added event."""
        return OutputEvent(
            type=OutputEventType.EDGE_ADDED,
            edge_id=edge_id,
            edge_data=edge_data,
        )

    def _emit_level_complete(
        self,
        current_level: int,
        total_levels: int,
    ) -> OutputEvent:
        """Create a level complete event."""
        return OutputEvent(
            type=OutputEventType.LEVEL_COMPLETE,
            current_level=current_level,
            total_levels=total_levels,
        )

    def _emit_token(self, token: str) -> OutputEvent:
        """Create a token event for streaming text."""
        return OutputEvent(type=OutputEventType.TOKEN, token=token)

