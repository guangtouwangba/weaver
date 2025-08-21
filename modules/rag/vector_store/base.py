"""
向量存储服务接口定义

定义向量存储和相似性搜索的标准接口，支持多种向量数据库。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple
from enum import Enum
from datetime import datetime


class VectorStoreProvider(Enum):
    """向量存储提供商"""
    WEAVIATE = "weaviate"
    PGVECTOR = "pgvector"
    CHROMADB = "chromadb"
    QDRANT = "qdrant"
    MILVUS = "milvus"


class SimilarityMetric(Enum):
    """相似性度量方式"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"


class VectorStoreConfig:
    """向量存储配置"""
    
    def __init__(self,
                 provider: VectorStoreProvider,
                 connection_string: str,
                 collection_name: str,
                 dimension: int,
                 similarity_metric: SimilarityMetric = SimilarityMetric.COSINE,
                 index_type: Optional[str] = None,
                 batch_size: int = 100,
                 max_connections: int = 10,
                 **kwargs):
        self.provider = provider
        self.connection_string = connection_string
        self.collection_name = collection_name
        self.dimension = dimension
        self.similarity_metric = similarity_metric
        self.index_type = index_type
        self.batch_size = batch_size
        self.max_connections = max_connections
        self.extra_params = kwargs


class VectorDocument:
    """向量文档"""
    
    def __init__(self,
                 id: str,
                 vector: List[float],
                 content: str,
                 metadata: Optional[Dict[str, Any]] = None,
                 document_id: Optional[str] = None,
                 chunk_index: Optional[int] = None,
                 created_at: Optional[datetime] = None):
        self.id = id
        self.vector = vector
        self.content = content
        self.metadata = metadata or {}
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.created_at = created_at or datetime.utcnow()


class SearchResult:
    """搜索结果"""
    
    def __init__(self,
                 document: VectorDocument,
                 score: float,
                 rank: int,
                 metadata: Optional[Dict[str, Any]] = None):
        self.document = document
        self.score = score
        self.rank = rank
        self.metadata = metadata or {}


class SearchFilter:
    """搜索过滤器"""
    
    def __init__(self,
                 document_ids: Optional[List[str]] = None,
                 metadata_filters: Optional[Dict[str, Any]] = None,
                 date_range: Optional[Tuple[datetime, datetime]] = None,
                 content_filters: Optional[Dict[str, str]] = None):
        self.document_ids = document_ids
        self.metadata_filters = metadata_filters
        self.date_range = date_range
        self.content_filters = content_filters


class BulkOperationResult:
    """批量操作结果"""
    
    def __init__(self,
                 success_count: int,
                 failed_count: int,
                 total_count: int,
                 processing_time_ms: float,
                 errors: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.success_count = success_count
        self.failed_count = failed_count
        self.total_count = total_count
        self.processing_time_ms = processing_time_ms
        self.errors = errors or []
        self.metadata = metadata or {}


class VectorStoreError(Exception):
    """向量存储错误"""
    
    def __init__(self, message: str, provider: Optional[str] = None,
                 error_code: Optional[str] = None, original_error: Optional[Exception] = None):
        self.provider = provider
        self.error_code = error_code
        self.original_error = original_error
        super().__init__(message)


class IVectorStore(ABC):
    """向量存储接口"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化向量存储
        
        Raises:
            VectorStoreError: 初始化失败时抛出
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理向量存储资源"""
        pass
    
    @abstractmethod
    async def create_collection(self, config: VectorStoreConfig) -> bool:
        """
        创建向量集合
        
        Args:
            config: 集合配置
            
        Returns:
            bool: 创建是否成功
            
        Raises:
            VectorStoreError: 创建失败时抛出
        """
        pass
    
    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        """
        删除向量集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 删除是否成功
            
        Raises:
            VectorStoreError: 删除失败时抛出
        """
        pass
    
    @abstractmethod
    async def upsert_vectors(self, documents: List[VectorDocument]) -> BulkOperationResult:
        """
        插入或更新向量
        
        Args:
            documents: 向量文档列表
            
        Returns:
            BulkOperationResult: 批量操作结果
            
        Raises:
            VectorStoreError: 操作失败时抛出
        """
        pass
    
    @abstractmethod
    async def upsert_single_vector(self, document: VectorDocument) -> bool:
        """
        插入或更新单个向量
        
        Args:
            document: 向量文档
            
        Returns:
            bool: 操作是否成功
            
        Raises:
            VectorStoreError: 操作失败时抛出
        """
        pass
    
    @abstractmethod
    async def search_similar(self, 
                           query_vector: List[float],
                           limit: int = 10,
                           score_threshold: Optional[float] = None,
                           filters: Optional[SearchFilter] = None) -> List[SearchResult]:
        """
        相似性搜索
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量限制
            score_threshold: 相似性分数阈值
            filters: 搜索过滤器
            
        Returns:
            List[SearchResult]: 搜索结果列表
            
        Raises:
            VectorStoreError: 搜索失败时抛出
        """
        pass
    
    @abstractmethod
    async def get_vector_by_id(self, vector_id: str) -> Optional[VectorDocument]:
        """
        根据ID获取向量
        
        Args:
            vector_id: 向量ID
            
        Returns:
            Optional[VectorDocument]: 向量文档，不存在返回None
            
        Raises:
            VectorStoreError: 获取失败时抛出
        """
        pass
    
    @abstractmethod
    async def delete_vectors(self, vector_ids: List[str]) -> BulkOperationResult:
        """
        删除向量
        
        Args:
            vector_ids: 向量ID列表
            
        Returns:
            BulkOperationResult: 批量操作结果
            
        Raises:
            VectorStoreError: 删除失败时抛出
        """
        pass
    
    @abstractmethod
    async def delete_vectors_by_document_id(self, document_id: str) -> BulkOperationResult:
        """
        根据文档ID删除相关向量
        
        Args:
            document_id: 文档ID
            
        Returns:
            BulkOperationResult: 批量操作结果
            
        Raises:
            VectorStoreError: 删除失败时抛出
        """
        pass
    
    @abstractmethod
    async def update_metadata(self, vector_id: str, metadata: Dict[str, Any]) -> bool:
        """
        更新向量元数据
        
        Args:
            vector_id: 向量ID
            metadata: 新的元数据
            
        Returns:
            bool: 更新是否成功
            
        Raises:
            VectorStoreError: 更新失败时抛出
        """
        pass
    
    @abstractmethod
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
            
        Raises:
            VectorStoreError: 获取失败时抛出
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        pass
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """
        获取服务名称
        
        Returns:
            str: 服务名称
        """
        pass
    
    @property
    @abstractmethod
    def config(self) -> VectorStoreConfig:
        """
        获取配置信息
        
        Returns:
            VectorStoreConfig: 配置对象
        """
        pass