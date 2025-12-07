"""Canvas domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class CanvasNode:
    """Canvas node entity - represents a card on the canvas."""

    id: str
    type: str = "card"
    title: str = ""
    content: str = ""
    x: float = 0
    y: float = 0
    width: float = 200
    height: float = 150
    color: str = "default"
    tags: List[str] = field(default_factory=list)
    source_id: Optional[str] = None  # Document ID if from PDF
    source_page: Optional[int] = None  # Page number if from PDF
    # New fields for view system
    view_type: str = "free"  # 'free' | 'thinking'
    section_id: Optional[str] = None
    promoted_from: Optional[str] = None  # Weak reference to original node
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CanvasEdge:
    """Canvas edge entity - represents a connection between nodes."""

    source: str
    target: str
    id: Optional[str] = None


@dataclass
class CanvasViewport:
    """Canvas viewport state."""

    x: float = 0
    y: float = 0
    scale: float = 1


@dataclass
class CanvasSection:
    """Canvas section entity - represents a container for grouping nodes."""

    id: str
    title: str
    view_type: str = "free"  # 'free' | 'thinking'
    is_collapsed: bool = False
    node_ids: List[str] = field(default_factory=list)
    x: float = 0
    y: float = 0
    width: Optional[float] = None  # Auto-calculated from nodes
    height: Optional[float] = None  # Auto-calculated from nodes
    conversation_id: Optional[str] = None  # For thinking path sections
    question: Optional[str] = None  # For thinking path sections
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CanvasViewState:
    """Canvas view state - independent state for each view."""

    view_type: str  # 'free' | 'thinking'
    viewport: CanvasViewport
    selected_node_ids: List[str] = field(default_factory=list)
    collapsed_section_ids: List[str] = field(default_factory=list)


@dataclass
class Canvas:
    """Canvas entity - represents the knowledge canvas for a project."""

    id: UUID = field(default_factory=uuid4)
    project_id: Optional[UUID] = None
    nodes: List[CanvasNode] = field(default_factory=list)
    edges: List[CanvasEdge] = field(default_factory=list)
    sections: List[CanvasSection] = field(default_factory=list)
    viewport: CanvasViewport = field(
        default_factory=CanvasViewport
    )  # Legacy: default viewport for backward compatibility
    view_states: Dict[str, CanvasViewState] = field(
        default_factory=dict
    )  # Key: 'free' | 'thinking'
    version: int = 1  # Version for optimistic locking
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_node(self, node: CanvasNode) -> None:
        """Add a node to the canvas."""
        self.nodes.append(node)
        self.updated_at = datetime.utcnow()

    def remove_node(self, node_id: str) -> None:
        """Remove a node and its connections."""
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.edges = [e for e in self.edges if e.source != node_id and e.target != node_id]
        self.updated_at = datetime.utcnow()

    def add_edge(self, edge: CanvasEdge) -> None:
        """Add an edge to the canvas."""
        self.edges.append(edge)
        self.updated_at = datetime.utcnow()

    def update_node(self, node_id: str, **kwargs) -> bool:
        """Update a node's properties."""
        for node in self.nodes:
            if node.id == node_id:
                # Update only provided fields
                if "type" in kwargs:
                    node.type = kwargs["type"]
                if "title" in kwargs:
                    node.title = kwargs["title"]
                if "content" in kwargs:
                    node.content = kwargs["content"]
                if "x" in kwargs:
                    node.x = kwargs["x"]
                if "y" in kwargs:
                    node.y = kwargs["y"]
                if "width" in kwargs:
                    node.width = kwargs["width"]
                if "height" in kwargs:
                    node.height = kwargs["height"]
                if "color" in kwargs:
                    node.color = kwargs["color"]
                if "tags" in kwargs:
                    node.tags = kwargs["tags"]
                if "source_id" in kwargs:
                    node.source_id = kwargs["source_id"]
                if "source_page" in kwargs:
                    node.source_page = kwargs["source_page"]
                if "view_type" in kwargs:
                    node.view_type = kwargs["view_type"]
                if "section_id" in kwargs:
                    node.section_id = kwargs["section_id"]
                if "promoted_from" in kwargs:
                    node.promoted_from = kwargs["promoted_from"]
                node.updated_at = datetime.utcnow()
                self.updated_at = datetime.utcnow()
                return True
        return False

    def find_node(self, node_id: str) -> Optional[CanvasNode]:
        """Find a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert canvas to dictionary for storage."""
        result = {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "title": n.title,
                    "content": n.content,
                    "x": n.x,
                    "y": n.y,
                    "width": n.width,
                    "height": n.height,
                    "color": n.color,
                    "tags": n.tags,
                    "sourceId": n.source_id,
                    "sourcePage": n.source_page,
                    "viewType": n.view_type,
                    "sectionId": n.section_id,
                    "promotedFrom": n.promoted_from,
                    "createdAt": n.created_at.isoformat() if n.created_at else None,
                    "updatedAt": n.updated_at.isoformat() if n.updated_at else None,
                }
                for n in self.nodes
            ],
            "edges": [{"id": e.id, "source": e.source, "target": e.target} for e in self.edges],
            "viewport": {
                "x": self.viewport.x,
                "y": self.viewport.y,
                "scale": self.viewport.scale,
            },
        }

        # Add sections if any
        if self.sections:
            result["sections"] = [
                {
                    "id": s.id,
                    "title": s.title,
                    "viewType": s.view_type,
                    "isCollapsed": s.is_collapsed,
                    "nodeIds": s.node_ids,
                    "x": s.x,
                    "y": s.y,
                    "width": s.width,
                    "height": s.height,
                    "conversationId": s.conversation_id,
                    "question": s.question,
                    "createdAt": s.created_at.isoformat() if s.created_at else None,
                    "updatedAt": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in self.sections
            ]

        # Add view states if any
        if self.view_states:
            result["viewStates"] = {
                view_type: {
                    "viewType": vs.view_type,
                    "viewport": {
                        "x": vs.viewport.x,
                        "y": vs.viewport.y,
                        "scale": vs.viewport.scale,
                    },
                    "selectedNodeIds": vs.selected_node_ids,
                    "collapsedSectionIds": vs.collapsed_section_ids,
                }
                for view_type, vs in self.view_states.items()
            }

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any], project_id: UUID) -> "Canvas":
        """Create canvas from dictionary."""
        nodes = [
            CanvasNode(
                id=n["id"],
                type=n.get("type", "card"),
                title=n.get("title", ""),
                content=n.get("content", ""),
                x=n.get("x", 0),
                y=n.get("y", 0),
                width=n.get("width", 200),
                height=n.get("height", 150),
                color=n.get("color", "default"),
                tags=n.get("tags", []),
                source_id=n.get("sourceId"),
                source_page=n.get("sourcePage"),
                view_type=n.get("viewType", "free"),  # Default to 'free' for backward compatibility
                section_id=n.get("sectionId"),
                promoted_from=n.get("promotedFrom"),
                created_at=datetime.fromisoformat(n["createdAt"])
                if n.get("createdAt")
                else datetime.utcnow(),
                updated_at=datetime.fromisoformat(n["updatedAt"])
                if n.get("updatedAt")
                else datetime.utcnow(),
            )
            for n in data.get("nodes", [])
        ]

        edges = [
            CanvasEdge(
                id=e.get("id"),
                source=e["source"],
                target=e["target"],
            )
            for e in data.get("edges", [])
        ]

        sections = [
            CanvasSection(
                id=s["id"],
                title=s.get("title", ""),
                view_type=s.get("viewType", "free"),
                is_collapsed=s.get("isCollapsed", False),
                node_ids=s.get("nodeIds", []),
                x=s.get("x", 0),
                y=s.get("y", 0),
                width=s.get("width"),
                height=s.get("height"),
                conversation_id=s.get("conversationId"),
                question=s.get("question"),
                created_at=datetime.fromisoformat(s["createdAt"])
                if s.get("createdAt")
                else datetime.utcnow(),
                updated_at=datetime.fromisoformat(s["updatedAt"])
                if s.get("updatedAt")
                else datetime.utcnow(),
            )
            for s in data.get("sections", [])
        ]

        viewport_data = data.get("viewport", {})
        viewport = CanvasViewport(
            x=viewport_data.get("x", 0),
            y=viewport_data.get("y", 0),
            scale=viewport_data.get("scale", 1),
        )

        # Parse view states
        view_states = {}
        view_states_data = data.get("viewStates", {})
        for view_type, vs_data in view_states_data.items():
            vs_viewport_data = vs_data.get("viewport", {})
            view_states[view_type] = CanvasViewState(
                view_type=vs_data.get("viewType", view_type),
                viewport=CanvasViewport(
                    x=vs_viewport_data.get("x", 0),
                    y=vs_viewport_data.get("y", 0),
                    scale=vs_viewport_data.get("scale", 1),
                ),
                selected_node_ids=vs_data.get("selectedNodeIds", []),
                collapsed_section_ids=vs_data.get("collapsedSectionIds", []),
            )

        return cls(
            project_id=project_id,
            nodes=nodes,
            edges=edges,
            sections=sections,
            viewport=viewport,
            view_states=view_states,
        )
