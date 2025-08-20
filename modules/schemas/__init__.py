"""
Schema模块

使用Pydantic定义全局统一的数据模式，提供类型安全和序列化支持。
减少数据分层，统一数据定义。
"""

from .base import BaseSchema, TimestampMixin, PaginationSchema, ErrorSchema
from .topic import TopicSchema, TopicCreate, TopicUpdate, TopicResponse, TopicList
from .file import FileSchema, FileCreate, FileUpdate, FileResponse, FileList
from .document import DocumentSchema, DocumentCreate, DocumentUpdate, DocumentResponse, DocumentList
from .document import DocumentChunkSchema, DocumentChunkCreate, DocumentChunkResponse
from .enums import FileStatus, TopicStatus, ContentType, ChunkingStrategy, ProcessingStatus, SearchType
from .requests import (
    FileLoadRequest, ProcessingRequest, SearchRequest, 
    OrchestrationRequest, UploadUrlRequest, ConfirmUploadRequest,
    AddResourceRequest
)
from .responses import (
    ProcessingResult, SearchResult, SearchResponse,
    OrchestrationResult, UploadUrlResponse, ConfirmUploadResponse,
    APIResponse, HealthCheckResponse, PaginatedResponse
)
from .converters import (
    topic_to_schema, file_to_schema, document_to_schema,
    topic_to_response, file_to_response, document_to_response,
    topics_to_responses, files_to_responses, documents_to_responses,
    schema_to_topic_dict, schema_to_file_dict, schema_to_document_dict
)

__all__ = [
    # 基础Schema
    'BaseSchema',
    'TimestampMixin',
    'PaginationSchema',
    'ErrorSchema',
    
    # 主题Schema
    'TopicSchema',
    'TopicCreate', 
    'TopicUpdate',
    'TopicResponse',
    'TopicList',
    
    # 文件Schema
    'FileSchema',
    'FileCreate',
    'FileUpdate', 
    'FileResponse',
    'FileList',
    
    # 文档Schema
    'DocumentSchema',
    'DocumentCreate',
    'DocumentUpdate',
    'DocumentResponse',
    'DocumentList',
    'DocumentChunkSchema',
    'DocumentChunkCreate',
    'DocumentChunkResponse',
    
    # 枚举
    'FileStatus',
    'TopicStatus', 
    'ContentType',
    'ChunkingStrategy',
    'ProcessingStatus',
    'SearchType',
    
    # 请求响应Schema
    'FileLoadRequest',
    'ProcessingRequest',
    'SearchRequest',
    'OrchestrationRequest',
    'UploadUrlRequest',
    'ConfirmUploadRequest',
    'AddResourceRequest',
    'ProcessingResult',
    'SearchResult',
    'SearchResponse',
    'OrchestrationResult',
    'UploadUrlResponse',
    'ConfirmUploadResponse',
    'APIResponse',
    'HealthCheckResponse',
    'PaginatedResponse',
    
    # 转换器
    'topic_to_schema',
    'file_to_schema',
    'document_to_schema',
    'topic_to_response',
    'file_to_response',
    'document_to_response',
    'topics_to_responses',
    'files_to_responses',
    'documents_to_responses',
    'schema_to_topic_dict',
    'schema_to_file_dict',
    'schema_to_document_dict'
]
