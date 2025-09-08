"""
Process file use case.

Handles processing uploaded files into documents.
"""

from typing import Optional, Dict, Any

from ...core.entities.document import Document
from ...core.entities.file import File
from ...core.repositories.document_repository import DocumentRepository
from ...core.repositories.file_repository import FileRepository
from ...core.domain_services.document_processing_service import DocumentProcessingService
from ...core.domain_services.vector_search_service import VectorSearchService
from ..common.base_use_case import BaseUseCase
from ..common.exceptions import NotFoundError, ValidationError, BusinessRuleViolationError


class ProcessFileRequest:
    """Request model for processing a file."""
    
    def __init__(
        self,
        file_id: str,
        title: Optional[str] = None,
        chunking_strategy: str = "fixed_size",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        generate_summary: bool = True,
        extract_keywords: bool = True
    ):
        self.file_id = file_id
        self.title = title
        self.chunking_strategy = chunking_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.generate_summary = generate_summary
        self.extract_keywords = extract_keywords


class ProcessFileResult:
    """Result model for file processing."""
    
    def __init__(
        self,
        document: Document,
        chunks_created: int,
        processing_time: float,
        summary: Optional[str] = None,
        keywords: Optional[list] = None
    ):
        self.document = document
        self.chunks_created = chunks_created
        self.processing_time = processing_time
        self.summary = summary
        self.keywords = keywords


class ProcessFileUseCase(BaseUseCase):
    """Use case for processing a file into a document."""
    
    def __init__(
        self,
        file_repository: FileRepository,
        document_repository: DocumentRepository,
        processing_service: DocumentProcessingService,
        vector_search_service: VectorSearchService
    ):
        super().__init__()
        self._file_repository = file_repository
        self._document_repository = document_repository
        self._processing_service = processing_service
        self._vector_search_service = vector_search_service
    
    async def execute(self, request: ProcessFileRequest) -> ProcessFileResult:
        """Execute the process file use case."""
        import time
        start_time = time.time()
        
        self.log_execution_start("process_file", file_id=request.file_id)
        
        try:
            # Validate input
            self._validate_request(request)
            
            # Get file
            file = await self._file_repository.get_by_id(request.file_id)
            if not file:
                raise NotFoundError("File", request.file_id)
            
            # Check if file is available for processing
            if not file.is_available():
                raise BusinessRuleViolationError(
                    f"File is not available for processing. Current status: {file.status.value}"
                )
            
            # Mark file as processing
            file.mark_as_processing()
            await self._file_repository.save(file)
            
            try:
                # Extract text content
                content = self._processing_service.extract_text(
                    file.storage_key, 
                    file.content_type
                )
                
                # Generate title if not provided
                title = request.title or file.original_name
                
                # Create document
                document = Document(
                    title=title,
                    content=content,
                    content_type=file.content_type,
                    file_id=file.id,
                    file_path=file.storage_key,
                    file_size=file.file_size,
                    status="processing"
                )
                
                # Extract metadata
                metadata = self._processing_service.extract_metadata(file.storage_key, content)
                
                # Generate summary if requested
                summary = None
                if request.generate_summary and content:
                    summary = self._processing_service.generate_summary(content)
                    metadata["summary"] = summary
                
                # Extract keywords if requested
                keywords = None
                if request.extract_keywords and content:
                    keywords = self._processing_service.extract_keywords(content)
                    metadata["keywords"] = keywords
                
                document.metadata = metadata
                
                # Save document
                await self._document_repository.save(document)
                
                # Process chunks
                chunks = self._processing_service.chunk_content(
                    content,
                    chunk_size=request.chunk_size,
                    overlap=request.chunk_overlap,
                    strategy=request.chunking_strategy
                )
                
                # Generate embeddings for chunks
                chunks_with_embeddings = []
                for chunk in chunks:
                    embedding = await self._vector_search_service.generate_embedding(chunk.content)
                    chunk_with_embedding = chunk.with_embedding(embedding)
                    chunks_with_embeddings.append(chunk_with_embedding)
                
                # Save chunks
                await self._document_repository.save_chunks(chunks_with_embeddings)
                
                # Index chunks for search
                await self._vector_search_service.index_chunks(chunks_with_embeddings)
                
                # Update document status
                document.update_status("completed", "indexed")
                await self._document_repository.save(document)
                
                # Mark file as available
                file.mark_as_available()
                await self._file_repository.save(file)
                
                processing_time = time.time() - start_time
                
                result = ProcessFileResult(
                    document=document,
                    chunks_created=len(chunks_with_embeddings),
                    processing_time=processing_time,
                    summary=summary,
                    keywords=keywords
                )
                
                self.log_execution_end("process_file", 
                                     file_id=request.file_id, 
                                     document_id=document.id,
                                     chunks_created=len(chunks_with_embeddings))
                return result
                
            except Exception as e:
                # Mark file as failed and document as failed
                file.mark_as_failed()
                await self._file_repository.save(file)
                
                if 'document' in locals():
                    document.update_status("failed", str(e))
                    await self._document_repository.save(document)
                
                raise
            
        except Exception as e:
            self.log_error("process_file", e, file_id=request.file_id)
            raise
    
    def _validate_request(self, request: ProcessFileRequest) -> None:
        """Validate the process file request."""
        if not request.file_id or not request.file_id.strip():
            raise ValidationError("File ID is required", "file_id")
        
        if request.chunk_size <= 0 or request.chunk_size > 10000:
            raise ValidationError("Chunk size must be between 1 and 10000", "chunk_size")
        
        if request.chunk_overlap < 0 or request.chunk_overlap >= request.chunk_size:
            raise ValidationError("Chunk overlap must be between 0 and chunk_size", "chunk_overlap")
        
        valid_strategies = ["fixed_size", "sentence", "paragraph", "semantic", "recursive"]
        if request.chunking_strategy not in valid_strategies:
            raise ValidationError(f"Invalid chunking strategy. Must be one of: {valid_strategies}", "chunking_strategy")