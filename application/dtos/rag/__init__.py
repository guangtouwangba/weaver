"""
RAG DTOs Package

This module contains all Data Transfer Objects related to RAG operations.
"""

from .requests import (
    DocumentIngestionRequest,
    BatchIngestionRequest,
    SearchRequest,
    CreateIndexRequest,
    UpdateDocumentRequest,
    DeleteDocumentRequest,
    DocumentListRequest,
    EmbeddingRequest,
    SimilaritySearchRequest,
    AnalyticsRequest,
    SystemHealthRequest,
    ExportRequest,
    ImportRequest,
    
    # Enums
    DocumentFormat,
    ChunkStrategy
)

from .responses import (
    ProcessingResponse,
    BatchProcessingResponse,
    DocumentChunkResponse,
    DocumentResponse,
    SearchResultItem,
    SearchResponse,
    IndexResponse,
    DocumentListResponse,
    EmbeddingResponse,
    SimilaritySearchResponse,
    SystemHealthResponse,
    AnalyticsResponse,
    ExportResponse,
    ImportResponse,
    ErrorResponse,
    TaskStatusResponse
)

__all__ = [
    # Request DTOs
    "DocumentIngestionRequest",
    "BatchIngestionRequest", 
    "SearchRequest",
    "CreateIndexRequest",
    "UpdateDocumentRequest",
    "DeleteDocumentRequest",
    "DocumentListRequest",
    "EmbeddingRequest",
    "SimilaritySearchRequest",
    "AnalyticsRequest",
    "SystemHealthRequest",
    "ExportRequest",
    "ImportRequest",
    
    # Response DTOs
    "ProcessingResponse",
    "BatchProcessingResponse",
    "DocumentChunkResponse",
    "DocumentResponse",
    "SearchResultItem",
    "SearchResponse",
    "IndexResponse",
    "DocumentListResponse",
    "EmbeddingResponse",
    "SimilaritySearchResponse",
    "SystemHealthResponse",
    "AnalyticsResponse",
    "ExportResponse",
    "ImportResponse",
    "ErrorResponse",
    "TaskStatusResponse",
    
    # Enums
    "DocumentFormat",
    "ChunkStrategy"
]