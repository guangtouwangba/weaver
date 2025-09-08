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

from modules.vector_store.base import (
    BulkOperationResult,
    IndexType,
    IVectorStore,
    SearchFilter,
    SearchResult,
    SimilarityMetric,
    SummaryDocument,
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
    
    def _build_weaviate_filter(self, filters: SearchFilter) -> Optional[Filter]:
        """构建Weaviate原生Where过滤条件
        
        Args:
            filters: 搜索过滤条件
            
        Returns:
            Filter: Weaviate过滤对象，如果无过滤条件则返回None
        """
        if not filters or not filters.metadata_filters:
            return None
        
        try:
            filter_conditions = []
            
            for key, value in filters.metadata_filters.items():
                if key == "topic_id" and value is not None:
                    # topic_id过滤 - Weaviate要求使用字符串类型
                    filter_conditions.append(Filter.by_property("topic_id").equal(str(value)))
                    logger.debug(f"🔍 添加topic_id过滤条件: {value} (转换为字符串)")
                
                elif key == "document_id" and value is not None:
                    # document_id过滤 - 字符串类型
                    filter_conditions.append(Filter.by_property("document_id").equal(str(value)))
                    logger.debug(f"🔍 添加document_id过滤条件: {value}")
                
                elif key == "collection_type" and value is not None:
                    # collection_type过滤 - 用于区分不同类型的内容
                    filter_conditions.append(Filter.by_property("collection_type").equal(str(value)))
                    logger.debug(f"🔍 添加collection_type过滤条件: {value}")
                    
                else:
                    # 通用metadata过滤 - 在metadata JSON字段中查找
                    # 使用path查询来访问嵌套的metadata字段
                    filter_conditions.append(Filter.by_property(f"metadata.{key}").equal(value))
                    logger.debug(f"🔍 添加通用metadata过滤条件: {key}={value}")
            
            if not filter_conditions:
                return None
            
            # 如果只有一个条件，直接返回
            if len(filter_conditions) == 1:
                return filter_conditions[0]
            
            # 多个条件使用AND逻辑连接
            combined_filter = filter_conditions[0]
            for condition in filter_conditions[1:]:
                combined_filter = combined_filter & condition
                
            logger.debug(f"🔍 构建了包含{len(filter_conditions)}个条件的复合过滤器")
            return combined_filter
            
        except Exception as e:
            logger.error(f"构建Weaviate过滤器失败: {e}")
            return None

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
            
            # 检查集合中的文档总数
            try:
                total_objects = collection.aggregate.over_all(total_count=True)
                total_count = total_objects.total_count
                logger.info(f"📚 向量数据库状态: collection='{collection_name}', 总文档数={total_count}")
                
                if total_count == 0:
                    logger.warning(f"⚠️ 向量数据库为空！collection '{collection_name}' 中没有任何文档")
                    return []
                    
            except Exception as count_error:
                logger.warning(f"⚠️ 无法获取文档总数: {count_error}")
            
            # 构建Weaviate原生where过滤条件（优先使用数据库层过滤）
            where_filter = self._build_weaviate_filter(filters) if filters else None
            
            # 使用原生过滤时不需要增加搜索数量，应用层过滤时才需要
            if where_filter:
                search_limit = limit  # 数据库层已过滤，使用精确限制
                logger.debug(f"🎯 使用Weaviate原生where过滤，精确限制: {search_limit}")
            else:
                search_limit = limit * 3 if filters else limit  # 应用层过滤需要更多候选
                logger.debug(f"🔄 使用应用层过滤，扩大搜索范围: {search_limit}")
            
            logger.debug(f"🔎 Weaviate搜索参数: collection={collection_name}, "
                        f"向量维度={len(query_vector)}, limit={search_limit}, "
                        f"score_threshold={score_threshold}")
            
            # 构建查询参数，根据是否有过滤条件选择不同的调用方式
            query_params = {
                "near_vector": query_vector,
                "limit": search_limit,
                "return_metadata": ["score", "distance"]
            }
            
            # 如果有过滤条件，添加filters参数（v4客户端使用filters而不是where）
            if where_filter:
                query_params["filters"] = where_filter
                logger.debug(f"🎯 添加原生filters过滤条件: {where_filter}")
            
            response = collection.query.near_vector(**query_params)
            
            logger.debug(f"📊 Weaviate原始响应: {len(response.objects)} 个对象")
            
            # 处理结果并应用应用层过滤
            results = []
            filtered_count = 0
            score_filtered_count = 0
            
            logger.debug(f"🔍 开始处理 {len(response.objects)} 个Weaviate响应对象")
            
            for i, obj in enumerate(response.objects):
                # 计算相似度分数
                score = getattr(obj.metadata, 'score', 0.0)
                distance = getattr(obj.metadata, 'distance', 1.0)
                
                logger.debug(f"📄 处理对象 {i+1}: UUID={obj.uuid}, score={score:.4f}, distance={distance:.4f}")
                
                # 应用分数阈值
                if score_threshold and score < score_threshold:
                    score_filtered_count += 1
                    logger.debug(f"❌ 对象 {i+1} 被分数阈值过滤 (score={score:.4f} < threshold={score_threshold})")
                    continue
                
                # 反序列化metadata JSON字符串
                properties = dict(obj.properties)
                if "metadata" in properties and isinstance(properties["metadata"], str):
                    try:
                        properties["metadata"] = json.loads(properties["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        # 如果解析失败，保持原始字符串
                        logger.debug(f"⚠️ 对象 {i+1} metadata JSON解析失败，保持原始字符串")
                        pass
                
                # 应用层过滤（仅在没有使用原生where过滤时执行）
                if filters and not where_filter and not self._apply_filters_on_result(properties, filters):
                    filtered_count += 1
                    logger.debug(f"❌ 对象 {i+1} 被应用层过滤器过滤")
                    continue
                elif where_filter:
                    # 使用了原生过滤，跳过应用层过滤
                    logger.debug(f"✅ 对象 {i+1} 已通过Weaviate原生过滤")
                
                # 如果已经有足够的结果，停止处理
                if len(results) >= limit:
                    logger.debug(f"✅ 已达到结果限制 {limit}，停止处理")
                    break
                
                # 提取文档信息用于日志
                content = obj.properties.get("content", "")
                content_preview = content[:50] + "..." if len(content) > 50 else content
                doc_id = obj.properties.get("document_id", "")
                
                logger.debug(f"✅ 对象 {i+1} 通过所有过滤: UUID={obj.uuid}, "
                           f"doc_id={doc_id}, content_preview='{content_preview}'")
                
                # 创建VectorDocument
                vector_doc = VectorDocument(
                    id=str(obj.uuid),
                    content=content,
                    metadata=properties.get("metadata", {}),
                    vector=None  # 向量不需要在搜索结果中返回
                )
                
                result = SearchResult(
                    document=vector_doc,
                    score=score,
                    rank=0,  # Weaviate不提供rank，设为0
                    metadata=properties
                )
                results.append(result)
            
            # 详细的过滤统计日志
            if score_filtered_count > 0:
                logger.info(f"🎯 分数阈值过滤移除了 {score_filtered_count} 个结果 (< {score_threshold})")
            if filtered_count > 0:
                logger.info(f"🎯 应用层过滤移除了 {filtered_count} 个结果")
            if where_filter:
                logger.info(f"🚀 使用Weaviate原生where过滤，跳过应用层过滤提升性能")
            
            logger.info(f"📊 Weaviate搜索完成: 原始{len(response.objects)}个 → 最终{len(results)}个结果")
            
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
        if not filters:
            return None
        
        try:
            conditions = []
            
            # 处理metadata_filters
            if filters.metadata_filters:
                for field, value in filters.metadata_filters.items():
                    if value is not None:
                        # 根据值类型决定过滤方式
                        if isinstance(value, list):
                            conditions.append(
                                Filter.by_property(field).contains_any(value)
                            )
                        else:
                            conditions.append(
                                Filter.by_property(field).equal(value)
                            )
            
            # 处理document_ids
            if filters.document_ids:
                conditions.append(
                    Filter.by_property("document_id").contains_any(filters.document_ids)
                )
            
            # 处理content_filters
            if filters.content_filters:
                for field, value in filters.content_filters.items():
                    if value:
                        conditions.append(
                            Filter.by_property(field).like(f"*{value}*")
                        )
            
            # 处理date_range
            if filters.date_range:
                start_date, end_date = filters.date_range
                conditions.append(
                    Filter.by_property("created_at").greater_or_equal(start_date.isoformat())
                )
                conditions.append(
                    Filter.by_property("created_at").less_or_equal(end_date.isoformat())
                )
            
            # 组合条件 (默认使用AND)
            if len(conditions) == 1:
                return conditions[0]
            elif len(conditions) > 1:
                result = conditions[0]
                for condition in conditions[1:]:
                    result = result & condition
                return result
        
        except Exception as e:
            logger.warning(f"构建过滤器失败: {e}")
            return None
        
        return None

    def _apply_filters_on_result(self, properties: Dict[str, Any], filters: SearchFilter) -> bool:
        """在应用层应用过滤条件"""
        try:
            # 获取实际的metadata
            metadata = properties.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            
            # 检查metadata_filters
            if filters.metadata_filters:
                for key, expected_value in filters.metadata_filters.items():
                    actual_value = None
                    
                    # 在properties或metadata中查找值
                    if key in properties:
                        actual_value = properties[key]
                    elif key in metadata:
                        actual_value = metadata[key]
                    
                    # 检查值是否匹配
                    if actual_value is None:
                        return False
                    
                    if isinstance(expected_value, list):
                        if actual_value not in expected_value:
                            return False
                    else:
                        if actual_value != expected_value:
                            return False
            
            # 检查document_ids
            if filters.document_ids:
                document_id = properties.get("document_id") or metadata.get("document_id")
                if document_id not in filters.document_ids:
                    return False
            
            # 检查content_filters
            if filters.content_filters:
                content = properties.get("content", "")
                for field, pattern in filters.content_filters.items():
                    if pattern and pattern.lower() not in content.lower():
                        return False
            
            # 检查date_range (简化实现)
            if filters.date_range:
                # 这里可以根据需要实现日期范围过滤
                pass
            
            return True
            
        except Exception as e:
            logger.warning(f"应用过滤器时出错: {e}")
            return True  # 出错时不过滤

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
    
    async def upsert_summary_documents(
        self, summaries: List[SummaryDocument]
    ) -> BulkOperationResult:
        """插入或更新摘要文档"""
        if not summaries:
            return BulkOperationResult(0, 0, 0, 0.0)
        
        if not self._initialized:
            raise VectorStoreError("服务未初始化", provider="weaviate")
        
        start_time = time.time()
        success_count = 0
        failed_count = 0
        errors = []
        
        # 确定摘要集合名称 
        summary_collection_name = "summaries"
        
        try:
            # 确保摘要集合存在
            await self._ensure_summary_collection(summary_collection_name)
            
            collection = self._client.collections.get(summary_collection_name)
            
            # 批量插入
            with collection.batch.rate_limit(requests_per_minute=600) as batch:
                for summary in summaries:
                    try:
                        properties = {
                            "summary": summary.summary,
                            "key_topics": summary.key_topics,
                            "document_ids": summary.document_ids,
                            "scope_level": summary.scope_level,
                            "created_at": summary.created_at.isoformat(),
                            **summary.metadata
                        }
                        
                        batch.add_object(
                            properties=properties,
                            vector=summary.vector,
                            uuid=summary.id
                        )
                        success_count += 1
                        
                    except Exception as e:
                        failed_count += 1
                        errors.append(f"Failed to process summary {summary.id}: {e}")
                        logger.error(f"插入摘要文档失败 {summary.id}: {e}")
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"插入摘要文档完成: 成功={success_count}, 失败={failed_count}")
            
            return BulkOperationResult(
                success_count=success_count,
                failed_count=failed_count,
                total_count=len(summaries),
                processing_time_ms=processing_time,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"批量插入摘要文档失败: {e}")
            raise VectorStoreError(
                f"批量插入摘要文档失败: {e}",
                provider="weaviate",
                error_code="BULK_UPSERT_SUMMARIES_FAILED"
            )
    
    async def search_summaries(
        self,
        query_vector: List[float],
        top_k: int = 10,
        score_threshold: float = 0.0,
        filters: Optional[SearchFilter] = None,
    ) -> List[SearchResult]:
        """搜索摘要文档"""
        if not self._initialized:
            raise VectorStoreError("服务未初始化", provider="weaviate")
        
        summary_collection_name = "summaries"
        
        try:
            # 检查集合是否存在
            if not self._client.collections.exists(summary_collection_name):
                logger.warning(f"摘要集合 {summary_collection_name} 不存在")
                return []
            
            collection = self._client.collections.get(summary_collection_name)
            
            # 构建查询条件
            where_filter = None
            if filters and filters.metadata_filters:
                where_filter = self._build_weaviate_filter(filters)
            
            # 执行向量搜索
            query_result = collection.query.near_vector(
                near_vector=query_vector,
                limit=top_k,
                distance=1 - score_threshold if score_threshold > 0 else None,
                where=where_filter,
                return_metadata=['distance', 'certainty']
            )
            
            results = []
            for i, obj in enumerate(query_result.objects):
                # 计算相似度分数
                certainty = obj.metadata.certainty if obj.metadata.certainty is not None else 0.0
                
                # 创建摘要文档对象
                summary_doc = SummaryDocument(
                    id=str(obj.uuid),
                    vector=[],  # 不返回向量以节省内存
                    summary=obj.properties.get('summary', ''),
                    key_topics=obj.properties.get('key_topics', []),
                    document_ids=obj.properties.get('document_ids', []),
                    scope_level=obj.properties.get('scope_level', 'document'),
                    metadata={k: v for k, v in obj.properties.items() 
                             if k not in ['summary', 'key_topics', 'document_ids', 'scope_level', 'created_at']}
                )
                
                # 包装为VectorDocument以便与SearchResult兼容
                vector_doc = VectorDocument(
                    id=str(obj.uuid),
                    vector=[],
                    content=summary_doc.summary,
                    metadata={
                        'summary_document': True,
                        'key_topics': summary_doc.key_topics,
                        'document_ids': summary_doc.document_ids,
                        'scope_level': summary_doc.scope_level,
                        **summary_doc.metadata
                    }
                )
                
                result = SearchResult(
                    document=vector_doc,
                    score=certainty,
                    rank=i + 1
                )
                results.append(result)
            
            logger.info(f"摘要搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"摘要搜索失败: {e}")
            raise VectorStoreError(
                f"摘要搜索失败: {e}",
                provider="weaviate",
                error_code="SUMMARY_SEARCH_FAILED"
            )
    
    async def _ensure_summary_collection(self, collection_name: str) -> None:
        """确保摘要集合存在"""
        if not self._client.collections.exists(collection_name):
            logger.info(f"创建摘要集合: {collection_name}")
            
            # 定义摘要集合的属性
            properties = [
                Property(name="summary", data_type=DataType.TEXT),
                Property(name="key_topics", data_type=DataType.TEXT_ARRAY),
                Property(name="document_ids", data_type=DataType.TEXT_ARRAY),
                Property(name="scope_level", data_type=DataType.TEXT),
                Property(name="created_at", data_type=DataType.TEXT),
            ]
            
            # 创建集合
            self._client.collections.create(
                name=collection_name,
                properties=properties,
                vectorizer_config=Configure.Vectorizer.none(),  # 使用外部向量
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE
                ),
                description="文档摘要集合，用于高级概念和主题检索"
            )
            
            # 缓存集合配置
            self._collection_configs[collection_name] = VectorStoreConfig(
                provider=VectorStoreProvider.WEAVIATE,
                connection_string=self.url,
                collection_name=collection_name,
                dimension=1536,  # 默认OpenAI嵌入维度
                similarity_metric=SimilarityMetric.COSINE,
                index_type=IndexType.SUMMARY,
                description="摘要文档集合"
            )
            
            logger.info(f"摘要集合 {collection_name} 创建完成")

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
