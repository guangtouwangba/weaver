"""Domain entities."""

from research_agent.domain.entities.canvas import Canvas, CanvasEdge, CanvasNode
from research_agent.domain.entities.chunk import DocumentChunk
from research_agent.domain.entities.config import (
    CitationFormat,
    EmbeddingConfig,
    GenerationConfig,
    IntentClassificationConfig,
    IntentType,
    LLMConfig,
    LongContextConfig,
    RAGConfig,
    RAGMode,
    RetrievalConfig,
    RetrievalStrategyType,
)
from research_agent.domain.entities.document import Document, DocumentStatus
from research_agent.domain.entities.graph import (
    Entity,
    EntityType,
    KnowledgeGraph,
    Relation,
    RelationType,
)
from research_agent.domain.entities.project import Project
from research_agent.domain.entities.task import Task, TaskStatus, TaskType

__all__ = [
    # Project & Document
    "Project",
    "Document",
    "DocumentStatus",
    "DocumentChunk",
    # Canvas
    "Canvas",
    "CanvasNode",
    "CanvasEdge",
    # Task
    "Task",
    "TaskStatus",
    "TaskType",
    # Knowledge Graph
    "Entity",
    "EntityType",
    "Relation",
    "RelationType",
    "KnowledgeGraph",
    # Configuration Entities
    "RAGConfig",
    "RAGMode",
    "LLMConfig",
    "EmbeddingConfig",
    "RetrievalConfig",
    "RetrievalStrategyType",
    "GenerationConfig",
    "CitationFormat",
    "IntentClassificationConfig",
    "IntentType",
    "LongContextConfig",
]
