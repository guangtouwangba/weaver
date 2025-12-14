"""Document repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from research_agent.domain.entities.document import Document


class DocumentRepository(ABC):
    """Abstract document repository interface."""

    @abstractmethod
    async def save(self, document: Document) -> Document:
        """Save a document."""
        pass

    @abstractmethod
    async def find_by_id(self, document_id: UUID) -> Optional[Document]:
        """Find document by ID."""
        pass

    @abstractmethod
    async def find_by_project(self, project_id: UUID) -> List[Document]:
        """Find all documents for a project."""
        pass

    @abstractmethod
    async def delete(self, document_id: UUID) -> bool:
        """Delete a document."""
        pass

