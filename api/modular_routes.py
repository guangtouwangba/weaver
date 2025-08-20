"""
Modular API

Simple API routes that use the modular architecture instead of complex DDD layers.
This demonstrates how to use the modular system directly from API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from datetime import datetime

from modules.router import DocumentRouter
from modules.models import SearchQuery, ContentType, ModuleConfig

# Create router instance
router = APIRouter(prefix="/api/v1/modular", tags=["modular-rag"])

# Global document router instance (in production, use proper DI)
_document_router = None


async def get_document_router() -> DocumentRouter:
    """Get document router instance."""
    global _document_router
    if _document_router is None:
        _document_router = DocumentRouter()
        await _document_router.initialize()
    return _document_router


# Pydantic models for API
class DocumentIngestionRequest(BaseModel):
    """Request model for document ingestion."""
    file_paths: List[str] = Field(..., description="List of file paths to ingest")


class DocumentIngestionResponse(BaseModel):
    """Response model for document ingestion."""
    success: bool
    total_files: int
    processed_successfully: int
    failed_files: int
    results: List[dict]


class SearchRequest(BaseModel):
    """Request model for document search."""
    query: str = Field(..., min_length=1, description="Search query")
    max_results: int = Field(10, ge=1, le=100, description="Maximum number of results")
    document_ids: Optional[List[str]] = Field(None, description="Limit search to specific documents")
    content_types: Optional[List[str]] = Field(None, description="Filter by content types")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")


class SearchResponse(BaseModel):
    """Response model for search results."""
    query: str
    total_results: int
    processing_time_ms: float
    results: List[dict]
    metadata: dict


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    status: str
    total_documents: int
    total_chunks: int
    supported_formats: List[str]
    components: dict


# API Endpoints

@router.post("/ingest", response_model=DocumentIngestionResponse)
async def ingest_documents(request: DocumentIngestionRequest):
    """
    Ingest documents into the system.
    
    This endpoint demonstrates the simplicity of the modular approach:
    - No complex DDD layers
    - Direct module usage
    - Clear data flow
    """
    try:
        document_router = await get_document_router()
        
        results = []
        processed_successfully = 0
        failed_files = 0
        
        # Process each file
        async for result in document_router.ingest_documents_batch(request.file_paths):
            result_dict = {
                'success': result.success,
                'document_id': result.document_id,
                'chunks_created': result.chunks_created,
                'processing_time_ms': result.processing_time_ms,
                'error_message': result.error_message,
                'metadata': result.metadata
            }
            results.append(result_dict)
            
            if result.success:
                processed_successfully += 1
            else:
                failed_files += 1
        
        return DocumentIngestionResponse(
            success=failed_files == 0,
            total_files=len(request.file_paths),
            processed_successfully=processed_successfully,
            failed_files=failed_files,
            results=results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {e}")


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Search documents using the modular retrieval system.
    
    This endpoint shows how simple the search becomes:
    - Direct router call
    - No complex service orchestration
    - Clear request/response flow
    """
    try:
        document_router = await get_document_router()
        
        # Convert content type strings to enums
        content_types = None
        if request.content_types:
            content_types = []
            for ct_str in request.content_types:
                try:
                    content_types.append(ContentType(ct_str))
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid content type: {ct_str}")
        
        # Create search query
        query = SearchQuery(
            query=request.query,
            max_results=request.max_results,
            document_ids=request.document_ids,
            content_types=content_types,
            tags=request.tags
        )
        
        # Execute search
        response = await document_router.search_documents(query)
        
        # Convert results to dict format
        results_dict = []
        for result in response.results:
            results_dict.append({
                'chunk_id': result.chunk.id,
                'document_id': result.chunk.document_id,
                'content': result.chunk.content,
                'score': result.score,
                'rank': result.rank,
                'chunk_index': result.chunk.chunk_index,
                'metadata': result.metadata
            })
        
        return SearchResponse(
            query=response.query,
            total_results=response.total_results,
            processing_time_ms=response.processing_time_ms,
            results=results_dict,
            metadata=response.metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """
    Get a specific document by ID.
    
    Simple direct retrieval through the router.
    """
    try:
        document_router = await get_document_router()
        document = await document_router.get_document_by_id(document_id)
        
        return {
            'id': document.id,
            'title': document.title,
            'content': document.content,
            'content_type': document.content_type.value,
            'file_path': document.file_path,
            'file_size': document.file_size,
            'status': document.status.value,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat(),
            'metadata': document.metadata,
            'tags': document.tags
        }
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Document not found: {e}")


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and all its associated data.
    
    Simple deletion through the router.
    """
    try:
        document_router = await get_document_router()
        success = await document_router.delete_document(document_id)
        
        return {
            'success': success,
            'document_id': document_id,
            'message': 'Document deleted successfully' if success else 'Failed to delete document'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {e}")


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Get system status showing the simplicity of the modular architecture.
    
    This endpoint shows how easy it is to get comprehensive system status
    without complex layer navigation.
    """
    try:
        document_router = await get_document_router()
        status = document_router.get_status()
        
        return SystemStatusResponse(
            status="healthy" if status.get('initialized', False) else "not_initialized",
            total_documents=status.get('total_documents', 0),
            total_chunks=status.get('total_chunks', 0),
            supported_formats=status.get('supported_formats', []),
            components={
                'file_loader': status.get('file_loader_status', {}),
                'document_processor': status.get('document_processor_status', {}),
                'router': {
                    'initialized': status.get('initialized', False),
                    'enabled': status.get('enabled', False)
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {e}")


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    try:
        document_router = await get_document_router()
        status = document_router.get_status()
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'initialized': status.get('initialized', False),
            'components_active': len([k for k, v in status.items() if isinstance(v, dict) and v.get('initialized')])
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }


# Lifecycle management endpoints

@router.post("/initialize")
async def initialize_system():
    """
    Initialize the modular system.
    """
    try:
        document_router = await get_document_router()
        # Router is already initialized by get_document_router()
        
        return {
            'success': True,
            'message': 'System initialized successfully',
            'status': document_router.get_status()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize system: {e}")


@router.post("/shutdown")
async def shutdown_system():
    """
    Shutdown the modular system.
    """
    try:
        global _document_router
        if _document_router:
            await _document_router.cleanup()
            _document_router = None
        
        return {
            'success': True,
            'message': 'System shutdown successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to shutdown system: {e}")