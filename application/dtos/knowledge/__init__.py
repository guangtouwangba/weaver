"""
Knowledge Management DTOs

知识管理相关的数据传输对象，用于API层与应用层之间的数据传递。
严格遵循DTO模式，不包含业务逻辑。
"""

from .requests import (
    DocumentIngestionRequest,
    DocumentProcessingRequest,
    SearchRequest,
    DocumentListRequest,
    BatchIngestionRequest
)

from .responses import (
    DocumentIngestionResponse,
    DocumentProcessingResponse,
    SearchResponse,
    DocumentListResponse,
    BatchIngestionResponse,
    DocumentSummaryResponse
)

__all__ = [
    # Request DTOs
    "DocumentIngestionRequest",
    "DocumentProcessingRequest", 
    "SearchRequest",
    "DocumentListRequest",
    "BatchIngestionRequest",
    
    # Response DTOs
    "DocumentIngestionResponse",
    "DocumentProcessingResponse",
    "SearchResponse", 
    "DocumentListResponse",
    "BatchIngestionResponse",
    "DocumentSummaryResponse",
]