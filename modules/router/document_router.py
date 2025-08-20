"""
Document Router

Main router implementation that orchestrates the document processing pipeline.
"""

from typing import List, AsyncIterator, Dict, Any
from datetime import datetime

from .interface import IRouter
from ..file_loader import IFileLoader, MultiFormatFileLoader
from ..document_processor import IDocumentProcessor, ChunkingProcessor
from ..models import (
    Document, SearchQuery, SearchResponse, ProcessingResult, SearchResult,
    ModuleConfig, RouterError, DocumentProcessorError, FileLoaderError
)


class DocumentRouter(IRouter):
    """Document router that orchestrates the processing pipeline."""
    
    def __init__(self, 
                 config: ModuleConfig = None,
                 file_loader: IFileLoader = None,
                 document_processor: IDocumentProcessor = None):
        super().__init__(config or ModuleConfig())
        
        # Initialize components
        self.file_loader = file_loader or MultiFormatFileLoader(self.config)
        self.document_processor = document_processor or ChunkingProcessor(self.config)
        
        # Document storage (in-memory for now)
        self._documents: Dict[str, Document] = {}
        self._document_chunks: Dict[str, List] = {}  # document_id -> chunks
    
    async def initialize(self):
        """Initialize the router and all components."""
        await super().initialize()
        
        # Initialize components
        await self.file_loader.initialize()
        await self.document_processor.initialize()
    
    async def cleanup(self):
        """Cleanup router and all components."""
        # Cleanup components
        await self.file_loader.cleanup()
        await self.document_processor.cleanup()
        
        # Clear storage
        self._documents.clear()
        self._document_chunks.clear()
        
        await super().cleanup()
    
    async def ingest_document(self, file_path: str) -> ProcessingResult:
        """Ingest a single document through the full pipeline."""
        start_time = datetime.now()
        
        try:
            # Step 1: Load document
            document = await self.file_loader.load_document(file_path)
            
            # Step 2: Process document (create chunks)
            processing_result = await self.document_processor.process_document(document)
            
            if not processing_result.success:
                return processing_result
            
            # Step 3: Store document and chunks
            self._documents[document.id] = document
            if 'chunks' in processing_result.metadata:
                self._document_chunks[document.id] = processing_result.metadata['chunks']
            
            # Calculate total processing time
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Return success result
            return ProcessingResult(
                success=True,
                document_id=document.id,
                chunks_created=processing_result.chunks_created,
                processing_time_ms=total_time,
                metadata={
                    'file_path': file_path,
                    'document_title': document.title,
                    'content_type': document.content_type.value,
                    'file_size': document.file_size,
                    'loading_time_ms': processing_result.processing_time_ms,
                    'total_documents_stored': len(self._documents)
                }
            )
            
        except FileLoaderError as e:
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            return ProcessingResult(
                success=False,
                processing_time_ms=total_time,
                error_message=f"File loading failed: {e}",
                metadata={'file_path': file_path, 'stage': 'file_loading'}
            )
            
        except DocumentProcessorError as e:
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            return ProcessingResult(
                success=False,
                processing_time_ms=total_time,
                error_message=f"Document processing failed: {e}",
                metadata={'file_path': file_path, 'stage': 'document_processing'}
            )
            
        except Exception as e:
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            return ProcessingResult(
                success=False,
                processing_time_ms=total_time,
                error_message=f"Unexpected error: {e}",
                metadata={'file_path': file_path, 'stage': 'unknown'}
            )
    
    async def ingest_documents_batch(self, file_paths: List[str]) -> AsyncIterator[ProcessingResult]:
        """Ingest multiple documents in batch."""
        for file_path in file_paths:
            result = await self.ingest_document(file_path)
            yield result
    
    async def search_documents(self, query: SearchQuery) -> SearchResponse:
        """Search documents using simple text matching."""
        start_time = datetime.now()
        
        try:
            results = []
            
            # Simple keyword search implementation
            query_lower = query.query.lower()
            
            for doc_id, document in self._documents.items():
                # Skip if document doesn't match filters
                if query.document_ids and doc_id not in query.document_ids:
                    continue
                
                if query.content_types and document.content_type not in query.content_types:
                    continue
                
                if query.tags and not any(tag in document.tags for tag in query.tags):
                    continue
                
                if query.created_after and document.created_at < query.created_after:
                    continue
                
                if query.created_before and document.created_at > query.created_before:
                    continue
                
                # Simple text matching
                content_lower = document.content.lower()
                if query_lower in content_lower:
                    # Calculate simple relevance score
                    score = content_lower.count(query_lower) / len(content_lower.split())
                    
                    # Search in chunks if available
                    chunks = self._document_chunks.get(doc_id, [])
                    for chunk in chunks:
                        if query_lower in chunk.content.lower():
                            result = SearchResult(
                                chunk=chunk,
                                score=score,
                                rank=len(results) + 1,
                                metadata={
                                    'document_title': document.title,
                                    'match_type': 'chunk_content'
                                }
                            )
                            results.append(result)
                            
                            if len(results) >= query.max_results:
                                break
                    
                    if len(results) >= query.max_results:
                        break
            
            # Sort by score (descending)
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Update ranks
            for i, result in enumerate(results):
                result.rank = i + 1
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return SearchResponse(
                query=query.query,
                results=results[:query.max_results],
                total_results=len(results),
                processing_time_ms=processing_time,
                metadata={
                    'search_strategy': 'simple_text_matching',
                    'documents_searched': len(self._documents),
                    'chunks_searched': sum(len(chunks) for chunks in self._document_chunks.values())
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return SearchResponse(
                query=query.query,
                results=[],
                total_results=0,
                processing_time_ms=processing_time,
                metadata={
                    'error': str(e),
                    'search_failed': True
                }
            )
    
    async def get_document_by_id(self, document_id: str) -> Document:
        """Retrieve a specific document by ID."""
        document = self._documents.get(document_id)
        if not document:
            raise RouterError(f"Document not found: {document_id}")
        return document
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and its chunks."""
        try:
            # Remove document
            if document_id in self._documents:
                del self._documents[document_id]
            
            # Remove chunks
            if document_id in self._document_chunks:
                del self._document_chunks[document_id]
            
            return True
            
        except Exception as e:
            raise RouterError(f"Failed to delete document {document_id}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get router status."""
        status = super().get_status()
        
        status.update({
            'total_documents': len(self._documents),
            'total_chunks': sum(len(chunks) for chunks in self._document_chunks.values()),
            'file_loader_status': self.file_loader.get_status(),
            'document_processor_status': self.document_processor.get_status(),
            'supported_formats': self.file_loader.supported_formats()
        })
        
        return status