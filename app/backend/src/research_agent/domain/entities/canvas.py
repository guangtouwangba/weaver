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
class Canvas:
    """Canvas entity - represents the knowledge canvas for a project."""

    id: UUID = field(default_factory=uuid4)
    project_id: Optional[UUID] = None
    nodes: List[CanvasNode] = field(default_factory=list)
    edges: List[CanvasEdge] = field(default_factory=list)
    viewport: CanvasViewport = field(default_factory=CanvasViewport)
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
        return {
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

        viewport_data = data.get("viewport", {})
        viewport = CanvasViewport(
            x=viewport_data.get("x", 0),
            y=viewport_data.get("y", 0),
            scale=viewport_data.get("scale", 1),
        )

        return cls(
            project_id=project_id,
            nodes=nodes,
            edges=edges,
            viewport=viewport,
        )

