"""
模块化RAG系统

一个简单、解耦的文档处理和检索系统。

使用示例:
    # 简单使用
    from modules import RagAPI
    
    api = RagAPI()
    result = await api.process_file("document.pdf")
    search_results = await api.search("查询内容")
    
    # 兼容原有API
    from modules import APIAdapter
    
    adapter = APIAdapter()
    result = await adapter.confirm_upload_completion("file_id", "document.pdf")
"""

# 核心模块
from .models import (
    Document, DocumentChunk, ContentType, ChunkingStrategy,
    ProcessingStatus, ProcessingRequest, ProcessingResult,
    SearchRequest, SearchResult, OrchestrationRequest, OrchestrationResult,
    # 兼容性模型
    SearchQuery, SearchResponse, ModuleConfig, ModuleInterface,
    FileLoaderError, DocumentProcessorError
)

# 文件加载模块
from .file_loader import (
    IFileLoader, TextFileLoader, MultiFormatFileLoader
)

# 文档处理模块
from .document_processor import (
    IDocumentProcessor, TextProcessor, ChunkingProcessor
)

# 编排模块
from .orchestrator import (
    IOrchestrator, DocumentOrchestrator
)

# API模块
from .api import (
    IModularAPI, RagAPI, APIError
)

# 兼容层
from .compatibility import APIAdapter

# 数据库模块
from .database import (
    DatabaseConnection, get_session, DatabaseService,
    Topic, File, Document, DocumentChunk,
    TopicRepository, FileRepository, DocumentRepository
)

# 存储模块
from .storage import IStorage, MockStorage, LocalStorage

# 文件上传模块
from .file_upload import FileUploadService, IFileUploadService

# 便捷导入
__all__ = [
    # 核心模型
    'Document', 'DocumentChunk', 'ContentType', 'ChunkingStrategy',
    'ProcessingStatus', 'ProcessingRequest', 'ProcessingResult',
    'SearchRequest', 'SearchResult', 'OrchestrationRequest', 'OrchestrationResult',
    
    # 兼容性模型
    'SearchQuery', 'SearchResponse', 'ModuleConfig', 'ModuleInterface',
    
    # 接口
    'IFileLoader', 'IDocumentProcessor', 'IOrchestrator', 'IModularAPI',
    
    # 实现
    'TextFileLoader', 'MultiFormatFileLoader',
    'TextProcessor', 'ChunkingProcessor',
    'DocumentOrchestrator',
    'RagAPI',
    
    # 异常
    'APIError', 'FileLoaderError', 'DocumentProcessorError',
    
    # 兼容层
    'APIAdapter',
    
    # 数据库
    'DatabaseConnection', 'get_session', 'DatabaseService',
    'Topic', 'File', 'Document', 'DocumentChunk',
    'TopicRepository', 'FileRepository', 'DocumentRepository',
    
    # 存储
    'IStorage', 'MockStorage', 'LocalStorage',
    
    # 文件上传
    'FileUploadService', 'IFileUploadService'
]

# 版本信息
__version__ = "1.0.0"
__author__ = "RAG System Team"
__description__ = "模块化RAG文档处理系统"