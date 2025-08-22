"""
Modular API interface definitions

Define unified, simplified API interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from ..models import Document, DocumentChunk, SearchResult


class APIError(Exception):
    """API error"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class IModularAPI(ABC):
    """Modular API interface"""

    @abstractmethod
    async def process_file(self, file_path: str, **options) -> Dict[str, Any]:
        """
        Process single file

        Args:
            file_path: File path
            **options: Processing options

        Returns:
            Dict[str, Any]: Processing result

        Raises:
            APIError: Thrown when processing fails
        """
        pass

    @abstractmethod
    async def process_files(
        self, file_paths: List[str], **options
    ) -> List[Dict[str, Any]]:
        """
        Batch process files

        Args:
            file_paths: List of file paths
            **options: Processing options

        Returns:
            List[Dict[str, Any]]: List of processing results
        """
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 10, **filters) -> Dict[str, Any]:
        """
        Search documents

        Args:
            query: Search query
            limit: Result count limit
            **filters: Search filters

        Returns:
            Dict[str, Any]: Search results
        """
        pass

    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document

        Args:
            document_id: Document ID

        Returns:
            Optional[Dict[str, Any]]: Document information, returns None if not exists
        """
        pass

    @abstractmethod
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get document chunks

        Args:
            document_id: Document ID

        Returns:
            List[Dict[str, Any]]: List of document chunks
        """
        pass

    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document

        Args:
            document_id: Document ID

        Returns:
            bool: Whether deletion was successful
        """
        pass

    @abstractmethod
    async def update_document_metadata(
        self, document_id: str, metadata: Dict[str, Any]
    ) -> bool:
        """
        Update document metadata

        Args:
            document_id: Document ID
            metadata: New metadata

        Returns:
            bool: Whether update was successful
        """
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Get system status

        Returns:
            Dict[str, Any]: System status information
        """
        pass

    @abstractmethod
    async def get_supported_formats(self) -> List[str]:
        """
        Get supported file formats

        Returns:
            List[str]: List of supported formats
        """
        pass
