"""
Document API schemas.

Pydantic models for document-related API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from ...core.entities.document import Document
from ...use_cases.document.search_documents import DocumentSearchResult


class CreateDocumentRequestSchema(BaseModel):
    """Schema for create document request."""
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    content: str = Field(..., min_length=1, description="Document content")
    content_type: str = Field(default="text", description="Content type")
    file_id: Optional[str] = Field(None, description="Associated file ID")
    file_path: Optional[str] = Field(None, description="File path")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: str
    title: str
    content: Optional[str] = None
    content_type: str
    file_id: Optional[str] = None
    file_path: Optional[str] = None
    file_size: int
    status: str
    processing_status: Optional[str] = None
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_entity(cls, document: Document) -> "DocumentResponse":
        """Create response from document entity."""
        return cls(
            id=document.id,
            title=document.title,
            content=document.content,
            content_type=document.content_type,
            file_id=document.file_id,
            file_path=document.file_path,
            file_size=document.file_size,
            status=document.status,
            processing_status=document.processing_status,
            metadata=document.metadata or {},
            created_at=document.created_at,
            updated_at=document.updated_at
        )


class SearchDocumentsRequestSchema(BaseModel):
    """Schema for search documents request."""
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    use_semantic_search: bool = Field(default=True, description="Use semantic search")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Similarity threshold")


class SearchResultResponse(BaseModel):
    """Schema for individual search result."""
    document: DocumentResponse
    score: float
    relevant_chunks: List[str]
    metadata: Dict[str, Any]
    
    @classmethod
    def from_search_result(cls, result: DocumentSearchResult) -> "SearchResultResponse":
        """Create response from search result."""
        return cls(
            document=DocumentResponse.from_entity(result.document),
            score=result.score,
            relevant_chunks=result.relevant_chunks,
            metadata=result.metadata
        )


class SearchResultsResponse(BaseModel):
    """Schema for search results response."""
    results: List[SearchResultResponse]
    total: int
    query: str
    
    @classmethod
    def from_search_results(cls, results: List[DocumentSearchResult], query: str) -> "SearchResultsResponse":
        """Create response from search results."""
        return cls(
            results=[SearchResultResponse.from_search_result(r) for r in results],
            total=len(results),
            query=query
        )