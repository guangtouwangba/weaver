"""Thinking Path domain entities for evidence-backed claims, questions, and concepts."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

# =============================================================================
# Enums
# =============================================================================


class ClaimStatus(str, Enum):
    """Status of a claim based on evidence support."""

    TENTATIVE = "tentative"  # Initial state, needs more evidence
    SUPPORTED = "supported"  # Has strong supporting evidence
    DISPUTED = "disputed"  # Has conflicting evidence
    ARCHIVED = "archived"  # No longer active


class QuestionStatus(str, Enum):
    """Status of a research question."""

    OPEN = "open"  # Not yet resolved
    INVESTIGATING = "investigating"  # Actively being researched
    ANSWERED = "answered"  # Has been resolved
    ARCHIVED = "archived"  # No longer active


class QuestionPriority(str, Enum):
    """Priority level for questions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnchorStatus(str, Enum):
    """Status of a source anchor."""

    VALID = "valid"  # Anchor is valid and can be located
    STALE = "stale"  # Source changed, anchor may be inaccurate
    BROKEN = "broken"  # Cannot locate the anchor in source


class CreatedFrom(str, Enum):
    """
    How a node was created (for Minimal Canvas audit).

    IMPORTANT: "import" is NOT allowed - this enforces the
    "no auto nodes on import" principle.
    """

    DRAG = "drag"  # Dragged from reader/assistant to canvas
    EXPLICIT_ACTION = "explicit_action"  # Explicit button click
    CHAT_SAVE = "chat_save"  # Saved from chat thinking path


class ThinkingPathEventType(str, Enum):
    """
    Types of events in the thinking path.

    MVP Whitelist - only these events are recorded:
    """

    # Node lifecycle
    CREATE_NODE = "create_node"
    UPDATE_NODE = "update_node"
    DELETE_NODE = "delete_node"

    # Anchor management
    ADD_ANCHOR = "add_anchor"
    REMOVE_ANCHOR = "remove_anchor"

    # Status/confidence changes
    CHANGE_CONFIDENCE = "change_confidence"
    CHANGE_STATUS = "change_status"

    # Relationships
    LINK_NODES = "link_nodes"
    UNLINK_NODES = "unlink_nodes"

    # Checkpoints
    CREATE_CHECKPOINT = "create_checkpoint"


class CheckpointMethod(str, Enum):
    """How a checkpoint was created."""

    MANUAL = "manual"  # User explicitly created
    AUTO_MILESTONE = "auto_milestone"  # System detected milestone
    SESSION_END = "session_end"  # End of work session


# =============================================================================
# Source Anchor
# =============================================================================


@dataclass
class PDFLocator:
    """Locator for PDF sources."""

    page: int
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    context_hash: Optional[str] = None  # Hash of surrounding text for validation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page": self.page,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "context_hash": self.context_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PDFLocator":
        return cls(
            page=data.get("page", 0),
            char_start=data.get("char_start"),
            char_end=data.get("char_end"),
            context_hash=data.get("context_hash"),
        )


@dataclass
class WebLocator:
    """Locator for web sources."""

    selector: Optional[str] = None  # CSS selector or XPath
    context_window: Optional[str] = None  # Surrounding text for validation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selector": self.selector,
            "context_window": self.context_window,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebLocator":
        return cls(
            selector=data.get("selector"),
            context_window=data.get("context_window"),
        )


@dataclass
class SourceAnchor:
    """
    A precise reference to a location within a source document.

    This is the atomic unit of evidence that supports or disputes claims.
    """

    id: UUID = field(default_factory=uuid4)
    project_id: Optional[UUID] = None
    source_type: str = "pdf"  # "pdf", "web", "chat", "manual"
    source_id: Optional[UUID] = None  # Document ID for PDFs
    source_url: Optional[str] = None  # URL for web sources
    quote_text: str = ""  # The actual quoted text
    locator: Dict[str, Any] = field(default_factory=dict)  # Type-specific locator
    status: AnchorStatus = AnchorStatus.VALID
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def get_pdf_locator(self) -> Optional[PDFLocator]:
        """Get PDF locator if source type is PDF."""
        if self.source_type == "pdf" and self.locator:
            return PDFLocator.from_dict(self.locator)
        return None

    def get_web_locator(self) -> Optional[WebLocator]:
        """Get web locator if source type is web."""
        if self.source_type == "web" and self.locator:
            return WebLocator.from_dict(self.locator)
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "projectId": str(self.project_id) if self.project_id else None,
            "sourceType": self.source_type,
            "sourceId": str(self.source_id) if self.source_id else None,
            "sourceUrl": self.source_url,
            "quoteText": self.quote_text,
            "locator": self.locator,
            "status": self.status.value if isinstance(self.status, AnchorStatus) else self.status,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# Node Types
# =============================================================================


@dataclass
class ClaimNode:
    """
    An evidence-backed claim on the canvas.

    Claims are statements that can be supported or disputed by source anchors.
    """

    id: UUID = field(default_factory=uuid4)
    project_id: Optional[UUID] = None
    canvas_node_id: str = ""  # Reference to visual node on canvas
    title: str = ""
    statement: str = ""
    confidence: int = 30  # 0-100 scale (30 = tentative default)
    status: ClaimStatus = ClaimStatus.TENTATIVE
    evidence_anchor_ids: List[str] = field(default_factory=list)
    counter_evidence_anchor_ids: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_from: CreatedFrom = CreatedFrom.DRAG
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_evidence(self, anchor_id: str) -> None:
        """Add supporting evidence."""
        if anchor_id not in self.evidence_anchor_ids:
            self.evidence_anchor_ids.append(anchor_id)
            self._update_confidence()
            self.updated_at = datetime.utcnow()

    def add_counter_evidence(self, anchor_id: str) -> None:
        """Add contradicting evidence."""
        if anchor_id not in self.counter_evidence_anchor_ids:
            self.counter_evidence_anchor_ids.append(anchor_id)
            self._update_status_on_dispute()
            self.updated_at = datetime.utcnow()

    def _update_confidence(self) -> None:
        """Auto-adjust confidence based on evidence count."""
        evidence_count = len(self.evidence_anchor_ids)
        if evidence_count >= 3:
            self.confidence = min(self.confidence + 20, 100)
        elif evidence_count >= 1:
            self.confidence = min(self.confidence + 10, 80)

    def _update_status_on_dispute(self) -> None:
        """Update status when counter-evidence is added."""
        if self.counter_evidence_anchor_ids:
            self.status = ClaimStatus.DISPUTED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "projectId": str(self.project_id) if self.project_id else None,
            "canvasNodeId": self.canvas_node_id,
            "title": self.title,
            "statement": self.statement,
            "confidence": self.confidence,
            "status": self.status.value if isinstance(self.status, ClaimStatus) else self.status,
            "evidenceAnchorIds": self.evidence_anchor_ids,
            "counterEvidenceAnchorIds": self.counter_evidence_anchor_ids,
            "assumptions": self.assumptions,
            "tags": self.tags,
            "createdFrom": self.created_from.value
            if isinstance(self.created_from, CreatedFrom)
            else self.created_from,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class QuestionNode:
    """
    A research question representing a structural hole in understanding.
    """

    id: UUID = field(default_factory=uuid4)
    project_id: Optional[UUID] = None
    canvas_node_id: str = ""
    question_text: str = ""
    status: QuestionStatus = QuestionStatus.OPEN
    related_claim_ids: List[str] = field(default_factory=list)
    related_concept_ids: List[str] = field(default_factory=list)
    priority: QuestionPriority = QuestionPriority.MEDIUM
    tags: List[str] = field(default_factory=list)
    created_from: CreatedFrom = CreatedFrom.DRAG
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "projectId": str(self.project_id) if self.project_id else None,
            "canvasNodeId": self.canvas_node_id,
            "questionText": self.question_text,
            "status": self.status.value if isinstance(self.status, QuestionStatus) else self.status,
            "relatedClaimIds": self.related_claim_ids,
            "relatedConceptIds": self.related_concept_ids,
            "priority": self.priority.value
            if isinstance(self.priority, QuestionPriority)
            else self.priority,
            "tags": self.tags,
            "createdFrom": self.created_from.value
            if isinstance(self.created_from, CreatedFrom)
            else self.created_from,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class ConceptDefinition:
    """A single definition for a concept."""

    text: str
    source_anchor_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "sourceAnchorId": self.source_anchor_id,
        }


@dataclass
class ConceptNode:
    """
    A concept representing key terminology and definitions.
    """

    id: UUID = field(default_factory=uuid4)
    project_id: Optional[UUID] = None
    canvas_node_id: str = ""
    name: str = ""
    definitions: List[ConceptDefinition] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    related_concept_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_from: CreatedFrom = CreatedFrom.DRAG
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_definition(self, text: str, source_anchor_id: Optional[str] = None) -> None:
        """Add a new definition."""
        self.definitions.append(ConceptDefinition(text=text, source_anchor_id=source_anchor_id))
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "projectId": str(self.project_id) if self.project_id else None,
            "canvasNodeId": self.canvas_node_id,
            "name": self.name,
            "definitions": [d.to_dict() for d in self.definitions],
            "synonyms": self.synonyms,
            "relatedConceptIds": self.related_concept_ids,
            "tags": self.tags,
            "createdFrom": self.created_from.value
            if isinstance(self.created_from, CreatedFrom)
            else self.created_from,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# Thinking Path Events and Checkpoints
# =============================================================================


@dataclass
class ThinkingPathEvent:
    """
    An event in the thinking path representing understanding evolution.
    """

    id: UUID = field(default_factory=uuid4)
    project_id: Optional[UUID] = None
    event_type: ThinkingPathEventType = ThinkingPathEventType.CREATE_NODE
    node_id: Optional[str] = None
    node_type: Optional[str] = None  # "claim", "question", "concept", "card"
    event_data: Dict[str, Any] = field(default_factory=dict)
    checkpoint_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "projectId": str(self.project_id) if self.project_id else None,
            "eventType": self.event_type.value
            if isinstance(self.event_type, ThinkingPathEventType)
            else self.event_type,
            "nodeId": self.node_id,
            "nodeType": self.node_type,
            "eventData": self.event_data,
            "checkpointId": str(self.checkpoint_id) if self.checkpoint_id else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class ThinkingPathCheckpoint:
    """
    A checkpoint marking a significant state in the thinking path.
    """

    id: UUID = field(default_factory=uuid4)
    project_id: Optional[UUID] = None
    title: str = ""
    description: Optional[str] = None
    canvas_summary: Dict[str, Any] = field(default_factory=dict)
    created_method: CheckpointMethod = CheckpointMethod.MANUAL
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "projectId": str(self.project_id) if self.project_id else None,
            "title": self.title,
            "description": self.description,
            "canvasSummary": self.canvas_summary,
            "createdMethod": self.created_method.value
            if isinstance(self.created_method, CheckpointMethod)
            else self.created_method,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# Resume Mode Summary
# =============================================================================


@dataclass
class ResumeModeSummary:
    """
    Summary for Resume Mode - quick re-entry into a project.
    """

    project_id: UUID
    # Top clusters (simplified MVP: just groups of related claims)
    top_clusters: List[Dict[str, Any]] = field(default_factory=list)
    # Open questions that need resolution
    open_questions: List[QuestionNode] = field(default_factory=list)
    # Recent changes (from thinking path events)
    recent_changes: List[ThinkingPathEvent] = field(default_factory=list)
    # Last checkpoint for quick jump
    last_checkpoint: Optional[ThinkingPathCheckpoint] = None
    # Summary stats
    total_claims: int = 0
    total_questions: int = 0
    total_concepts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "projectId": str(self.project_id),
            "topClusters": self.top_clusters,
            "openQuestions": [q.to_dict() for q in self.open_questions],
            "recentChanges": [e.to_dict() for e in self.recent_changes],
            "lastCheckpoint": self.last_checkpoint.to_dict() if self.last_checkpoint else None,
            "totalClaims": self.total_claims,
            "totalQuestions": self.total_questions,
            "totalConcepts": self.total_concepts,
        }




