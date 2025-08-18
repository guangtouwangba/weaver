"""
FastAPI routes for RAG (Retrieval-Augmented Generation) operations.

This module provides REST API endpoints for document ingestion, search,
indexing, and other RAG-related operations with comprehensive validation.
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# Application layer imports
from services.rag_services import RAGService, DocumentService, SearchService
from application.dtos.rag import (
    # Request DTOs
    DocumentIngestionRequest, BatchIngestionRequest, SearchRequest,
    CreateIndexRequest, UpdateDocumentRequest, DeleteDocumentRequest,
    DocumentListRequest, EmbeddingRequest, SimilaritySearchRequest,
    SystemHealthRequest, DocumentFormat, ChunkStrategy,
    
    # Response DTOs
    ProcessingResponse, BatchProcessingResponse, DocumentResponse,
    SearchResponse, IndexResponse, DocumentListResponse, EmbeddingResponse,
    SimilaritySearchResponse, SystemHealthResponse
)
from domain.rag_interfaces import SearchStrategy, ProcessingStatus

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


# Pydantic API models for request validation

class DocumentIngestionAPI(BaseModel):
    """API model for document ingestion request."""
    model_config = ConfigDict(from_attributes=True)
    
    source: str = Field(..., min_length=1, description="File path, URL, or content")
    source_type: str = Field("file", pattern="^(file|url|content)$", description="Source type")
    document_format: Optional[DocumentFormat] = Field(None, description="Document format")
    title: Optional[str] = Field(None, max_length=500, description="Document title")
    author: Optional[str] = Field(None, max_length=200, description="Document author")
    category: Optional[str] = Field(None, max_length=100, description="Document category")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    
    # Processing configuration
    chunk_strategy: ChunkStrategy = Field(ChunkStrategy.FIXED_SIZE, description="Chunking strategy")
    chunk_size: int = Field(1000, gt=0, le=10000, description="Chunk size in characters")
    chunk_overlap: int = Field(200, ge=0, description="Chunk overlap in characters")
    enable_ocr: bool = Field(False, description="Enable OCR for image documents")
    extract_images: bool = Field(False, description="Extract images from documents")
    
    # Indexing configuration
    index_name: Optional[str] = Field(None, max_length=100, description="Target index name")
    enable_auto_tagging: bool = Field(True, description="Enable automatic tagging")
    enable_summary: bool = Field(True, description="Enable document summarization")


class BatchIngestionAPI(BaseModel):
    """API model for batch document ingestion."""
    model_config = ConfigDict(from_attributes=True)
    
    sources: List[str] = Field(..., min_items=1, max_items=100, description="List of sources")
    common_config: Optional[DocumentIngestionAPI] = Field(None, description="Common configuration")
    max_parallel: int = Field(5, ge=1, le=20, description="Maximum parallel processing")
    fail_fast: bool = Field(False, description="Stop on first failure")


class SearchAPI(BaseModel):
    """API model for knowledge search."""
    model_config = ConfigDict(from_attributes=True)
    
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    strategy: SearchStrategy = Field(SearchStrategy.SEMANTIC, description="Search strategy")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold")
    
    # Filters
    document_ids: Optional[List[str]] = Field(None, description="Filter by document IDs")
    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    date_from: Optional[datetime] = Field(None, description="Filter by date from")
    date_to: Optional[datetime] = Field(None, description="Filter by date to")
    authors: Optional[List[str]] = Field(None, description="Filter by authors")
    file_types: Optional[List[str]] = Field(None, description="Filter by file types")
    
    # Hybrid search configuration
    semantic_weight: float = Field(0.7, ge=0.0, le=1.0, description="Semantic search weight")
    keyword_weight: float = Field(0.3, ge=0.0, le=1.0, description="Keyword search weight")
    
    # Advanced options
    enable_reranking: bool = Field(True, description="Enable result reranking")
    enable_highlighting: bool = Field(True, description="Enable result highlighting")
    include_metadata: bool = Field(True, description="Include document metadata")
    expand_query: bool = Field(False, description="Enable query expansion")


class CreateIndexAPI(BaseModel):
    """API model for creating a new index."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=100, pattern="^[a-zA-Z0-9_-]+$")
    description: Optional[str] = Field(None, max_length=500, description="Index description")
    embedding_model: str = Field("text-embedding-ada-002", description="Embedding model name")
    dimension: int = Field(1536, gt=0, le=10000, description="Embedding dimension")
    distance_metric: str = Field("cosine", pattern="^(cosine|euclidean|dot_product)$")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Additional config")


class UpdateDocumentAPI(BaseModel):
    """API model for updating a document."""
    model_config = ConfigDict(from_attributes=True)
    
    title: Optional[str] = Field(None, max_length=500, description="New document title")
    content: Optional[str] = Field(None, description="New document content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")
    tags: Optional[List[str]] = Field(None, description="Updated tags")
    category: Optional[str] = Field(None, max_length=100, description="Updated category")
    
    # Processing options
    reprocess: bool = Field(False, description="Reprocess document content")
    reindex: bool = Field(False, description="Reindex document")
    preserve_chunks: bool = Field(True, description="Preserve existing chunks")


class DeleteDocumentAPI(BaseModel):
    """API model for deleting a document."""
    model_config = ConfigDict(from_attributes=True)
    
    hard_delete: bool = Field(False, description="Permanently delete (vs soft delete)")
    delete_from_vector_store: bool = Field(True, description="Remove from vector store")
    delete_chunks: bool = Field(True, description="Delete document chunks")


class EmbeddingAPI(BaseModel):
    """API model for generating embeddings."""
    model_config = ConfigDict(from_attributes=True)
    
    texts: List[str] = Field(..., min_items=1, max_items=100, description="Texts to embed")
    model: str = Field("text-embedding-ada-002", description="Embedding model")
    normalize: bool = Field(True, description="Normalize embeddings")


class SimilaritySearchAPI(BaseModel):
    """API model for similarity search."""
    model_config = ConfigDict(from_attributes=True)
    
    embedding: List[float] = Field(..., min_items=1, description="Query embedding vector")
    top_k: int = Field(10, ge=1, le=100, description="Number of results")
    similarity_threshold: float = Field(0.0, ge=0.0, le=1.0, description="Similarity threshold")
    index_name: Optional[str] = Field(None, description="Target index name")
    document_ids: Optional[List[str]] = Field(None, description="Filter by document IDs")
    metadata_filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")


# Mock dependency functions (to be replaced with actual services)

async def get_current_user_id() -> str:
    """Get current authenticated user ID."""
    return "user_123"  # Mock user ID


async def get_rag_service() -> RAGService:
    """Get RAG service instance with proper dependencies."""
    # TODO: Replace with proper dependency injection
    # For now, returning None to indicate this needs implementation
    raise HTTPException(
        status_code=501, 
        detail="RAG service dependencies not yet implemented. Please implement dependency injection."
    )


async def get_document_service() -> DocumentService:
    """Get document service instance."""
    # TODO: Replace with proper dependency injection
    raise HTTPException(
        status_code=501,
        detail="Document service dependencies not yet implemented."
    )


async def get_search_service() -> SearchService:
    """Get search service instance."""
    # TODO: Replace with proper dependency injection
    raise HTTPException(
        status_code=501,
        detail="Search service dependencies not yet implemented."
    )


# Document Management Routes

@router.post("/documents/ingest", response_model=ProcessingResponse, status_code=201)
async def ingest_document(
    request: DocumentIngestionAPI,
    user_id: str = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Ingest a single document into the RAG system.
    
    This endpoint handles document loading, processing, chunking, and indexing.
    """
    try:
        # Convert API model to DTO
        ingestion_request = DocumentIngestionRequest(
            source=request.source,
            source_type=request.source_type,
            document_format=request.document_format,
            title=request.title,
            author=request.author,
            category=request.category,
            tags=request.tags,
            metadata=request.metadata,
            chunk_strategy=request.chunk_strategy,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            enable_ocr=request.enable_ocr,
            extract_images=request.extract_images,
            index_name=request.index_name,
            enable_auto_tagging=request.enable_auto_tagging,
            enable_summary=request.enable_summary
        )
        
        response = await rag_service.ingest_document(ingestion_request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in ingest_document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/documents/batch-ingest", response_model=BatchProcessingResponse, status_code=201)
async def batch_ingest_documents(
    request: BatchIngestionAPI,
    user_id: str = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Ingest multiple documents in batch with parallel processing."""
    try:
        # Convert common config if provided
        common_config = None
        if request.common_config:
            common_config = DocumentIngestionRequest(
                source="",  # Will be set per source
                source_type=request.common_config.source_type,
                document_format=request.common_config.document_format,
                title=request.common_config.title,
                author=request.common_config.author,
                category=request.common_config.category,
                tags=request.common_config.tags,
                metadata=request.common_config.metadata,
                chunk_strategy=request.common_config.chunk_strategy,
                chunk_size=request.common_config.chunk_size,
                chunk_overlap=request.common_config.chunk_overlap,
                enable_ocr=request.common_config.enable_ocr,
                extract_images=request.common_config.extract_images,
                index_name=request.common_config.index_name,
                enable_auto_tagging=request.common_config.enable_auto_tagging,
                enable_summary=request.common_config.enable_summary
            )
        
        batch_request = BatchIngestionRequest(
            sources=request.sources,
            common_config=common_config,
            max_parallel=request.max_parallel,
            fail_fast=request.fail_fast
        )
        
        response = await rag_service.ingest_documents_batch(batch_request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in batch_ingest_documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str = Path(..., description="Document ID"),
    user_id: str = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Get detailed information about a specific document."""
    try:
        response = await rag_service.get_document(document_id)
        if not response:
            raise HTTPException(status_code=404, detail="Document not found")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(50, ge=1, le=1000, description="Number of documents to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|title|file_size)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    status: Optional[ProcessingStatus] = Query(None, description="Filter by status"),
    categories: Optional[List[str]] = Query(None, description="Filter by categories"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    authors: Optional[List[str]] = Query(None, description="Filter by authors"),
    date_from: Optional[datetime] = Query(None, description="Filter by date from"),
    date_to: Optional[datetime] = Query(None, description="Filter by date to"),
    search_text: Optional[str] = Query(None, description="Search in document text"),
    user_id: str = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """List documents with filtering, sorting, and pagination."""
    try:
        list_request = DocumentListRequest(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            status=status,
            categories=categories,
            tags=tags,
            authors=authors,
            date_from=date_from,
            date_to=date_to,
            search_text=search_text
        )
        
        response = await rag_service.list_documents(list_request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in list_documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/documents/{document_id}", response_model=ProcessingResponse)
async def update_document(
    document_id: str = Path(..., description="Document ID"),
    request: UpdateDocumentAPI = UpdateDocumentAPI(),
    user_id: str = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Update an existing document's metadata or content."""
    try:
        update_request = UpdateDocumentRequest(
            document_id=document_id,
            title=request.title,
            content=request.content,
            metadata=request.metadata,
            tags=request.tags,
            category=request.category,
            reprocess=request.reprocess,
            reindex=request.reindex,
            preserve_chunks=request.preserve_chunks
        )
        
        response = await rag_service.update_document(update_request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in update_document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/documents/{document_id}", response_model=ProcessingResponse)
async def delete_document(
    document_id: str = Path(..., description="Document ID"),
    request: DeleteDocumentAPI = DeleteDocumentAPI(),
    user_id: str = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Delete a document from the RAG system."""
    try:
        delete_request = DeleteDocumentRequest(
            document_id=document_id,
            hard_delete=request.hard_delete,
            delete_from_vector_store=request.delete_from_vector_store,
            delete_chunks=request.delete_chunks
        )
        
        response = await rag_service.delete_document(delete_request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in delete_document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Search Routes

@router.post("/search", response_model=SearchResponse)
async def search_knowledge(
    request: SearchAPI,
    user_id: str = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Perform knowledge search using various strategies (semantic, keyword, hybrid)."""
    try:
        # Validate semantic + keyword weights
        if abs((request.semantic_weight + request.keyword_weight) - 1.0) > 0.01:
            raise ValueError("Semantic weight + keyword weight must equal 1.0")
        
        search_request = SearchRequest(
            query=request.query,
            strategy=request.strategy,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            document_ids=request.document_ids,
            categories=request.categories,
            tags=request.tags,
            date_from=request.date_from,
            date_to=request.date_to,
            authors=request.authors,
            file_types=request.file_types,
            semantic_weight=request.semantic_weight,
            keyword_weight=request.keyword_weight,
            enable_reranking=request.enable_reranking,
            enable_highlighting=request.enable_highlighting,
            include_metadata=request.include_metadata,
            expand_query=request.expand_query
        )
        
        response = await rag_service.search(search_request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in search_knowledge: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/search/similarity", response_model=SimilaritySearchResponse)
async def similarity_search(
    request: SimilaritySearchAPI,
    user_id: str = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Perform similarity search using pre-computed embeddings."""
    try:
        similarity_request = SimilaritySearchRequest(
            embedding=request.embedding,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            index_name=request.index_name,
            document_ids=request.document_ids,
            metadata_filters=request.metadata_filters
        )
        
        response = await rag_service.similarity_search(similarity_request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in similarity_search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Index Management Routes

@router.post("/indexes", response_model=IndexResponse, status_code=201)
async def create_index(
    request: CreateIndexAPI,
    user_id: str = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Create a new vector index for document storage and search."""
    try:
        index_request = CreateIndexRequest(
            name=request.name,
            description=request.description,
            embedding_model=request.embedding_model,
            dimension=request.dimension,
            distance_metric=request.distance_metric,
            configuration=request.configuration
        )
        
        response = await rag_service.create_index(index_request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in create_index: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Embedding Routes

@router.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(
    request: EmbeddingAPI,
    user_id: str = Depends(get_current_user_id),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Generate embeddings for text inputs."""
    try:
        embedding_request = EmbeddingRequest(
            texts=request.texts,
            model=request.model,
            normalize=request.normalize
        )
        
        response = await rag_service.get_embeddings(embedding_request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in generate_embeddings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# System Routes

@router.get("/health", response_model=SystemHealthResponse)
async def health_check(
    components: List[str] = Query(["all"], description="Components to check"),
    include_metrics: bool = Query(True, description="Include performance metrics"),
    include_performance: bool = Query(False, description="Include detailed performance"),
    detailed: bool = Query(False, description="Include detailed information"),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Check the health status of the RAG system components."""
    try:
        health_request = SystemHealthRequest(
            check_components=components,
            include_metrics=include_metrics,
            include_performance=include_performance,
            detailed=detailed
        )
        
        response = await rag_service.get_system_health(health_request)
        
        # Determine HTTP status code based on health
        if response.overall_status == "healthy":
            status_code = 200
        elif response.overall_status == "degraded":
            status_code = 200  # Still operational
        else:  # unhealthy
            status_code = 503
            
        return JSONResponse(status_code=status_code, content=response.dict())
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "overall_status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


# Additional utility endpoints

@router.get("/")
async def rag_info():
    """Get RAG system information and available endpoints."""
    return {
        "service": "RAG API",
        "version": "1.0.0",
        "description": "Retrieval-Augmented Generation system for document management and search",
        "endpoints": {
            "documents": {
                "ingest": "POST /documents/ingest",
                "batch_ingest": "POST /documents/batch-ingest",
                "get": "GET /documents/{document_id}",
                "list": "GET /documents",
                "update": "PUT /documents/{document_id}",
                "delete": "DELETE /documents/{document_id}"
            },
            "search": {
                "knowledge_search": "POST /search",
                "similarity_search": "POST /search/similarity"
            },
            "indexes": {
                "create": "POST /indexes"
            },
            "embeddings": {
                "generate": "POST /embeddings"
            },
            "system": {
                "health": "GET /health",
                "info": "GET /"
            }
        },
        "supported_formats": ["text", "pdf", "docx", "html", "markdown", "json", "csv"],
        "supported_search_strategies": ["semantic", "keyword", "hybrid"],
        "timestamp": datetime.utcnow().isoformat()
    }