"""
Create document use case.

Handles the creation of new documents in the system.
"""

from typing import Optional, Dict, Any

from ...core.entities.document import Document
from ...core.repositories.document_repository import DocumentRepository
from ...core.domain_services.document_processing_service import DocumentProcessingService
from ...core.domain_services.vector_search_service import VectorSearchService
from ...core.events.event_dispatcher import EventDispatcher
from ...core.events.document_events import DocumentProcessedEvent
from ..common.base_use_case import BaseUseCase
from ..common.exceptions import ValidationError


class CreateDocumentRequest:
    """Request model for creating a document."""
    
    def __init__(
        self,
        title: str,
        content: str,
        content_type: str = "text",
        file_id: Optional[str] = None,
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.content = content
        self.content_type = content_type
        self.file_id = file_id
        self.file_path = file_path
        self.metadata = metadata or {}


class CreateDocumentUseCase(BaseUseCase):
    """Use case for creating a new document."""
    
    def __init__(
        self,
        document_repository: DocumentRepository,
        processing_service: DocumentProcessingService,
        vector_search_service: VectorSearchService,
        event_dispatcher: EventDispatcher = None
    ):
        super().__init__()
        self._document_repository = document_repository
        self._processing_service = processing_service
        self._vector_search_service = vector_search_service
        self._event_dispatcher = event_dispatcher
    
    async def execute(self, request: CreateDocumentRequest) -> Document:
        """Execute the create document use case."""
        self.log_execution_start("create_document", title=request.title)
        
        try:
            # Validate input
            self._validate_request(request)
            
            # Process content if needed
            processed_content = self._processing_service.clean_content(request.content)
            
            # Extract additional metadata
            extracted_metadata = self._processing_service.extract_metadata("", processed_content)
            combined_metadata = {**request.metadata, **extracted_metadata}
            
            # Create document entity
            document = Document(
                title=request.title,
                content=processed_content,
                content_type=request.content_type,
                file_id=request.file_id,
                file_path=request.file_path,
                metadata=combined_metadata,
                status="created"
            )
            
            # Mark as created and publish event
            document.mark_as_created()
            
            # Save document
            await self._document_repository.save(document)
            
            # Dispatch domain events
            if self._event_dispatcher:
                for event in document.get_domain_events():
                    await self._event_dispatcher.dispatch(event)
                document.clear_domain_events()
            
            # Process document for chunking and indexing (async)
            await self._process_document_async(document)
            
            self.log_execution_end("create_document", document_id=document.id)
            return document
            
        except Exception as e:
            self.log_error("create_document", e, title=request.title)
            raise
    
    def _validate_request(self, request: CreateDocumentRequest) -> None:
        """Validate the create document request."""
        if not request.title or not request.title.strip():
            raise ValidationError("Document title is required", "title")
        
        if not request.content or not request.content.strip():
            raise ValidationError("Document content is required", "content")
        
        if len(request.title) > 500:
            raise ValidationError("Document title too long (max 500 characters)", "title")
        
        # Validate content
        if not self._processing_service.validate_content(request.content):
            raise ValidationError("Document content is not suitable for processing", "content")
    
    async def _process_document_async(self, document: Document) -> None:
        """Process document for chunking and indexing."""
        try:
            # Update status to processing
            document.update_status("processing", "chunking")
            await self._document_repository.save(document)
            
            # Create chunks
            chunks = self._processing_service.chunk_content(document.content)
            
            # Generate embeddings and index chunks
            chunks_with_embeddings = []
            for chunk in chunks:
                embedding = await self._vector_search_service.generate_embedding(chunk.content)
                chunk_with_embedding = chunk.with_embedding(embedding)
                chunks_with_embeddings.append(chunk_with_embedding)
            
            # Save chunks
            await self._document_repository.save_chunks(chunks_with_embeddings)
            
            # Index chunks for search
            await self._vector_search_service.index_chunks(chunks_with_embeddings)
            
            # Update document status to completed
            document.update_status("completed", "indexed")
            await self._document_repository.save(document)
            
            # Publish document processed event
            if self._event_dispatcher:
                import time
                processing_time = time.time() - time.time()  # This would be calculated properly
                event = DocumentProcessedEvent.create(
                    document_id=document.id,
                    chunks_created=len(chunks_with_embeddings),
                    processing_time=processing_time
                )
                await self._event_dispatcher.dispatch(event)
            
        except Exception as e:
            # Update document status to failed
            document.update_status("failed", str(e))
            await self._document_repository.save(document)
            self.log_error("process_document_async", e, document_id=document.id)