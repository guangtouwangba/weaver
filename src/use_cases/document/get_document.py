"""
Get document use case.

Handles retrieving documents from the system.
"""

from typing import Optional

from ...core.entities.document import Document
from ...core.repositories.document_repository import DocumentRepository
from ..common.base_use_case import BaseUseCase
from ..common.exceptions import NotFoundError, ValidationError


class GetDocumentUseCase(BaseUseCase):
    """Use case for retrieving a document."""
    
    def __init__(self, document_repository: DocumentRepository):
        super().__init__()
        self._document_repository = document_repository
    
    async def execute(self, document_id: str) -> Document:
        """Execute the get document use case."""
        self.log_execution_start("get_document", document_id=document_id)
        
        try:
            # Validate input
            if not document_id or not document_id.strip():
                raise ValidationError("Document ID is required", "document_id")
            
            # Get document
            document = await self._document_repository.get_by_id(document_id)
            
            if not document:
                raise NotFoundError("Document", document_id)
            
            self.log_execution_end("get_document", document_id=document_id)
            return document
            
        except Exception as e:
            self.log_error("get_document", e, document_id=document_id)
            raise