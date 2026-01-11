"""Output domain entity for generated outputs (mindmaps, summaries, etc.)."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class OutputType(str, Enum):
    """Types of generated outputs."""

    MINDMAP = "mindmap"
    SUMMARY = "summary"
    FLASHCARDS = "flashcards"
    PODCAST = "podcast"
    QUIZ = "quiz"
    TIMELINE = "timeline"
    COMPARE = "compare"
    CUSTOM = "custom"
    ARTICLE = "article"  # Magic Cursor: Draft Article
    ACTION_LIST = "action_list"  # Magic Cursor: Action List


class OutputStatus(str, Enum):
    """Status of an output generation."""

    GENERATING = "generating"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class SourceRef:
    """Reference to source content for traceability.

    Supports multiple source types for future extensibility:
    - document: PDF, markdown, etc. (location = page number)
    - video/audio: Media files (location = timestamp in seconds)
    - web: URLs (location = URL with optional text fragment)
    - node: Canvas nodes (location = node ID)
    """

    source_id: str  # ID of the source entity (document_id, node_id, etc.)
    quote: str  # Exact quoted text or transcript segment
    source_type: str = "document"  # 'document', 'node', 'video', 'audio', 'web'
    location: Optional[str] = None  # Page number, timestamp, URL fragment, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sourceId": self.source_id,
            "sourceType": self.source_type,
            "location": self.location,
            "quote": self.quote,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceRef":
        """Create from dictionary."""
        return cls(
            source_id=data.get("sourceId", data.get("source_id", "")),
            source_type=data.get("sourceType", data.get("source_type", "document")),
            location=data.get("location"),
            quote=data.get("quote", ""),
        )


@dataclass
class MindmapNode:
    """Represents a node in a mindmap."""

    id: str
    label: str
    content: str = ""
    depth: int = 0
    parent_id: Optional[str] = None
    x: float = 0
    y: float = 0
    width: float = 200
    height: float = 100
    color: str = "default"
    status: str = "complete"  # "generating" | "complete" | "error"
    source_refs: List["SourceRef"] = field(default_factory=list)  # Source references for drilldown

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "label": self.label,
            "content": self.content,
            "depth": self.depth,
            "parentId": self.parent_id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "color": self.color,
            "status": self.status,
            "sourceRefs": [ref.to_dict() for ref in self.source_refs],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MindmapNode":
        """Create from dictionary."""
        source_refs_data = data.get("sourceRefs", data.get("source_refs", []))
        return cls(
            id=data["id"],
            label=data["label"],
            content=data.get("content", ""),
            depth=data.get("depth", 0),
            parent_id=data.get("parentId"),
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 200),
            height=data.get("height", 100),
            color=data.get("color", "default"),
            status=data.get("status", "complete"),
            source_refs=[SourceRef.from_dict(ref) for ref in source_refs_data],
        )


@dataclass
class MindmapEdge:
    """Represents an edge in a mindmap."""

    id: str
    source: str
    target: str
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MindmapEdge":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            source=data["source"],
            target=data["target"],
            label=data.get("label", ""),
        )


@dataclass
class MindmapData:
    """Data structure for a mindmap output."""

    nodes: List[MindmapNode] = field(default_factory=list)
    edges: List[MindmapEdge] = field(default_factory=list)
    root_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "rootId": self.root_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MindmapData":
        """Create from dictionary."""
        return cls(
            nodes=[MindmapNode.from_dict(n) for n in data.get("nodes", [])],
            edges=[MindmapEdge.from_dict(e) for e in data.get("edges", [])],
            root_id=data.get("rootId"),
        )

    def add_node(self, node: MindmapNode) -> None:
        """Add a node to the mindmap."""
        self.nodes.append(node)
        if node.depth == 0:
            self.root_id = node.id

    def add_edge(self, edge: MindmapEdge) -> None:
        """Add an edge to the mindmap."""
        self.edges.append(edge)

    def find_node(self, node_id: str) -> Optional[MindmapNode]:
        """Find a node by ID."""
        return next((n for n in self.nodes if n.id == node_id), None)

    def get_children(self, node_id: str) -> List[MindmapNode]:
        """Get child nodes of a given node."""
        return [n for n in self.nodes if n.parent_id == node_id]


# =============================================================================
# Summary Data Structures
# =============================================================================


@dataclass
class KeyFinding:
    """Represents a key finding in a summary."""

    label: str
    content: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "label": self.label,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyFinding":
        """Create from dictionary."""
        return cls(
            label=data["label"],
            content=data["content"],
        )


@dataclass
class SummaryData:
    """Data structure for a summary output."""

    summary: str
    key_findings: List[KeyFinding] = field(default_factory=list)
    document_title: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "summary": self.summary,
            "keyFindings": [kf.to_dict() for kf in self.key_findings],
            "documentTitle": self.document_title,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SummaryData":
        """Create from dictionary."""
        return cls(
            summary=data.get("summary", ""),
            key_findings=[KeyFinding.from_dict(kf) for kf in data.get("keyFindings", [])],
            document_title=data.get("documentTitle", ""),
        )


# =============================================================================
# Flashcard Data Structures
# =============================================================================


@dataclass
class Flashcard:
    """Represents a flashcard."""

    front: str
    back: str
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "front": self.front,
            "back": self.back,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Flashcard":
        """Create from dictionary."""
        return cls(
            front=data["front"],
            back=data["back"],
            notes=data.get("notes"),
        )


@dataclass
class FlashcardData:
    """Data structure for flashcards output."""

    cards: List[Flashcard] = field(default_factory=list)
    document_title: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "cards": [c.to_dict() for c in self.cards],
            "documentTitle": self.document_title,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlashcardData":
        """Create from dictionary."""
        return cls(
            cards=[Flashcard.from_dict(c) for c in data.get("cards", [])],
            document_title=data.get("documentTitle", ""),
        )


# =============================================================================
# Article Data Structures (Magic Cursor: Draft Article)
# =============================================================================


@dataclass
class ArticleSection:
    """Represents a section in an article."""

    heading: str
    content: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "heading": self.heading,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleSection":
        """Create from dictionary."""
        return cls(
            heading=data["heading"],
            content=data["content"],
        )


@dataclass
class ArticleData:
    """Data structure for an article output (Magic Cursor: Draft Article)."""

    title: str = ""
    sections: List[ArticleSection] = field(default_factory=list)
    source_refs: List[SourceRef] = field(default_factory=list)
    snapshot_context: Optional[Dict[str, Any]] = None  # Selection box coordinates

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections],
            "sourceRefs": [ref.to_dict() for ref in self.source_refs],
            "snapshotContext": self.snapshot_context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleData":
        """Create from dictionary."""
        return cls(
            title=data.get("title", ""),
            sections=[ArticleSection.from_dict(s) for s in data.get("sections", [])],
            source_refs=[SourceRef.from_dict(ref) for ref in data.get("sourceRefs", [])],
            snapshot_context=data.get("snapshotContext"),
        )


# =============================================================================
# Action List Data Structures (Magic Cursor: Action List)
# =============================================================================


@dataclass
class ActionItem:
    """Represents an action item in a task list."""

    id: str
    text: str
    done: bool = False
    priority: str = "medium"  # "high", "medium", "low"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "done": self.done,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionItem":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            text=data["text"],
            done=data.get("done", False),
            priority=data.get("priority", "medium"),
        )


@dataclass
class ActionListData:
    """Data structure for action list output (Magic Cursor: Action List)."""

    title: str = "Action Items"
    items: List[ActionItem] = field(default_factory=list)
    source_refs: List[SourceRef] = field(default_factory=list)
    snapshot_context: Optional[Dict[str, Any]] = None  # Selection box coordinates

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "title": self.title,
            "items": [item.to_dict() for item in self.items],
            "sourceRefs": [ref.to_dict() for ref in self.source_refs],
            "snapshotContext": self.snapshot_context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionListData":
        """Create from dictionary."""
        return cls(
            title=data.get("title", "Action Items"),
            items=[ActionItem.from_dict(item) for item in data.get("items", [])],
            source_refs=[SourceRef.from_dict(ref) for ref in data.get("sourceRefs", [])],
            snapshot_context=data.get("snapshotContext"),
        )


@dataclass
class Output:
    """Output entity - represents a generated output (mindmap, summary, etc.)."""

    id: UUID = field(default_factory=uuid4)
    project_id: Optional[UUID] = None
    output_type: OutputType = OutputType.MINDMAP
    source_ids: List[UUID] = field(default_factory=list)
    status: OutputStatus = OutputStatus.GENERATING
    title: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_complete(self, data: Dict[str, Any]) -> None:
        """Mark output as complete with data."""
        self.status = OutputStatus.COMPLETE
        self.data = data
        self.updated_at = datetime.utcnow()

    def mark_error(self, error_message: str) -> None:
        """Mark output as error."""
        self.status = OutputStatus.ERROR
        self.error_message = error_message
        self.updated_at = datetime.utcnow()

    def mark_cancelled(self) -> None:
        """Mark output as cancelled."""
        self.status = OutputStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    @property
    def is_complete(self) -> bool:
        """Check if output generation is complete."""
        return self.status == OutputStatus.COMPLETE

    @property
    def is_generating(self) -> bool:
        """Check if output is still being generated."""
        return self.status == OutputStatus.GENERATING

    def get_mindmap_data(self) -> Optional[MindmapData]:
        """Get mindmap data if this is a mindmap output."""
        if self.output_type != OutputType.MINDMAP or not self.data:
            return None
        return MindmapData.from_dict(self.data)

    def get_summary_data(self) -> Optional[SummaryData]:
        """Get summary data if this is a summary output."""
        if self.output_type != OutputType.SUMMARY or not self.data:
            return None
        return SummaryData.from_dict(self.data)

    def get_flashcard_data(self) -> Optional[FlashcardData]:
        """Get flashcard data if this is a flashcard output."""
        if self.output_type != OutputType.FLASHCARDS or not self.data:
            return None
        return FlashcardData.from_dict(self.data)

    def get_article_data(self) -> Optional[ArticleData]:
        """Get article data if this is an article output."""
        if self.output_type != OutputType.ARTICLE or not self.data:
            return None
        return ArticleData.from_dict(self.data)

    def get_action_list_data(self) -> Optional[ActionListData]:
        """Get action list data if this is an action list output."""
        if self.output_type != OutputType.ACTION_LIST or not self.data:
            return None
        return ActionListData.from_dict(self.data)
