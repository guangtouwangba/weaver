"""Domain entities."""

from research_agent.domain.entities.canvas import Canvas, CanvasEdge, CanvasNode
from research_agent.domain.entities.chunk import DocumentChunk
from research_agent.domain.entities.document import Document, DocumentStatus
from research_agent.domain.entities.graph import Entity, EntityType, KnowledgeGraph, Relation, RelationType
from research_agent.domain.entities.project import Project
from research_agent.domain.entities.task import Task, TaskStatus, TaskType

__all__ = [
    "Project",
    "Document",
    "DocumentStatus",
    "DocumentChunk",
    "Canvas",
    "CanvasNode",
    "CanvasEdge",
    "Task",
    "TaskStatus",
    "TaskType",
    "Entity",
    "EntityType",
    "Relation",
    "RelationType",
    "KnowledgeGraph",
]

