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
    sub_type: Optional[str] = None  # 'source' for PDF documents
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
    file_metadata: Optional[Dict[str, Any]] = None  # Metadata including thumbnail URL
    # New fields for view system
    view_type: str = "free"  # 'free' | 'thinking'
    section_id: Optional[str] = None
    promoted_from: Optional[str] = None  # Weak reference to original node
    generation: int = 1  # Generation ID for async clear support
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CanvasEdge:
    """Canvas edge entity - represents a connection between nodes."""

    source: str
    target: str
    id: Optional[str] = None
    generation: int = 1  # Generation ID for async clear support


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
    generation: int = 1  # Generation ID for async clear support
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
    user_id: Optional[str] = None
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
    current_generation: int = 1  # Current generation for async clear
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_node(self, node: CanvasNode) -> None:
        """Add a node to the canvas with current generation."""
        # Ensure node has current generation
        node.generation = self.current_generation
        self.nodes.append(node)
        self.updated_at = datetime.utcnow()

    def remove_node(self, node_id: str) -> None:
        """Remove a node and its connections."""
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.edges = [e for e in self.edges if e.source != node_id and e.target != node_id]
        self.updated_at = datetime.utcnow()

    def add_edge(self, edge: CanvasEdge) -> None:
        """Add an edge to the canvas with current generation."""
        # Ensure edge has current generation
        edge.generation = self.current_generation
        self.edges.append(edge)
        self.updated_at = datetime.utcnow()

    def add_section(self, section: CanvasSection) -> None:
        """Add a section to the canvas with current generation."""
        # Ensure section has current generation
        section.generation = self.current_generation
        self.sections.append(section)
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
                if "file_metadata" in kwargs:
                    node.file_metadata = kwargs["file_metadata"]
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

    def find_node(self, node_id: str, current_only: bool = True) -> Optional[CanvasNode]:
        """Find a node by ID.

        Args:
            node_id: The ID of the node to find.
            current_only: If True, only search in current generation nodes.
        """
        for node in self.nodes:
            if node.id == node_id:
                if current_only and node.generation != self.current_generation:
                    continue
                return node
        return None

    def get_visible_nodes(self) -> List[CanvasNode]:
        """Get all nodes in the current generation."""
        return [n for n in self.nodes if n.generation == self.current_generation]

    def get_visible_edges(self) -> List[CanvasEdge]:
        """Get all edges in the current generation."""
        return [e for e in self.edges if e.generation == self.current_generation]

    def get_visible_sections(self) -> List[CanvasSection]:
        """Get all sections in the current generation."""
        return [s for s in self.sections if s.generation == self.current_generation]

    def get_old_items_count(self) -> int:
        """Get count of items from previous generations (pending cleanup)."""
        old_nodes = sum(1 for n in self.nodes if n.generation < self.current_generation)
        old_edges = sum(1 for e in self.edges if e.generation < self.current_generation)
        old_sections = sum(1 for s in self.sections if s.generation < self.current_generation)
        return old_nodes + old_edges + old_sections

    def remove_old_items(self, generation_threshold: Optional[int] = None) -> int:
        """Remove items from generations below the threshold.

        Args:
            generation_threshold: Remove items with generation < threshold.
                                  If None, uses current_generation.

        Returns:
            Number of items removed.
        """
        threshold = generation_threshold or self.current_generation

        old_nodes_count = len([n for n in self.nodes if n.generation < threshold])
        old_edges_count = len([e for e in self.edges if e.generation < threshold])
        old_sections_count = len([s for s in self.sections if s.generation < threshold])

        self.nodes = [n for n in self.nodes if n.generation >= threshold]
        self.edges = [e for e in self.edges if e.generation >= threshold]
        self.sections = [s for s in self.sections if s.generation >= threshold]

        removed_count = old_nodes_count + old_edges_count + old_sections_count
        if removed_count > 0:
            self.updated_at = datetime.utcnow()

        return removed_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert canvas to dictionary for storage."""
        result = {
            "currentGeneration": self.current_generation,
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "subType": n.sub_type,
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
                    "fileMetadata": n.file_metadata,
                    "viewType": n.view_type,
                    "sectionId": n.section_id,
                    "promotedFrom": n.promoted_from,
                    "generation": n.generation,
                    "createdAt": n.created_at.isoformat() if n.created_at else None,
                    "updatedAt": n.updated_at.isoformat() if n.updated_at else None,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "generation": e.generation,
                }
                for e in self.edges
            ],
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
                    "generation": s.generation,
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

    def to_visible_dict(self) -> Dict[str, Any]:
        """Convert canvas to dictionary, only including current generation items.

        This is used for API responses where old (cleared) items should be hidden.
        """
        visible_nodes = self.get_visible_nodes()
        visible_edges = self.get_visible_edges()
        visible_sections = self.get_visible_sections()

        result = {
            "currentGeneration": self.current_generation,
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "subType": n.sub_type,
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
                    "fileMetadata": n.file_metadata,
                    "viewType": n.view_type,
                    "sectionId": n.section_id,
                    "promotedFrom": n.promoted_from,
                    "generation": n.generation,
                    "createdAt": n.created_at.isoformat() if n.created_at else None,
                    "updatedAt": n.updated_at.isoformat() if n.updated_at else None,
                }
                for n in visible_nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "generation": e.generation,
                }
                for e in visible_edges
            ],
            "viewport": {
                "x": self.viewport.x,
                "y": self.viewport.y,
                "scale": self.viewport.scale,
            },
        }

        # Add sections if any
        if visible_sections:
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
                    "generation": s.generation,
                    "createdAt": s.created_at.isoformat() if s.created_at else None,
                    "updatedAt": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in visible_sections
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
    def from_dict(
        cls, data: Dict[str, Any], project_id: UUID, user_id: Optional[str] = None
    ) -> "Canvas":
        """Create canvas from dictionary."""
        current_generation = data.get("currentGeneration", 1)

        nodes = [
            CanvasNode(
                id=n["id"],
                type=n.get("type", "card"),
                sub_type=n.get("subType"),
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
                file_metadata=n.get("fileMetadata"),
                view_type=n.get("viewType", "free"),  # Default to 'free' for backward compatibility
                section_id=n.get("sectionId"),
                promoted_from=n.get("promotedFrom"),
                generation=n.get(
                    "generation", current_generation
                ),  # Default to current generation for backward compatibility
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
                generation=e.get("generation", current_generation),  # Default to current generation
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
                generation=s.get("generation", current_generation),  # Default to current generation
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
            user_id=user_id,
            nodes=nodes,
            edges=edges,
            sections=sections,
            viewport=viewport,
            view_states=view_states,
            current_generation=current_generation,
        )

    @classmethod
    def create_empty(cls, project_id: UUID, user_id: Optional[str] = None) -> "Canvas":
        """Create an empty canvas for a project."""
        return cls(
            project_id=project_id,
            user_id=user_id,
            nodes=[],
            edges=[],
            sections=[],
            viewport=CanvasViewport(),
            view_states={},
        )

    def clear(self) -> int:
        """Clear all items by incrementing generation (async-friendly).

        Instead of immediately deleting items, this increments the generation.
        Old items remain in storage but are invisible. A background task can
        later call remove_old_items() to physically delete them.

        Returns:
            The previous generation number (useful for cleanup task).
        """
        previous_generation = self.current_generation
        self.current_generation += 1
        self.updated_at = datetime.utcnow()
        return previous_generation

    def clear_view(self, view_type: str) -> int:
        """Clear only items for a specific view type by incrementing generation.

        Items from other view types are upgraded to the new generation,
        so they remain visible. Items of the specified view_type stay at the
        old generation and become invisible.

        Args:
            view_type: 'free' or 'thinking'

        Returns:
            The previous generation number (useful for cleanup task).
        """
        previous_generation = self.current_generation
        self.current_generation += 1

        # Upgrade nodes from other view types to the new generation
        for node in self.nodes:
            if node.view_type != view_type and node.generation == previous_generation:
                node.generation = self.current_generation

        # Upgrade sections from other view types to the new generation
        for section in self.sections:
            if section.view_type != view_type and section.generation == previous_generation:
                section.generation = self.current_generation

        # Upgrade edges: only if both connected nodes are in the new generation
        visible_node_ids = {n.id for n in self.nodes if n.generation == self.current_generation}
        for edge in self.edges:
            if edge.generation == previous_generation:
                if edge.source in visible_node_ids and edge.target in visible_node_ids:
                    edge.generation = self.current_generation

        self.updated_at = datetime.utcnow()
        return previous_generation

    def clear_sync(self) -> None:
        """Synchronously clear all nodes, edges, and sections (legacy method).

        Use clear() for async-friendly clearing with generation support.
        """
        self.nodes = []
        self.edges = []
        self.sections = []
        self.updated_at = datetime.utcnow()

    def clear_view_sync(self, view_type: str) -> None:
        """Synchronously clear items for a specific view type (legacy method).

        Use clear_view() for async-friendly clearing with generation support.

        Args:
            view_type: 'free' or 'thinking'
        """
        # Get IDs of nodes to remove
        nodes_to_remove = {n.id for n in self.nodes if n.view_type == view_type}

        # Remove nodes of the specified view type
        self.nodes = [n for n in self.nodes if n.view_type != view_type]

        # Remove edges that connect to removed nodes
        self.edges = [
            e
            for e in self.edges
            if e.source not in nodes_to_remove and e.target not in nodes_to_remove
        ]

        # Remove sections of the specified view type
        self.sections = [s for s in self.sections if s.view_type != view_type]

        self.updated_at = datetime.utcnow()
