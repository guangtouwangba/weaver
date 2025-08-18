"""
RAG Application Services

This module contains application services that orchestrate RAG domain operations,
following the DDD application layer pattern.
"""

import logging
from typing import Optional
from datetime import datetime
import asyncio

# Domain interfaces
from domain.rag_interfaces import (
    IDocumentLoader, IDocumentProcessor, IVectorStore, IIndexManager,
    ISearchService, IKnowledgeManager, IEmbeddingService, SearchStrategy, ProcessingStatus,
    DocumentLoadError, DocumentProcessingError, IndexingError, SearchError
)

# DTOs
from application.dtos.rag import (
    DocumentIngestionRequest, BatchIngestionRequest, SearchRequest,
    CreateIndexRequest, UpdateDocumentRequest, DeleteDocumentRequest,
    DocumentListRequest, EmbeddingRequest, SimilaritySearchRequest,
    SystemHealthRequest, ProcessingResponse, BatchProcessingResponse, DocumentResponse,
    SearchResponse, IndexResponse, DocumentListResponse, EmbeddingResponse,
    SimilaritySearchResponse, SystemHealthResponse
)

# Models

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Application service for document management operations.
    
    This service coordinates document loading, processing, and indexing operations
    while maintaining the separation of concerns (SRP).
    """
    
    def __init__(self,
                 document_loader: IDocumentLoader,
                 document_processor: IDocumentProcessor,
                 knowledge_manager: IKnowledgeManager,
                 index_manager: IIndexManager):
        """
        Initialize document service with required dependencies.
        
        Args:
            document_loader: Document loading interface
            document_processor: Document processing interface  
            knowledge_manager: Knowledge management interface
            index_manager: Index management interface
        """
        self.document_loader = document_loader
        self.document_processor = document_processor
        self.knowledge_manager = knowledge_manager
        self.index_manager = index_manager
    
    async def ingest_document(self, request: DocumentIngestionRequest) -> ProcessingResponse:
        """
        Complete document ingestion workflow.
        
        Args:
            request: Document ingestion request
            
        Returns:
            ProcessingResponse: Ingestion result
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting document ingestion: {request.source}")
            
            # 1. Load document
            document = await self.document_loader.load_document(
                request.source,
                source_type=request.source_type,
                document_format=request.document_format
            )
            
            # 2. Set document metadata from request
            document.title = request.title or document.title
            document.metadata.update(request.metadata)
            if request.category:
                document.metadata['category'] = request.category
            if request.tags:
                document.metadata['tags'] = request.tags
            if request.author:
                document.metadata['author'] = request.author
            
            # 3. Process document (chunking, etc.)
            processing_config = {
                'chunk_strategy': request.chunk_strategy.value,
                'chunk_size': request.chunk_size,
                'chunk_overlap': request.chunk_overlap,
                'enable_ocr': request.enable_ocr,
                'extract_images': request.extract_images,
                'enable_auto_tagging': request.enable_auto_tagging,
                'enable_summary': request.enable_summary
            }
            
            processing_result = await self.document_processor.process_document(
                document, **processing_config
            )
            
            if not processing_result.success:
                return ProcessingResponse(
                    success=False,
                    document_id=document.id,
                    status=ProcessingStatus.FAILED,
                    message=processing_result.message,
                    errors=processing_result.errors,
                    processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )
            
            # 4. Add to knowledge base
            knowledge_result = await self.knowledge_manager.add_document(document)
            
            if not knowledge_result.success:
                return ProcessingResponse(
                    success=False,
                    document_id=document.id,
                    status=ProcessingStatus.FAILED,
                    message=f"Failed to add to knowledge base: {knowledge_result.message}",
                    errors=knowledge_result.errors,
                    processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )
            
            # 5. Index document
            index_result = await self.index_manager.index_document(
                document, request.index_name
            )
            
            if not index_result.success:
                # Try to rollback knowledge base addition
                try:
                    await self.knowledge_manager.delete_document(document.id)
                except Exception as e:
                    logger.error(f"Failed to rollback knowledge base addition: {e}")
                
                return ProcessingResponse(
                    success=False,
                    document_id=document.id,
                    status=ProcessingStatus.FAILED,
                    message=f"Failed to index document: {index_result.message}",
                    errors=index_result.errors,
                    processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ProcessingResponse(
                success=True,
                document_id=document.id,
                status=ProcessingStatus.COMPLETED,
                message=f"Successfully ingested document: {document.title}",
                chunks_created=processing_result.chunks_created,
                processing_time_ms=processing_time,
                file_size_bytes=document.file_size,
                metadata={
                    'processing_result': processing_result.metadata,
                    'knowledge_result': knowledge_result.metadata,
                    'index_result': index_result.metadata
                }
            )
            
        except DocumentLoadError as e:
            return ProcessingResponse(
                success=False,
                status=ProcessingStatus.FAILED,
                message=f"Document load error: {str(e)}",
                errors=[str(e)],
                processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
        except DocumentProcessingError as e:
            return ProcessingResponse(
                success=False,
                status=ProcessingStatus.FAILED,
                message=f"Document processing error: {str(e)}",
                errors=[str(e)],
                processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
        except IndexingError as e:
            return ProcessingResponse(
                success=False,
                status=ProcessingStatus.FAILED,
                message=f"Indexing error: {str(e)}",
                errors=[str(e)],
                processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
        except Exception as e:
            logger.error(f"Unexpected error during document ingestion: {e}")
            return ProcessingResponse(
                success=False,
                status=ProcessingStatus.FAILED,
                message=f"Unexpected error: {str(e)}",
                errors=[str(e)],
                processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
    
    async def ingest_documents_batch(self, request: BatchIngestionRequest) -> BatchProcessingResponse:
        """
        Batch document ingestion with parallel processing.
        
        Args:
            request: Batch ingestion request
            
        Returns:
            BatchProcessingResponse: Batch processing result
        """
        start_time = datetime.utcnow()
        total_documents = len(request.sources)
        
        logger.info(f"Starting batch ingestion of {total_documents} documents")
        
        # Create semaphore for parallel processing
        semaphore = asyncio.Semaphore(request.max_parallel)
        
        async def process_single(source: str) -> ProcessingResponse:
            async with semaphore:
                # Use common config or per-source config
                config = request.per_source_config.get(source, request.common_config) \
                    if request.per_source_config else request.common_config
                
                if not config:
                    config = DocumentIngestionRequest(source=source)
                else:
                    # Update source in config
                    config.source = source
                
                return await self.ingest_document(config)
        
        # Process all documents
        tasks = [process_single(source) for source in request.sources]
        
        if request.fail_fast:
            # Stop on first failure
            results = []
            for task in tasks:
                result = await task
                results.append(result)
                if not result.success:
                    # Cancel remaining tasks
                    for remaining_task in tasks[len(results):]:
                        remaining_task.cancel()
                    break
        else:
            # Process all regardless of failures
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to error responses
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    results[i] = ProcessingResponse(
                        success=False,
                        status=ProcessingStatus.FAILED,
                        message=f"Exception during processing: {str(result)}",
                        errors=[str(result)]
                    )
        
        # Calculate statistics
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        total_processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        total_chunks = sum(r.chunks_created for r in results if r.success)
        
        batch_status = "completed"
        if failed == total_documents:
            batch_status = "failed"
        elif failed > 0:
            batch_status = "partial"
        
        return BatchProcessingResponse(
            total_documents=total_documents,
            successful=successful,
            failed=failed,
            results=results,
            total_processing_time_ms=total_processing_time,
            average_processing_time_ms=total_processing_time / total_documents,
            total_chunks_created=total_chunks,
            batch_status=batch_status,
            completed_at=datetime.utcnow()
        )
    
    async def get_document(self, document_id: str) -> Optional[DocumentResponse]:
        """
        Get document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Optional[DocumentResponse]: Document response or None
        """
        try:
            document = await self.knowledge_manager.get_document(document_id)
            if not document:
                return None
            
            # Get document chunks for statistics
            chunks = await self.knowledge_manager.get_document_chunks(document_id)
            
            return DocumentResponse(
                id=document.id,
                title=document.title,
                content=document.content[:1000] + "..." if len(document.content) > 1000 else document.content,
                file_type=document.file_type,
                file_size=document.file_size,
                file_path=document.file_path,
                status=ProcessingStatus(document.status.value),
                author=document.metadata.get('author'),
                category=document.metadata.get('category'),
                tags=document.metadata.get('tags', []),
                chunk_count=len(chunks),
                word_count=len(document.content.split()),
                character_count=len(document.content),
                created_at=document.created_at,
                updated_at=document.updated_at,
                metadata=document.metadata,
                has_embeddings=any(chunk.embedding for chunk in chunks)
            )
            
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            return None
    
    async def list_documents(self, request: DocumentListRequest) -> DocumentListResponse:
        """
        List documents with filtering and pagination.
        
        Args:
            request: Document list request
            
        Returns:
            DocumentListResponse: List of documents
        """
        try:
            start_time = datetime.utcnow()
            
            # Convert request to search filter
            from rag.models import SearchFilter
            filters = SearchFilter(
                statuses=[request.status] if request.status else None,
                created_after=request.date_from,
                created_before=request.date_to,
                tags=request.tags
            )
            
            # Get documents
            documents = await self.knowledge_manager.list_documents(
                filters=filters,
                limit=request.limit,
                offset=request.offset
            )
            
            # Convert to response DTOs
            document_responses = []
            for doc in documents:
                chunks = await self.knowledge_manager.get_document_chunks(doc.id)
                
                doc_response = DocumentResponse(
                    id=doc.id,
                    title=doc.title,
                    content=doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    file_type=doc.file_type,
                    file_size=doc.file_size,
                    status=ProcessingStatus(doc.status.value),
                    author=doc.metadata.get('author'),
                    category=doc.metadata.get('category'),
                    tags=doc.metadata.get('tags', []),
                    chunk_count=len(chunks),
                    word_count=len(doc.content.split()),
                    character_count=len(doc.content),
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    metadata=doc.metadata
                )
                document_responses.append(doc_response)
            
            # Calculate aggregations
            status_dist = {}
            category_dist = {}
            total_size = 0
            total_chunks = 0
            
            for doc_resp in document_responses:
                # Status distribution
                status = doc_resp.status.value
                status_dist[status] = status_dist.get(status, 0) + 1
                
                # Category distribution
                category = doc_resp.category or "uncategorized"
                category_dist[category] = category_dist.get(category, 0) + 1
                
                # Totals
                total_size += doc_resp.file_size
                total_chunks += doc_resp.chunk_count
            
            query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return DocumentListResponse(
                documents=document_responses,
                total_count=len(document_responses),  # TODO: Get actual total count from knowledge manager
                limit=request.limit,
                offset=request.offset,
                has_more=len(document_responses) == request.limit,
                status_distribution=status_dist,
                category_distribution=category_dist,
                total_size_bytes=total_size,
                total_chunks=total_chunks,
                query_time_ms=query_time
            )
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise
    
    async def update_document(self, request: UpdateDocumentRequest) -> ProcessingResponse:
        """
        Update an existing document.
        
        Args:
            request: Update document request
            
        Returns:
            ProcessingResponse: Update result
        """
        try:
            start_time = datetime.utcnow()
            
            # Get existing document
            document = await self.knowledge_manager.get_document(request.document_id)
            if not document:
                return ProcessingResponse(
                    success=False,
                    document_id=request.document_id,
                    status=ProcessingStatus.FAILED,
                    message="Document not found",
                    errors=["Document not found"]
                )
            
            # Update document fields
            if request.title:
                document.title = request.title
            if request.content:
                document.content = request.content
            if request.metadata:
                document.metadata.update(request.metadata)
            if request.tags:
                document.metadata['tags'] = request.tags
            if request.category:
                document.metadata['category'] = request.category
            
            document.updated_at = datetime.utcnow()
            
            # Update in knowledge base
            update_result = await self.knowledge_manager.update_document(document)
            
            if not update_result.success:
                return ProcessingResponse(
                    success=False,
                    document_id=request.document_id,
                    status=ProcessingStatus.FAILED,
                    message=f"Failed to update document: {update_result.message}",
                    errors=update_result.errors
                )
            
            # Reindex if requested
            if request.reindex:
                index_result = await self.index_manager.update_document(document)
                if not index_result.success:
                    return ProcessingResponse(
                        success=False,
                        document_id=request.document_id,
                        status=ProcessingStatus.FAILED,
                        message=f"Failed to reindex document: {index_result.message}",
                        errors=index_result.errors
                    )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ProcessingResponse(
                success=True,
                document_id=request.document_id,
                status=ProcessingStatus.COMPLETED,
                message="Document updated successfully",
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error updating document {request.document_id}: {e}")
            return ProcessingResponse(
                success=False,
                document_id=request.document_id,
                status=ProcessingStatus.FAILED,
                message=f"Error updating document: {str(e)}",
                errors=[str(e)]
            )
    
    async def delete_document(self, request: DeleteDocumentRequest) -> ProcessingResponse:
        """
        Delete a document.
        
        Args:
            request: Delete document request
            
        Returns:
            ProcessingResponse: Deletion result
        """
        try:
            start_time = datetime.utcnow()
            
            # Delete from knowledge base
            success = await self.knowledge_manager.delete_document(request.document_id)
            
            if not success:
                return ProcessingResponse(
                    success=False,
                    document_id=request.document_id,
                    status=ProcessingStatus.FAILED,
                    message="Failed to delete document from knowledge base"
                )
            
            # Delete from index
            index_success = await self.index_manager.delete_document(request.document_id)
            
            if not index_success:
                logger.warning(f"Failed to delete document {request.document_id} from index")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ProcessingResponse(
                success=True,
                document_id=request.document_id,
                status=ProcessingStatus.COMPLETED,
                message="Document deleted successfully",
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error deleting document {request.document_id}: {e}")
            return ProcessingResponse(
                success=False,
                document_id=request.document_id,
                status=ProcessingStatus.FAILED,
                message=f"Error deleting document: {str(e)}",
                errors=[str(e)]
            )


class SearchService:
    """
    Application service for search operations.
    
    This service provides high-level search capabilities and coordinates
    different search strategies (SRP).
    """
    
    def __init__(self,
                 search_service: ISearchService,
                 knowledge_manager: IKnowledgeManager):
        """
        Initialize search service.
        
        Args:
            search_service: Search service interface
            knowledge_manager: Knowledge management interface
        """
        self.search_service = search_service
        self.knowledge_manager = knowledge_manager
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Perform knowledge search.
        
        Args:
            request: Search request
            
        Returns:
            SearchResponse: Search results
        """
        try:
            start_time = datetime.utcnow()
            
            # Convert request to search filter
            from rag.models import SearchFilter
            filters = SearchFilter(
                document_ids=request.document_ids,
                created_after=request.date_from,
                created_before=request.date_to,
                tags=request.tags
            )
            
            # Perform search based on strategy
            if request.strategy == SearchStrategy.SEMANTIC:
                query_result = await self.search_service.semantic_search(
                    request.query,
                    request.top_k,
                    filters
                )
            elif request.strategy == SearchStrategy.KEYWORD:
                query_result = await self.search_service.keyword_search(
                    request.query,
                    request.top_k,
                    filters
                )
            elif request.strategy == SearchStrategy.HYBRID:
                query_result = await self.search_service.hybrid_search(
                    request.query,
                    request.semantic_weight,
                    request.keyword_weight,
                    request.top_k,
                    filters
                )
            else:
                query_result = await self.search_service.search(
                    request.query,
                    request.strategy,
                    request.top_k,
                    filters
                )
            
            search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Convert to response format
            from application.dtos.rag import SearchResultItem, DocumentChunkResponse
            
            search_results = []
            scores = []
            
            for i, chunk in enumerate(query_result.chunks):
                # Get document info
                document = await self.knowledge_manager.get_document(chunk.document_id)
                
                if document:
                    doc_response = DocumentResponse(
                        id=document.id,
                        title=document.title,
                        file_type=document.file_type,
                        file_size=document.file_size,
                        status=ProcessingStatus(document.status.value),
                        author=document.metadata.get('author'),
                        category=document.metadata.get('category'),
                        tags=document.metadata.get('tags', []),
                        created_at=document.created_at,
                        updated_at=document.updated_at,
                        metadata=document.metadata
                    )
                    
                    chunk_response = DocumentChunkResponse(
                        id=chunk.id,
                        document_id=chunk.document_id,
                        content=chunk.content,
                        chunk_index=chunk.chunk_index,
                        start_position=chunk.start_position,
                        end_position=chunk.end_position,
                        metadata=chunk.metadata,
                        created_at=chunk.created_at
                    )
                    
                    # Get relevance score
                    relevance_score = (query_result.relevance_scores[i] 
                                     if i < len(query_result.relevance_scores) else 0.0)
                    scores.append(relevance_score)
                    
                    search_result = SearchResultItem(
                        chunk=chunk_response,
                        document=doc_response,
                        relevance_score=relevance_score,
                        rank=i + 1,
                        match_type=request.strategy.value
                    )
                    
                    search_results.append(search_result)
            
            # Calculate statistics
            max_score = max(scores) if scores else 0.0
            min_score = min(scores) if scores else 0.0
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            return SearchResponse(
                query=request.query,
                strategy=request.strategy,
                results=search_results,
                total_found=query_result.total_found,
                retrieved_count=len(search_results),
                search_time_ms=search_time,
                max_score=max_score,
                min_score=min_score,
                avg_score=avg_score,
                processed_query=query_result.metadata.get('processed_query'),
                expanded_terms=query_result.metadata.get('expanded_terms', []),
                query_intent=query_result.metadata.get('query_intent'),
                metadata=query_result.metadata
            )
            
        except SearchError as e:
            logger.error(f"Search error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise


# Main orchestrator service following the Facade pattern
class RAGService:
    """
    Main RAG orchestrator service.
    
    This service provides a unified interface for all RAG operations,
    coordinating document and search services (Facade pattern).
    """
    
    def __init__(self,
                 document_service: DocumentService,
                 search_service: SearchService,
                 embedding_service: IEmbeddingService,
                 vector_store: IVectorStore,
                 index_manager: IIndexManager):
        """
        Initialize RAG service.
        
        Args:
            document_service: Document service
            search_service: Search service
            embedding_service: Embedding service
            vector_store: Vector store
            index_manager: Index manager
        """
        self.document_service = document_service
        self.search_service = search_service
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.index_manager = index_manager
    
    # Document operations delegation
    async def ingest_document(self, request: DocumentIngestionRequest) -> ProcessingResponse:
        """Delegate to document service."""
        return await self.document_service.ingest_document(request)
    
    async def ingest_documents_batch(self, request: BatchIngestionRequest) -> BatchProcessingResponse:
        """Delegate to document service."""
        return await self.document_service.ingest_documents_batch(request)
    
    async def get_document(self, document_id: str) -> Optional[DocumentResponse]:
        """Delegate to document service."""
        return await self.document_service.get_document(document_id)
    
    async def list_documents(self, request: DocumentListRequest) -> DocumentListResponse:
        """Delegate to document service."""
        return await self.document_service.list_documents(request)
    
    async def update_document(self, request: UpdateDocumentRequest) -> ProcessingResponse:
        """Delegate to document service."""
        return await self.document_service.update_document(request)
    
    async def delete_document(self, request: DeleteDocumentRequest) -> ProcessingResponse:
        """Delegate to document service."""
        return await self.document_service.delete_document(request)
    
    # Search operations delegation
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Delegate to search service."""
        return await self.search_service.search(request)
    
    # Additional RAG-specific operations
    async def create_index(self, request: CreateIndexRequest) -> IndexResponse:
        """Create a new index."""
        try:
            success = await self.index_manager.create_index(
                request.name,
                {
                    'embedding_model': request.embedding_model,
                    'dimension': request.dimension,
                    'distance_metric': request.distance_metric,
                    **request.configuration
                }
            )
            
            if success:
                stats = await self.index_manager.get_index_stats(request.name)
                
                return IndexResponse(
                    name=request.name,
                    status="active",
                    description=request.description,
                    embedding_model=request.embedding_model,
                    dimension=request.dimension,
                    distance_metric=request.distance_metric,
                    configuration=request.configuration,
                    **stats
                )
            else:
                return IndexResponse(
                    name=request.name,
                    status="error",
                    description=request.description,
                    health_status="error"
                )
                
        except Exception as e:
            logger.error(f"Error creating index {request.name}: {e}")
            raise
    
    async def get_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings for texts."""
        try:
            start_time = datetime.utcnow()
            
            embeddings = await self.embedding_service.embed_texts_batch(request.texts)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=request.model,
                dimension=self.embedding_service.get_embedding_dimension(),
                processing_time_ms=processing_time,
                input_count=len(request.texts),
                successful=len(embeddings),
                failed=len(request.texts) - len(embeddings)
            )
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return EmbeddingResponse(
                model=request.model,
                input_count=len(request.texts),
                failed=len(request.texts),
                errors=[str(e)]
            )
    
    async def similarity_search(self, request: SimilaritySearchRequest) -> SimilaritySearchResponse:
        """Perform similarity search using embeddings."""
        try:
            start_time = datetime.utcnow()
            
            results = await self.vector_store.search_similar(
                request.embedding,
                request.top_k,
                {
                    'similarity_threshold': request.similarity_threshold,
                    'document_ids': request.document_ids,
                    **(request.metadata_filters or {})
                }
            )
            
            search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Convert results to response format
            from application.dtos.rag import SearchResultItem, DocumentChunkResponse
            
            search_results = []
            for i, result in enumerate(results):
                # This would need to be implemented based on your result structure
                # For now, creating a placeholder
                search_results.append(
                    SearchResultItem(
                        chunk=DocumentChunkResponse(
                            id=result.chunk_id,
                            document_id=result.document_id,
                            content=result.content,
                            chunk_index=0,
                            start_position=0,
                            end_position=len(result.content),
                            similarity_score=result.score
                        ),
                        document=DocumentResponse(
                            id=result.document_id,
                            title="",
                            file_type="",
                            file_size=0,
                            status=ProcessingStatus.COMPLETED
                        ),
                        relevance_score=result.score,
                        rank=i + 1,
                        match_type="similarity"
                    )
                )
            
            return SimilaritySearchResponse(
                results=search_results,
                total_candidates=len(results),
                retrieved_count=len(search_results),
                search_time_ms=search_time,
                similarity_threshold=request.similarity_threshold,
                index_name=request.index_name
            )
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            raise
    
    async def get_system_health(self, request: SystemHealthRequest) -> SystemHealthResponse:
        """Get system health status."""
        try:
            start_time = datetime.utcnow()
            
            components = {}
            overall_status = "healthy"
            
            # Check each component if requested
            if "all" in request.check_components or "vector_store" in request.check_components:
                try:
                    store_info = await self.vector_store.get_store_info()
                    components["vector_store"] = {
                        "status": "healthy",
                        "info": store_info
                    }
                except Exception as e:
                    components["vector_store"] = {
                        "status": "unhealthy", 
                        "error": str(e)
                    }
                    overall_status = "degraded"
            
            if "all" in request.check_components or "index" in request.check_components:
                try:
                    index_stats = await self.index_manager.get_index_stats()
                    components["index"] = {
                        "status": "healthy",
                        "stats": index_stats
                    }
                except Exception as e:
                    components["index"] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
                    overall_status = "degraded"
            
            if "all" in request.check_components or "embedding" in request.check_components:
                try:
                    model_info = self.embedding_service.get_model_info()
                    components["embedding"] = {
                        "status": "healthy",
                        "model_info": model_info
                    }
                except Exception as e:
                    components["embedding"] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
                    overall_status = "degraded"
            
            check_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SystemHealthResponse(
                overall_status=overall_status,
                components=components,
                check_duration_ms=check_duration
            )
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return SystemHealthResponse(
                overall_status="unhealthy",
                check_duration_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                alerts=[f"Health check failed: {str(e)}"]
            )

