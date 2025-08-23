"""
Router Interface

Defines the contract for routing and orchestration implementations.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional

from ...schemas import Document
from ...models import (
    ModuleConfig,
    ModuleInterface,
    ProcessingResult,
    SearchQuery,
    SearchResponse,
)


class RouterError(Exception):
    """Router错误"""

    def __init__(self, message: str, error_code: Optional[str] = None):
        self.error_code = error_code
        super().__init__(message)


class IRouter(ModuleInterface):
    """Router interface for orchestrating module interactions."""

    @abstractmethod
    async def ingest_document(self, file_path: str) -> ProcessingResult:
        """
        Ingest a single document through the full pipeline.

        Args:
            file_path: Path to the document file

        Returns:
            ProcessingResult: Result of the ingestion process

        Raises:
            RouterError: If ingestion fails
        """
        pass

    @abstractmethod
    async def ingest_documents_batch(
        self, file_paths: List[str]
    ) -> AsyncIterator[ProcessingResult]:
        """
        Ingest multiple documents in batch.

        Args:
            file_paths: List of document file paths

        Yields:
            ProcessingResult: Result for each document ingestion
        """
        pass

    @abstractmethod
    async def search_documents(self, query: SearchQuery) -> SearchResponse:
        """
        Search for documents using the configured retrieval strategy.

        Args:
            query: Search query specification

        Returns:
            SearchResponse: Search results

        Raises:
            RouterError: If search fails
        """
        pass

    @abstractmethod
    async def get_document_by_id(self, document_id: str) -> Document:
        """
        Retrieve a specific document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document: The requested document

        Raises:
            RouterError: If document not found or retrieval fails
        """
        pass

    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and all its associated data.

        Args:
            document_id: Document identifier

        Returns:
            bool: True if deletion was successful

        Raises:
            RouterError: If deletion fails
        """
        pass
