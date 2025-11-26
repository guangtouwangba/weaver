"""Domain repository interfaces."""

from research_agent.domain.repositories.canvas_repo import CanvasRepository
from research_agent.domain.repositories.chunk_repo import ChunkRepository
from research_agent.domain.repositories.document_repo import DocumentRepository
from research_agent.domain.repositories.project_repo import ProjectRepository

__all__ = [
    "ProjectRepository",
    "DocumentRepository",
    "ChunkRepository",
    "CanvasRepository",
]

