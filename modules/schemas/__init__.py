"""
Schema模块

使用Pydantic定义全局统一的数据模式，提供类型安全和序列化支持。
减少数据分层，统一数据定义。
"""

from modules.schemas.base import (
    BaseSchema,
    ErrorSchema,
    PaginationSchema,
    TimestampMixin,
)
from modules.schemas.converters import (
    document_to_response,
    document_to_schema,
    documents_to_responses,
    file_to_response,
    file_to_schema,
    files_to_responses,
    schema_to_document_dict,
    schema_to_file_dict,
    schema_to_topic_dict,
    topic_to_response,
    topic_to_schema,
    topics_to_responses,
)
from modules.schemas.document import (
    Document,
    DocumentChunk,
    DocumentChunkCreate,
    DocumentChunkResponse,
    DocumentChunkSchema,
    DocumentCreate,
    DocumentList,
    DocumentResponse,
    DocumentSchema,
    DocumentUpdate,
    create_document_from_path,
)
from modules.schemas.enums import (
    ChunkingStrategy,
    ContentType,
    FileStatus,
    ProcessingStatus,
    SearchType,
    TaskName,
    TopicStatus,
)
from modules.schemas.file import (
    FileCreate,
    FileList,
    FileResponse,
    FileSchema,
    FileUpdate,
)
from modules.schemas.requests import (
    AddResourceRequest,
    ConfirmUploadRequest,
    FileLoadRequest,
    OrchestrationRequest,
    ProcessingRequest,
    SearchRequest,
    UploadUrlRequest,
)
from modules.schemas.responses import (
    APIResponse,
    ConfirmUploadResponse,
    HealthCheckResponse,
    OrchestrationResult,
    PaginatedResponse,
    ProcessingResult,
    SearchResponse,
    SearchResult,
    UploadUrlResponse,
)
from modules.schemas.topic import (
    TopicCreate,
    TopicList,
    TopicResponse,
    TopicSchema,
    TopicUpdate,
)
from modules.schemas.chat import (
    # Enums
    MessageRole,
    SSEEventType,
    
    # Basic schemas
    RetrievedContext,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    AIMetadata,
    
    # SSE event schemas
    SSEStartEvent,
    SSEProgressEvent,
    SSEContextEvent,
    SSEDeltaEvent,
    SSECompleteEvent,
    SSEErrorEvent,
    
    # Conversation management
    ConversationSummary,
    ConversationListRequest,
    ConversationListResponse,
    MessageHistoryRequest,
    MessageHistoryResponse,
    
    # Search functionality
    ChatSearchRequest,
    ChatSearchResult,
    ChatSearchResponse,
    
    # Statistics
    ChatStatisticsResponse,
)

__all__ = [
    # 基础Schema
    "BaseSchema",
    "TimestampMixin",
    "PaginationSchema",
    "ErrorSchema",
    # 主题Schema
    "TopicSchema",
    "TopicCreate",
    "TopicUpdate",
    "TopicResponse",
    "TopicList",
    # 文件Schema
    "FileSchema",
    "FileCreate",
    "FileUpdate",
    "FileResponse",
    "FileList",
    # 文档Schema
    "Document",
    "DocumentChunk",
    "DocumentSchema",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentList",
    "DocumentChunkSchema",
    "DocumentChunkCreate",
    "DocumentChunkResponse",
    # 枚举
    "FileStatus",
    "TopicStatus",
    "ContentType",
    "ChunkingStrategy",
    "ProcessingStatus",
    "SearchType",
    "TaskName",
    # 请求响应Schema
    "FileLoadRequest",
    "ProcessingRequest",
    "SearchRequest",
    "OrchestrationRequest",
    "UploadUrlRequest",
    "ConfirmUploadRequest",
    "AddResourceRequest",
    "ProcessingResult",
    "SearchResult",
    "SearchResponse",
    "OrchestrationResult",
    "UploadUrlResponse",
    "ConfirmUploadResponse",
    "APIResponse",
    "HealthCheckResponse",
    "PaginatedResponse",
    # 转换器
    "topic_to_schema",
    "file_to_schema",
    "document_to_schema",
    "topic_to_response",
    "file_to_response",
    "document_to_response",
    "topics_to_responses",
    "files_to_responses",
    "documents_to_responses",
    "schema_to_topic_dict",
    "schema_to_file_dict",
    "schema_to_document_dict",
    "create_document_from_path",
    # Chat相关Schema
    "MessageRole",
    "SSEEventType",
    "RetrievedContext",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "AIMetadata",
    "SSEStartEvent",
    "SSEProgressEvent",
    "SSEContextEvent",
    "SSEDeltaEvent",
    "SSECompleteEvent",
    "SSEErrorEvent",
    "ConversationSummary",
    "ConversationListRequest",
    "ConversationListResponse",
    "MessageHistoryRequest",
    "MessageHistoryResponse",
    "ChatSearchRequest",
    "ChatSearchResult",
    "ChatSearchResponse",
    "ChatStatisticsResponse",
]
