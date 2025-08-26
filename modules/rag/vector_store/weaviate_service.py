"""
Weaviate向量存储服务实现

使用Weaviate作为向量数据库存储和搜索文档嵌入。
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import weaviate
from weaviate.classes.config import Configure, Property, DataType, VectorDistances
from weaviate.classes.query import Filter
from weaviate.exceptions import WeaviateBaseError

from modules.rag.vector_store.base import (
    BulkOperationResult,
    IVectorStore,
    SearchFilter,
    SearchResult,
    SimilarityMetric,
    VectorDocument,
    VectorStoreConfig,
    VectorStoreError,
    VectorStoreProvider,
)


class ProxyDisabler:
    """临时禁用系统代理设置的上下文管理器"""
    
    def __init__(self):
        self.proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        self.original_env = {}
    
    def __enter__(self):
        import os
        for var in self.proxy_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
            os.environ[var] = ''
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import os
        try:
            for var in self.proxy_vars:
                if var in self.original_env:
                    os.environ[var] = self.original_env[var]
                elif var in os.environ:
                    del os.environ[var]
        except:
            pass  # 忽略恢复环境变量时的错误

logger = logging.getLogger(__name__)


class WeaviateVectorStore(IVectorStore):
    """Weaviate向量存储服务实现"""
    
    def __init__(
        self,
        url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        batch_size: int = 100,
        create_collections_on_init: bool = False,  # 新参数：是否在初始化时创建集合
    ):
        self.url = url
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.batch_size = batch_size
        self._create_collections_on_init = create_collections_on_init
        
        self._client: Optional[weaviate.WeaviateClient] = None
        self._initialized = False
        
        # 集合配置缓存
        self._collection_configs: Dict[str, VectorStoreConfig] = {}
        
        logger.info(f"Weaviate向量存储初始化: {url}")
    
    async def initialize(self) -> None:
        """初始化向量存储"""
        if self._initialized:
            return
        
        try:
            # 直接连接，不使用代理禁用器
            # 创建客户端
            auth_config = None
            if self.api_key:
                auth_config = weaviate.auth.AuthApiKey(api_key=self.api_key)
            
            # Parse URL to get host and port
            url_parts = self.url.replace("http://", "").replace("https://", "").split(":")
            host = url_parts[0]
            port = int(url_parts[1]) if len(url_parts) > 1 else 8080
            secure = self.url.startswith("https://")
            
            # 使用纯HTTP连接，简单可靠
            self._client = weaviate.connect_to_local(
                host=host,
                port=port,
                skip_init_checks=True,
            )
            
            # 测试连接
            if not self._client.is_ready():
                raise VectorStoreError("Weaviate服务未就绪")
            
            self._initialized = True
            logger.info("Weaviate向量存储连接成功")
            
            # 如果启用了集合创建，创建默认集合(fail fast)
            if self._create_collections_on_init:
                await self._create_default_collections()
            
            logger.info("Weaviate向量存储初始化完成")
            
        except Exception as e:
            logger.error(f"Weaviate初始化失败: {e}")
            raise VectorStoreError(
                f"初始化失败: {e}",
                provider="weaviate",
                error_code="INITIALIZATION_FAILED"
            )
    
    async def cleanup(self) -> None:
        """清理向量存储资源"""
        if self._client:
            try:
                self._client.close()
            except Exception as e:
                logger.warning(f"关闭Weaviate客户端失败: {e}")
            self._client = None
        
        self._initialized = False
        logger.info("Weaviate向量存储资源已清理")
    
    async def _create_default_collections(self) -> None:
        """创建默认集合，fail fast机制"""
        default_collections = ["documents"]  # 可以添加更多默认集合
        
        for collection_name in default_collections:
            try:
                logger.info(f"检查/创建默认集合: {collection_name}")
                
                # 检查集合是否存在
                if self._client.collections.exists(collection_name):
                    logger.info(f"集合 {collection_name} 已存在")
                    continue
                
                # 创建集合配置
                default_config = VectorStoreConfig(
                    provider=VectorStoreProvider.WEAVIATE,
                    connection_string=self.url,
                    collection_name=collection_name,
                    dimension=1536,  # OpenAI text-embedding-3-small维度
                    similarity_metric=SimilarityMetric.COSINE,
                    enable_auto_vectorization=False,
                    description=f"默认RAG文档集合: {collection_name}"
                )
                
                # 创建集合
                success = await self.create_collection(default_config)
                if not success:
                    raise VectorStoreError(f"创建默认集合 {collection_name} 失败")
                
                logger.info(f"成功创建默认集合: {collection_name}")
                
            except Exception as e:
                logger.error(f"创建默认集合 {collection_name} 失败: {e}")
                # Fail fast - 如果默认集合创建失败，整个初始化失败
                raise VectorStoreError(
                    f"创建默认集合 {collection_name} 失败: {e}",
                    provider="weaviate",
                    error_code="DEFAULT_COLLECTION_CREATION_FAILED"
                )
    
    async def create_collection(self, config: VectorStoreConfig) -> bool:
        """
        创建向量集合
        
        Args:
            config: 集合配置
            
        Returns:
            bool: 创建是否成功
        """
        if not self._initialized:
            raise VectorStoreError("服务未初始化", provider="weaviate")
        
        try:
            collection_name = config.collection_name
            
            # 检查集合是否已存在
            if self._client.collections.exists(collection_name):
                logger.info(f"集合 {collection_name} 已存在")
                self._collection_configs[collection_name] = config
                return True
            
            # 创建集合属性
            properties = [
                Property(name="content", data_type=DataType.TEXT),
                Property(name="document_id", data_type=DataType.TEXT),
                Property(name="chunk_index", data_type=DataType.INT),
                Property(name="content_type", data_type=DataType.TEXT),
                Property(name="topic_id", data_type=DataType.TEXT),
                Property(name="file_id", data_type=DataType.TEXT),
                Property(name="title", data_type=DataType.TEXT),
                Property(name="metadata", data_type=DataType.TEXT),  # 使用TEXT存储JSON字符串
                Property(name="created_at", data_type=DataType.TEXT),
            ]
            
            # 向量化器配置
            vectorizer_config = None
            if config.enable_auto_vectorization:
                vectorizer_config = Configure.Vectorizer.none()  # 使用外部向量
            
            # 创建集合
            collection = self._client.collections.create(
                name=collection_name,
                properties=properties,
                vectorizer_config=vectorizer_config,
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=self._convert_similarity_metric(config.similarity_metric)
                ),
                description=f"RAG文档集合: {config.description or collection_name}",
            )
            
            self._collection_configs[collection_name] = config
            logger.info(f"成功创建集合: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建集合失败 {config.collection_name}: {e}")
            raise VectorStoreError(
                f"创建集合失败: {e}",
                provider="weaviate",
                error_code="COLLECTION_CREATION_FAILED"
            )
    
    async def delete_collection(self, collection_name: str) -> bool:
        """
        删除向量集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 删除是否成功
        """
        if not self._initialized:
            raise VectorStoreError("服务未初始化", provider="weaviate")
        
        try:
            if not self._client.collections.exists(collection_name):
                logger.warning(f"集合 {collection_name} 不存在")
                return True
            
            self._client.collections.delete(collection_name)
            
            # 清理配置缓存
            if collection_name in self._collection_configs:
                del self._collection_configs[collection_name]
            
            logger.info(f"成功删除集合: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除集合失败 {collection_name}: {e}")
            raise VectorStoreError(
                f"删除集合失败: {e}",
                provider="weaviate",
                error_code="COLLECTION_DELETION_FAILED"
            )
    
    async def upsert_vectors(
        self, documents: List[VectorDocument]
    ) -> BulkOperationResult:
        """
        批量插入或更新向量
        
        Args:
            documents: 向量文档列表
            
        Returns:
            BulkOperationResult: 批量操作结果
        """
        if not self._initialized:
            raise VectorStoreError("服务未初始化", provider="weaviate")
        
        if not documents:
            return BulkOperationResult(
                success_count=0,
                failed_count=0,
                total_count=0,
                errors=[]
            )
        
        start_time = time.time()
        # 从第一个文档的metadata中获取collection_name，如果没有则使用默认值
        collection_name = documents[0].metadata.get('collection_name', 'documents')
        
        try:
            # 确保集合存在
            await self._ensure_collection_exists(collection_name)
            
            collection = self._client.collections.get(collection_name)
            
            # 批量处理
            success_count = 0
            failed_count = 0
            errors = []
            
            for i in range(0, len(documents), self.batch_size):
                batch_docs = documents[i:i + self.batch_size]
                
                # 准备批量数据
                batch_objects = []
                for doc in batch_docs:
                    # 将metadata序列化为JSON字符串
                    metadata_json = json.dumps(doc.metadata.get("chunk_metadata", {}))
                    
                    obj_data = {
                        "content": doc.content,  # 直接使用doc.content，不是metadata中的
                        "document_id": doc.document_id or doc.metadata.get("document_id", ""),
                        "chunk_index": doc.chunk_index if hasattr(doc, 'chunk_index') else doc.metadata.get("chunk_index", 0),
                        "content_type": doc.metadata.get("content_type", ""),
                        "topic_id": doc.metadata.get("topic_id", ""),
                        "file_id": doc.metadata.get("file_id", ""),
                        "title": doc.metadata.get("title", ""),
                        "metadata": metadata_json,  # JSON字符串
                        "created_at": doc.metadata.get("created_at", ""),
                    }
                    
                    batch_objects.append({
                        "uuid": doc.id,
                        "properties": obj_data,
                        "vector": doc.vector
                    })
                
                # 执行批量插入
                try:
                    # 直接批量操作，不使用代理禁用器
                    with collection.batch.dynamic() as batch:
                        for obj in batch_objects:
                            batch.add_object(
                                properties=obj["properties"],
                                vector=obj["vector"],
                                uuid=obj["uuid"]
                            )
                    
                    success_count += len(batch_docs)
                    logger.debug(f"批量插入成功: {len(batch_docs)} 文档")
                    
                except Exception as e:
                    failed_count += len(batch_docs)
                    error_msg = f"批量插入失败: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                
                # 避免过载
                if i + self.batch_size < len(documents):
                    await asyncio.sleep(0.01)
            
            processing_time = (time.time() - start_time) * 1000
            
            result = BulkOperationResult(
                success_count=success_count,
                failed_count=failed_count,
                total_count=len(documents),
                processing_time_ms=processing_time,
                errors=errors
            )
            
            logger.info(
                f"批量向量操作完成: {success_count} 成功, {failed_count} 失败, "
                f"耗时 {processing_time:.1f}ms"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"批量向量操作失败: {e}")
            raise VectorStoreError(
                f"批量向量操作失败: {e}",
                provider="weaviate",
                error_code="BULK_OPERATION_FAILED"
            )
    
    async def upsert_single_vector(self, document: VectorDocument) -> bool:
        """
        插入或更新单个向量
        
        Args:
            document: 向量文档
            
        Returns:
            bool: 操作是否成功
        """
        result = await self.upsert_vectors([document])
        return result.success_count > 0
    
    async def search_similar(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[SearchFilter] = None,
        collection_name: str = "documents",
    ) -> List[SearchResult]:
        """
        搜索相似向量
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量限制
            score_threshold: 相似度阈值
            filters: 搜索过滤条件
            collection_name: 集合名称
            
        Returns:
            List[SearchResult]: 搜索结果列表
        """
        if not self._initialized:
            raise VectorStoreError("服务未初始化", provider="weaviate")
        
        try:
            collection = self._client.collections.get(collection_name)
            
            # 构建查询
            query_builder = collection.query.near_vector(
                near_vector=query_vector,
                limit=limit,
                return_metadata=["score", "distance"]
            )
            
            # 添加过滤条件
            if filters:
                where_filter = self._build_where_filter(filters)
                if where_filter:
                    query_builder = query_builder.where(where_filter)
            
            # 执行查询
            response = query_builder
            
            # 处理结果
            results = []
            for obj in response.objects:
                # 计算相似度分数
                score = getattr(obj.metadata, 'score', 0.0)
                distance = getattr(obj.metadata, 'distance', 1.0)
                
                # 应用分数阈值
                if score_threshold and score < score_threshold:
                    continue
                
                # 反序列化metadata JSON字符串
                properties = dict(obj.properties)
                if "metadata" in properties and isinstance(properties["metadata"], str):
                    try:
                        properties["metadata"] = json.loads(properties["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        # 如果解析失败，保持原始字符串
                        pass
                
                result = SearchResult(
                    id=str(obj.uuid),
                    score=score,
                    distance=distance,
                    metadata=properties,
                    content=obj.properties.get("content", "")
                )
                results.append(result)
            
            logger.debug(f"向量搜索完成: 查询向量维度 {len(query_vector)}, 返回 {len(results)} 结果")
            
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise VectorStoreError(
                f"向量搜索失败: {e}",
                provider="weaviate",
                error_code="SEARCH_FAILED"
            )
    
    async def delete_vectors(
        self,
        ids: List[str],
        collection_name: str = "documents"
    ) -> BulkOperationResult:
        """
        删除向量
        
        Args:
            ids: 要删除的向量ID列表
            collection_name: 集合名称
            
        Returns:
            BulkOperationResult: 批量操作结果
        """
        if not self._initialized:
            raise VectorStoreError("服务未初始化", provider="weaviate")
        
        try:
            collection = self._client.collections.get(collection_name)
            
            success_count = 0
            failed_count = 0
            errors = []
            
            for doc_id in ids:
                try:
                    collection.data.delete_by_id(doc_id)
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"删除 {doc_id} 失败: {e}")
            
            result = BulkOperationResult(
                success_count=success_count,
                failed_count=failed_count,
                total_count=len(ids),
                errors=errors
            )
            
            logger.info(f"批量删除完成: {success_count} 成功, {failed_count} 失败")
            
            return result
            
        except Exception as e:
            logger.error(f"批量删除失败: {e}")
            raise VectorStoreError(
                f"批量删除失败: {e}",
                provider="weaviate",
                error_code="BULK_DELETE_FAILED"
            )
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        获取集合信息
        
        Args:
            collection_name: 集合名称
            
        Returns:
            Dict[str, Any]: 集合信息
        """
        if not self._initialized:
            raise VectorStoreError("服务未初始化", provider="weaviate")
        
        try:
            if not self._client.collections.exists(collection_name):
                raise VectorStoreError(f"集合 {collection_name} 不存在")
            
            collection = self._client.collections.get(collection_name)
            
            # 获取集合统计信息
            aggregate_result = collection.aggregate.over_all(total_count=True)
            total_count = aggregate_result.total_count
            
            info = {
                "name": collection_name,
                "total_objects": total_count,
                "exists": True,
                "config": self._collection_configs.get(collection_name, {})
            }
            
            return info
            
        except Exception as e:
            logger.error(f"获取集合信息失败 {collection_name}: {e}")
            raise VectorStoreError(
                f"获取集合信息失败: {e}",
                provider="weaviate",
                error_code="GET_COLLECTION_INFO_FAILED"
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            "service": "weaviate_vector_store",
            "status": "healthy" if self._initialized else "not_initialized",
            "url": self.url,
            "timeout": self.timeout,
            "batch_size": self.batch_size,
        }
        
        if self._initialized and self._client:
            try:
                # 检查服务是否就绪
                is_ready = self._client.is_ready()
                status["is_ready"] = is_ready
                status["is_live"] = self._client.is_live()
                
                if is_ready:
                    # 获取服务器信息
                    meta_info = self._client.get_meta()
                    status["version"] = meta_info.get("version", "unknown")
                
            except Exception as e:
                status["status"] = "unhealthy"
                status["error"] = str(e)
        
        return status
    
    async def _ensure_collection_exists(self, collection_name: str) -> None:
        """确保集合存在(通常在启动时已创建，这是备用检查)"""
        if not self._client.collections.exists(collection_name):
            logger.warning(f"集合 {collection_name} 不存在，尝试创建...")
            
            # 使用默认配置创建集合
            default_config = VectorStoreConfig(
                provider=VectorStoreProvider.WEAVIATE,
                connection_string=self.url,
                collection_name=collection_name,
                dimension=1536,  # 默认OpenAI嵌入维度
                similarity_metric=SimilarityMetric.COSINE,
                enable_auto_vectorization=False,  # 我们提供自己的向量
                description=f"运行时创建的集合: {collection_name}"
            )
            
            success = await self.create_collection(default_config)
            if not success:
                raise VectorStoreError(f"运行时创建集合 {collection_name} 失败")
            
            logger.info(f"运行时成功创建集合: {collection_name}")
        else:
            logger.debug(f"集合 {collection_name} 已存在")
    
    def _convert_similarity_metric(self, metric: SimilarityMetric) -> VectorDistances:
        """转换相似度度量为Weaviate VectorDistances枚举"""
        mapping = {
            SimilarityMetric.COSINE: VectorDistances.COSINE,
            SimilarityMetric.DOT_PRODUCT: VectorDistances.DOT,
            SimilarityMetric.EUCLIDEAN: VectorDistances.L2_SQUARED,
            SimilarityMetric.MANHATTAN: VectorDistances.MANHATTAN,
        }
        return mapping.get(metric, VectorDistances.COSINE)
    
    def _build_where_filter(self, filters: SearchFilter) -> Optional[Filter]:
        """构建Weaviate查询过滤器"""
        if not filters or not filters.conditions:
            return None
        
        try:
            # 简化的过滤器实现
            conditions = []
            for condition in filters.conditions:
                if condition.operator == "eq":
                    conditions.append(
                        Filter.by_property(condition.field).equal(condition.value)
                    )
                elif condition.operator == "neq":
                    conditions.append(
                        Filter.by_property(condition.field).not_equal(condition.value)
                    )
                elif condition.operator == "in":
                    if isinstance(condition.value, list):
                        conditions.append(
                            Filter.by_property(condition.field).contains_any(condition.value)
                        )
            
            # 组合条件
            if len(conditions) == 1:
                return conditions[0]
            elif len(conditions) > 1:
                if filters.operator == "AND":
                    result = conditions[0]
                    for condition in conditions[1:]:
                        result = result & condition
                    return result
                else:  # OR
                    result = conditions[0]
                    for condition in conditions[1:]:
                        result = result | condition
                    return result
        
        except Exception as e:
            logger.warning(f"构建过滤器失败: {e}")
            return None
        
        return None

    async def get_vector_by_id(self, vector_id: str) -> Optional[VectorDocument]:
        """根据ID获取向量"""
        if not self._client:
            await self.initialize()
        
        try:
            # 获取默认集合
            collection_name = "documents"  # Default collection name
            collection = self._client.collections.get(collection_name)
            
            # 查询向量
            response = collection.query.fetch_object_by_id(vector_id)
            if not response:
                return None
            
            # 转换为VectorDocument
            properties = response.properties
            return VectorDocument(
                id=vector_id,
                vector=response.vector if hasattr(response, 'vector') else [],
                content=properties.get('content', ''),
                metadata=properties.get('metadata', {}),
                document_id=properties.get('document_id'),
                chunk_index=properties.get('chunk_index'),
            )
            
        except Exception as e:
            logger.error(f"获取向量失败 {vector_id}: {e}")
            return None

    async def delete_vectors_by_document_id(self, document_id: str) -> BulkOperationResult:
        """根据文档ID删除所有相关向量"""
        if not self._client:
            await self.initialize()
        
        try:
            collection_name = "documents"  # Default collection name
            collection = self._client.collections.get(collection_name)
            
            # 查询该文档的所有向量
            where_filter = Filter.by_property("document_id").equal(document_id)
            
            # 删除向量
            result = collection.data.delete_many(where=where_filter)
            
            return BulkOperationResult(
                successful=result.successful if hasattr(result, 'successful') else 0,
                failed=result.failed if hasattr(result, 'failed') else 0,
                errors=[]
            )
            
        except Exception as e:
            logger.error(f"根据文档ID删除向量失败 {document_id}: {e}")
            return BulkOperationResult(successful=0, failed=1, errors=[str(e)])

    async def update_metadata(self, vector_id: str, metadata: Dict[str, Any]) -> bool:
        """更新向量元数据"""
        if not self._client:
            await self.initialize()
        
        try:
            collection_name = "documents"  # Default collection name
            collection = self._client.collections.get(collection_name)
            
            # 更新元数据
            collection.data.update(
                uuid=vector_id,
                properties={"metadata": metadata}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"更新向量元数据失败 {vector_id}: {e}")
            return False

    async def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        if not self._client:
            await self.initialize()
        
        try:
            collection_name = "documents"  # Default collection name
            collection = self._client.collections.get(collection_name)
            
            # 获取集合信息
            response = collection.aggregate.over_all()
            
            return {
                "collection_name": collection_name,
                "total_objects": response.total_count if hasattr(response, 'total_count') else 0,
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"获取集合统计信息失败: {e}")
            return {
                "collection_name": "documents",
                "total_objects": 0,
                "status": "error",
                "error": str(e)
            }

    @property
    def service_name(self) -> str:
        """获取服务名称"""
        return "weaviate"

    @property
    def config(self) -> VectorStoreConfig:
        """获取配置信息"""
        return VectorStoreConfig(
            provider=VectorStoreProvider.WEAVIATE,
            connection_string=self.url,
            collection_name="documents",  # Default collection name
            dimension=1536,  # Default OpenAI embedding dimension
            similarity_metric=SimilarityMetric.COSINE,
            batch_size=self.batch_size,
            enable_auto_vectorization=False,  # 我们提供自己的向量
            description="默认文档集合"
        )
