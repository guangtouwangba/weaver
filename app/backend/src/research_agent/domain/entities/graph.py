"""Knowledge graph domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""

    PERSON = "person"
    ORGANIZATION = "organization"
    CONCEPT = "concept"
    TECHNOLOGY = "technology"
    PRODUCT = "product"
    EVENT = "event"
    LOCATION = "location"
    DOCUMENT = "document"
    TOPIC = "topic"
    OTHER = "other"


class RelationType(str, Enum):
    """Types of relations in the knowledge graph."""

    RELATED_TO = "related_to"
    PART_OF = "part_of"
    CREATED_BY = "created_by"
    USES = "uses"
    BELONGS_TO = "belongs_to"
    MENTIONED_IN = "mentioned_in"
    COMPARED_TO = "compared_to"
    DEPENDS_ON = "depends_on"
    INFLUENCES = "influences"
    SIMILAR_TO = "similar_to"
    CONTRASTS_WITH = "contrasts_with"
    IMPLEMENTS = "implements"
    DERIVED_FROM = "derived_from"
    OTHER = "other"


@dataclass
class Entity:
    """Entity - represents a node in the knowledge graph."""

    id: UUID = field(default_factory=uuid4)
    project_id: UUID | None = None
    document_id: UUID | None = None
    name: str = ""
    entity_type: EntityType = EntityType.CONCEPT
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_canvas_node(self, x: float = 0, y: float = 0) -> dict[str, Any]:
        """Convert entity to canvas node format."""
        # Map entity types to colors
        color_map = {
            EntityType.PERSON: "blue",
            EntityType.ORGANIZATION: "green",
            EntityType.CONCEPT: "purple",
            EntityType.TECHNOLOGY: "orange",
            EntityType.PRODUCT: "yellow",
            EntityType.EVENT: "red",
            EntityType.LOCATION: "cyan",
            EntityType.DOCUMENT: "gray",
            EntityType.TOPIC: "pink",
            EntityType.OTHER: "default",
        }

        return {
            "id": f"entity_{self.id}",
            "type": "card",
            "title": self.name,
            "content": self.description or "",
            "x": x,
            "y": y,
            "width": 200,
            "height": 150,
            "color": color_map.get(self.entity_type, "default"),
            "tags": [self.entity_type.value],
            "sourceId": str(self.document_id) if self.document_id else None,
            "sourcePage": None,
        }


@dataclass
class Relation:
    """Relation - represents an edge in the knowledge graph."""

    id: UUID = field(default_factory=uuid4)
    project_id: UUID | None = None
    source_entity_id: UUID | None = None
    target_entity_id: UUID | None = None
    relation_type: RelationType = RelationType.RELATED_TO
    description: str | None = None
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_canvas_edge(self) -> dict[str, Any]:
        """Convert relation to canvas edge format."""
        return {
            "id": f"relation_{self.id}",
            "source": f"entity_{self.source_entity_id}",
            "target": f"entity_{self.target_entity_id}",
            "label": self.relation_type.value.replace("_", " "),
        }


@dataclass
class KnowledgeGraph:
    """Knowledge graph containing entities and relations."""

    entities: list[Entity] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the graph."""
        self.entities.append(entity)

    def add_relation(self, relation: Relation) -> None:
        """Add a relation to the graph."""
        self.relations.append(relation)

    def get_entity_by_name(self, name: str) -> Entity | None:
        """Find an entity by name (case-insensitive)."""
        name_lower = name.lower()
        for entity in self.entities:
            if entity.name.lower() == name_lower:
                return entity
        return None

    def merge_entity(self, entity: Entity) -> Entity:
        """Merge entity with existing one if name matches, or add new."""
        existing = self.get_entity_by_name(entity.name)
        if existing:
            # Update description if new one is longer
            if entity.description and (not existing.description or len(entity.description) > len(existing.description)):
                existing.description = entity.description
            # Merge metadata
            existing.metadata.update(entity.metadata)
            return existing
        else:
            self.entities.append(entity)
            return entity

