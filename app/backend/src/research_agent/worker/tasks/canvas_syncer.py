"""Canvas sync task for updating canvas with knowledge graph data."""

import math
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.canvas import Canvas, CanvasEdge, CanvasNode
from research_agent.domain.entities.graph import EntityType
from research_agent.infrastructure.database.models import CanvasModel, EntityModel, RelationModel
from research_agent.shared.utils.logger import logger
from research_agent.worker.tasks.base import BaseTask


# Color mapping for entity types
ENTITY_COLOR_MAP = {
    "person": "#3B82F6",      # Blue
    "organization": "#10B981", # Green
    "concept": "#8B5CF6",     # Purple
    "technology": "#F59E0B",  # Orange
    "product": "#EAB308",     # Yellow
    "event": "#EF4444",       # Red
    "location": "#06B6D4",    # Cyan
    "document": "#6B7280",    # Gray
    "topic": "#EC4899",       # Pink
    "other": "#9CA3AF",       # Default gray
}


class CanvasSyncerTask(BaseTask):
    """Task for syncing knowledge graph to canvas."""

    @property
    def task_type(self) -> str:
        return "sync_canvas"

    async def execute(self, payload: Dict[str, Any], session: AsyncSession) -> None:
        """
        Sync knowledge graph entities and relations to canvas.
        
        Payload:
            project_id: UUID of the project
            document_id: Optional UUID of the document (to sync only that document's graph)
        """
        project_id = UUID(payload["project_id"])
        document_id = payload.get("document_id")
        if document_id:
            document_id = UUID(document_id)
        
        logger.info(f"Starting canvas sync for project {project_id}")
        
        # Get entities and relations
        entities = await self._get_entities(session, project_id, document_id)
        relations = await self._get_relations(session, project_id)
        
        if not entities:
            logger.info("No entities to sync")
            return
        
        # Calculate layout positions
        positions = self._calculate_layout(entities, relations)
        
        # Convert to canvas nodes and edges
        nodes = self._create_canvas_nodes(entities, positions)
        edges = self._create_canvas_edges(relations)
        
        # Get or create canvas
        canvas = await self._get_or_create_canvas(session, project_id)
        
        # Merge new nodes with existing canvas
        await self._merge_to_canvas(session, canvas, nodes, edges)
        
        logger.info(f"Canvas sync completed: {len(nodes)} nodes, {len(edges)} edges")

    async def _get_entities(
        self,
        session: AsyncSession,
        project_id: UUID,
        document_id: UUID = None,
    ) -> List[EntityModel]:
        """Get entities for the project."""
        stmt = select(EntityModel).where(EntityModel.project_id == project_id)
        
        if document_id:
            stmt = stmt.where(EntityModel.document_id == document_id)
        
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _get_relations(
        self,
        session: AsyncSession,
        project_id: UUID,
    ) -> List[RelationModel]:
        """Get relations for the project."""
        stmt = select(RelationModel).where(RelationModel.project_id == project_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    def _calculate_layout(
        self,
        entities: List[EntityModel],
        relations: List[RelationModel],
    ) -> Dict[UUID, Dict[str, float]]:
        """
        Calculate layout positions for entities using a force-directed algorithm.
        
        Returns dict mapping entity ID to {x, y} position.
        """
        if not entities:
            return {}
        
        # Simple circular layout with some randomization based on connections
        n = len(entities)
        positions = {}
        
        # Build adjacency for connection counting
        connections = {e.id: 0 for e in entities}
        for r in relations:
            if r.source_entity_id in connections:
                connections[r.source_entity_id] += 1
            if r.target_entity_id in connections:
                connections[r.target_entity_id] += 1
        
        # Sort entities by connection count (more connected = more central)
        sorted_entities = sorted(entities, key=lambda e: connections.get(e.id, 0), reverse=True)
        
        # Use a spiral layout - more connected nodes are closer to center
        center_x, center_y = 500, 400
        base_radius = 150
        
        for i, entity in enumerate(sorted_entities):
            if i == 0:
                # Most connected entity at center
                x, y = center_x, center_y
            else:
                # Spiral outward
                angle = (i - 1) * (2 * math.pi / max(n - 1, 1)) * 2.5  # Golden angle-ish
                radius = base_radius + (i * 50)  # Increase radius as we go
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
            
            positions[entity.id] = {"x": x, "y": y}
        
        return positions

    def _create_canvas_nodes(
        self,
        entities: List[EntityModel],
        positions: Dict[UUID, Dict[str, float]],
    ) -> List[CanvasNode]:
        """Create canvas nodes from entities."""
        nodes = []
        
        for entity in entities:
            pos = positions.get(entity.id, {"x": 100, "y": 100})
            color = ENTITY_COLOR_MAP.get(entity.entity_type, ENTITY_COLOR_MAP["other"])
            
            node = CanvasNode(
                id=f"entity_{entity.id}",
                type="card",
                title=entity.name,
                content=entity.description or "",
                x=pos["x"],
                y=pos["y"],
                width=200,
                height=120,
                color=color,
                tags=[entity.entity_type],
                source_id=str(entity.document_id) if entity.document_id else None,
            )
            nodes.append(node)
        
        return nodes

    def _create_canvas_edges(
        self,
        relations: List[RelationModel],
    ) -> List[CanvasEdge]:
        """Create canvas edges from relations."""
        edges = []
        
        for relation in relations:
            edge = CanvasEdge(
                id=f"relation_{relation.id}",
                source=f"entity_{relation.source_entity_id}",
                target=f"entity_{relation.target_entity_id}",
            )
            edges.append(edge)
        
        return edges

    async def _get_or_create_canvas(
        self,
        session: AsyncSession,
        project_id: UUID,
    ) -> CanvasModel:
        """Get existing canvas or create new one."""
        stmt = select(CanvasModel).where(CanvasModel.project_id == project_id)
        result = await session.execute(stmt)
        canvas = result.scalar_one_or_none()
        
        if not canvas:
            canvas = CanvasModel(
                project_id=project_id,
                data={"nodes": [], "edges": [], "viewport": {"x": 0, "y": 0, "scale": 1}},
            )
            session.add(canvas)
            await session.flush()
        
        return canvas

    async def _merge_to_canvas(
        self,
        session: AsyncSession,
        canvas: CanvasModel,
        new_nodes: List[CanvasNode],
        new_edges: List[CanvasEdge],
    ) -> None:
        """Merge new nodes and edges into existing canvas."""
        existing_data = canvas.data or {"nodes": [], "edges": [], "viewport": {"x": 0, "y": 0, "scale": 1}}
        existing_nodes = existing_data.get("nodes", [])
        existing_edges = existing_data.get("edges", [])
        
        # Get existing node IDs
        existing_node_ids = {n.get("id") for n in existing_nodes}
        existing_edge_ids = {e.get("id") for e in existing_edges}
        
        # Add new nodes that don't exist
        for node in new_nodes:
            if node.id not in existing_node_ids:
                existing_nodes.append({
                    "id": node.id,
                    "type": node.type,
                    "title": node.title,
                    "content": node.content,
                    "x": node.x,
                    "y": node.y,
                    "width": node.width,
                    "height": node.height,
                    "color": node.color,
                    "tags": node.tags,
                    "sourceId": node.source_id,
                    "sourcePage": node.source_page,
                })
        
        # Add new edges that don't exist
        for edge in new_edges:
            if edge.id not in existing_edge_ids:
                existing_edges.append({
                    "id": edge.id,
                    "source": edge.source,
                    "target": edge.target,
                })
        
        # Update canvas data
        canvas.data = {
            "nodes": existing_nodes,
            "edges": existing_edges,
            "viewport": existing_data.get("viewport", {"x": 0, "y": 0, "scale": 1}),
        }
        
        await session.flush()

