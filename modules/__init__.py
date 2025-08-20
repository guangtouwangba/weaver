"""
模块化RAG系统

一个简单、解耦的文档处理和检索系统。

使用示例:
    # 配置系统
    from modules import get_config
    config = get_config()
    
    # API系统
    from modules import api_router
    
    # 兼容原有API
    from modules import APIAdapter
    adapter = APIAdapter()
"""

# 导入配置模块
from .config import get_config, AppConfig, DatabaseConfig, StorageConfig

# 导入新的Service层API
from .api import api_router

# 导入兼容性层  
from .compatibility import APIAdapter

# 导入数据库相关
from .database import DatabaseConnection, get_session, get_db_session

# 导入存储相关
from .storage import IStorage, MockStorage, LocalStorage

# 导入文件上传
from .file_upload import FileUploadService

# 导入Schema层
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

# 导入Repository层
from .repository import (
    IBaseRepository, ITopicRepository, IFileRepository, IDocumentRepository,
    BaseRepository, TopicRepository, FileRepository, DocumentRepository
)

# 导入Service层
from .services import (
    BaseService, TopicService, FileService, DocumentService
)

# 导入兼容性模型（为了向后兼容）
from .models import (
    Document, DocumentChunk, ContentType, ChunkingStrategy,
    ProcessingStatus, ProcessingRequest, ProcessingResult,
    SearchRequest, SearchResult, OrchestrationRequest, OrchestrationResult,
    SearchQuery, SearchResponse, ModuleConfig, ModuleInterface,
    FileLoaderError, DocumentProcessorError, create_document_from_path
)

# 导入文件加载模块
from .file_loader import (
    IFileLoader, TextFileLoader, MultiFormatFileLoader
)

# 导入文档处理模块
from .document_processor import (
    IDocumentProcessor, TextProcessor, ChunkingProcessor
)

# 导入编排模块
from .orchestrator import (
    IOrchestrator, DocumentOrchestrator
)

__all__ = [
    # 配置相关
    'get_config',
    'AppConfig',
    'DatabaseConfig',
    'StorageConfig',
    
    # API层
    'api_router',
    
    # 兼容性层
    'APIAdapter',
    
    # 数据库相关
    'DatabaseConnection',
    'get_session',
    'get_db_session',
    
    # 存储相关
    'IStorage',
    'MockStorage',
    'LocalStorage',
    
    # 文件上传
    'FileUploadService',
    
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
    'IFileLoader', 'TextFileLoader', 'MultiFormatFileLoader',
    
    # 文档处理模块
    'IDocumentProcessor', 'TextProcessor', 'ChunkingProcessor',
    
    # 编排模块
    'IOrchestrator', 'DocumentOrchestrator',
]