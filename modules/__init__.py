from config import get_config, PydanticAppConfig as AppConfig, PydanticDatabaseConfig as DatabaseConfig, PydanticStorageConfig as StorageConfig
from .api import api_router
from .database import DatabaseConnection, get_session, get_db_session
from .storage import IStorage, MockStorage, LocalStorage


from .schemas import (
    # Base schemas
    BaseSchema, TimestampMixin, PaginationSchema, ErrorSchema,
    
    # Domain schemas
    TopicSchema, TopicCreate, TopicUpdate, TopicResponse, TopicList,
    FileSchema, FileCreate, FileUpdate, FileResponse, FileList,
    DocumentSchema, DocumentCreate, DocumentUpdate, DocumentResponse, DocumentList,
    DocumentChunkSchema, DocumentChunkCreate, DocumentChunkResponse,
    
    # Enums
    FileStatus, TopicStatus, ContentType, ChunkingStrategy, ProcessingStatus, SearchType,
    
    # Request/Response schemas
    FileLoadRequest, ProcessingRequest, SearchRequest,
    OrchestrationRequest, UploadUrlRequest, ConfirmUploadRequest,
    ProcessingResult, SearchResult, SearchResponse,
    OrchestrationResult, UploadUrlResponse, ConfirmUploadResponse,
    APIResponse, HealthCheckResponse, PaginatedResponse,
    
    # Converters
    topic_to_schema, file_to_schema, document_to_schema,
    topic_to_response, file_to_response, document_to_response,
    topics_to_responses, files_to_responses, documents_to_responses,
    schema_to_topic_dict, schema_to_file_dict, schema_to_document_dict
)


from .repository import (
    IBaseRepository, ITopicRepository, IFileRepository, IDocumentRepository,
    BaseRepository, TopicRepository, FileRepository, DocumentRepository
)


from .services import (
    BaseService, TopicService, FileService, DocumentService
)

from .models import (
    Document, DocumentChunk, ContentType, ChunkingStrategy,
    ProcessingStatus, ProcessingRequest, ProcessingResult,
    SearchRequest, SearchResult, OrchestrationRequest, OrchestrationResult,
    SearchQuery, SearchResponse, ModuleConfig, ModuleInterface,
    FileLoaderError, DocumentProcessorError, create_document_from_path
)

from .file_loader import (
    IFileLoader, TextFileLoader
    # MultiFormatFileLoader temporarily disabled pending refactoring
)

from . import rag

__all__ = [
    # 配置相关
    'get_config',
    'AppConfig',
    'DatabaseConfig',
    'StorageConfig',
    
    # API层
    'api_router',
    
    
    # 数据库相关
    'DatabaseConnection',
    'get_session',
    'get_db_session',
    
    # 存储相关
    'IStorage',
    'MockStorage',
    'LocalStorage',
    
    
    # Schema层
    'BaseSchema', 'TimestampMixin', 'PaginationSchema', 'ErrorSchema',
    'TopicSchema', 'TopicCreate', 'TopicUpdate', 'TopicResponse', 'TopicList',
    'FileSchema', 'FileCreate', 'FileUpdate', 'FileResponse', 'FileList',
    'DocumentSchema', 'DocumentCreate', 'DocumentUpdate', 'DocumentResponse', 'DocumentList',
    'DocumentChunkSchema', 'DocumentChunkCreate', 'DocumentChunkResponse',
    'FileStatus', 'TopicStatus', 'ContentType', 'ChunkingStrategy', 'ProcessingStatus', 'SearchType',
    'FileLoadRequest', 'ProcessingRequest', 'SearchRequest',
    'OrchestrationRequest', 'UploadUrlRequest', 'ConfirmUploadRequest',
    'ProcessingResult', 'SearchResult', 'SearchResponse',
    'OrchestrationResult', 'UploadUrlResponse', 'ConfirmUploadResponse',
    'APIResponse', 'HealthCheckResponse', 'PaginatedResponse',
    'topic_to_schema', 'file_to_schema', 'document_to_schema',
    'topic_to_response', 'file_to_response', 'document_to_response',
    'topics_to_responses', 'files_to_responses', 'documents_to_responses',
    'schema_to_topic_dict', 'schema_to_file_dict', 'schema_to_document_dict',
    
    # Repository层
    'IBaseRepository', 'ITopicRepository', 'IFileRepository', 'IDocumentRepository',
    'BaseRepository', 'TopicRepository', 'FileRepository', 'DocumentRepository',
    
    # Service层
    'BaseService', 'TopicService', 'FileService', 'DocumentService',
    
    # 兼容性模型
    'Document', 'DocumentChunk', 'ContentType', 'ChunkingStrategy',
    'ProcessingStatus', 'ProcessingRequest', 'ProcessingResult',
    'SearchRequest', 'SearchResult', 'OrchestrationRequest', 'OrchestrationResult',
    'SearchQuery', 'SearchResponse', 'ModuleConfig', 'ModuleInterface',
    'FileLoaderError', 'DocumentProcessorError', 'create_document_from_path',
    
    # 文件加载模块
    'IFileLoader', 'TextFileLoader',

    # RAG模块
    'rag',
]