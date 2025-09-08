"""
检索器组件实现

将现有的检索服务重构为模块化的检索器组件。
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from modules.rag.base import (
    IRetriever,
    RetrievedDocument,
    RAGContext,
    RAGPipelineError,
)
from modules.vector_store.base import IVectorStore, SearchFilter
from modules.embedding.base import IEmbeddingService

logger = logging.getLogger(__name__)


class VectorRetriever(IRetriever):
    """向量检索器 - 基于现有向量存储服务"""
    
    def __init__(
        self,
        vector_store: IVectorStore,
        embedding_service: IEmbeddingService,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(config)
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        
        # 配置参数
        self.default_top_k = config.get("default_top_k", 10)
        self.default_score_threshold = config.get("default_score_threshold", 0.0)
        self.collection_name = config.get("collection_name", "documents")
        
        logger.info(f"VectorRetriever 初始化: collection={self.collection_name}")
    
    async def initialize(self) -> None:
        """初始化向量检索器"""
        if self._initialized:
            return
        
        try:
            # 确保向量存储和嵌入服务已初始化
            if not self.vector_store._initialized:
                await self.vector_store.initialize()
            
            if not self.embedding_service._initialized:
                await self.embedding_service.initialize()
            
            self._initialized = True
            logger.info("VectorRetriever 初始化完成")
            
        except Exception as e:
            logger.error(f"VectorRetriever 初始化失败: {e}")
            raise RAGPipelineError(
                f"向量检索器初始化失败: {e}",
                component_type=self.component_type
            )
    
    async def process(self, context: RAGContext) -> RAGContext:
        """处理RAG上下文 - 执行向量检索"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 从上下文获取检索参数
            top_k = context.user_context.get("top_k", self.default_top_k)
            score_threshold = context.user_context.get("score_threshold", self.default_score_threshold)
            filters = context.user_context.get("filters")
            
            # 执行检索
            documents = await self.retrieve(
                query=context.query,
                top_k=top_k,
                filters=filters
            )
            
            # 过滤低分文档
            if score_threshold > 0:
                documents = [doc for doc in documents if doc.score >= score_threshold]
            
            # 更新上下文
            context.retrieved_documents.extend(documents)
            
            # 记录检索元数据
            context.processing_metadata["vector_retrieval"] = {
                "documents_found": len(documents),
                "top_k": top_k,
                "score_threshold": score_threshold,
                "collection_name": self.collection_name,
                "avg_score": sum(doc.score for doc in documents) / len(documents) if documents else 0.0
            }
            
            logger.info(f"向量检索完成: 找到 {len(documents)} 个文档")
            
            return context
            
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            raise RAGPipelineError(
                f"向量检索失败: {e}",
                component_type=self.component_type
            )
    
    async def retrieve(
        self, 
        query: str, 
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedDocument]:
        """检索相关文档"""
        try:
            start_time = time.time()
            
            # 生成查询向量
            query_vector = await self.embedding_service.generate_embedding(query)
            
            # 构建搜索过滤器
            search_filter = None
            if filters:
                search_filter = SearchFilter(
                    metadata_filters=filters.get("metadata_filters"),
                    document_ids=filters.get("document_ids"),
                    content_filters=filters.get("content_filters"),
                    date_range=filters.get("date_range")
                )
            
            # 执行向量搜索
            search_results = await self.vector_store.search_similar(
                query_vector=query_vector,
                limit=top_k,
                score_threshold=0.0,  # 在这里不过滤，让调用者决定
                filters=search_filter,
                collection_name=self.collection_name
            )
            
            # 转换为RetrievedDocument格式
            documents = []
            for i, result in enumerate(search_results):
                doc = RetrievedDocument(
                    id=result.document.id,
                    content=result.document.content,
                    score=result.score,
                    source="vector_store",
                    metadata=result.document.metadata,
                    rank=i + 1
                )
                documents.append(doc)
            
            retrieval_time = (time.time() - start_time) * 1000
            logger.debug(f"向量检索耗时: {retrieval_time:.1f}ms, 结果数: {len(documents)}")
            
            return documents
            
        except Exception as e:
            logger.error(f"向量检索执行失败: {e}")
            raise RAGPipelineError(f"向量检索执行失败: {e}")
    
    async def batch_retrieve(
        self, 
        queries: List[str], 
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[List[RetrievedDocument]]:
        """批量检索"""
        try:
            # 并行执行多个检索
            tasks = [
                self.retrieve(query, top_k, filters)
                for query in queries
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果和异常
            batch_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"批量检索第 {i} 个查询失败: {result}")
                    batch_results.append([])
                else:
                    batch_results.append(result)
            
            return batch_results
            
        except Exception as e:
            logger.error(f"批量检索失败: {e}")
            raise RAGPipelineError(f"批量检索失败: {e}")


class SummaryRetriever(IRetriever):
    """摘要检索器 - 检索文档摘要"""
    
    def __init__(
        self,
        vector_store: IVectorStore,
        embedding_service: IEmbeddingService,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(config)
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        
        # 配置参数
        self.default_top_k = config.get("default_top_k", 5)
        self.default_score_threshold = config.get("default_score_threshold", 0.75)
        
        logger.info("SummaryRetriever 初始化")
    
    async def initialize(self) -> None:
        """初始化摘要检索器"""
        if self._initialized:
            return
        
        try:
            # 确保依赖服务已初始化
            if not self.vector_store._initialized:
                await self.vector_store.initialize()
            
            if not self.embedding_service._initialized:
                await self.embedding_service.initialize()
            
            self._initialized = True
            logger.info("SummaryRetriever 初始化完成")
            
        except Exception as e:
            logger.error(f"SummaryRetriever 初始化失败: {e}")
            raise RAGPipelineError(
                f"摘要检索器初始化失败: {e}",
                component_type=self.component_type
            )
    
    async def process(self, context: RAGContext) -> RAGContext:
        """处理RAG上下文 - 执行摘要检索"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 从上下文获取检索参数
            top_k = context.user_context.get("summary_top_k", self.default_top_k)
            score_threshold = context.user_context.get("summary_score_threshold", self.default_score_threshold)
            filters = context.user_context.get("filters")
            
            # 执行摘要检索
            documents = await self.retrieve(
                query=context.query,
                top_k=top_k,
                filters=filters
            )
            
            # 过滤低分文档
            if score_threshold > 0:
                documents = [doc for doc in documents if doc.score >= score_threshold]
            
            # 标记为摘要文档
            for doc in documents:
                doc.metadata["is_summary"] = True
                doc.source = "summary_store"
            
            # 更新上下文
            context.retrieved_documents.extend(documents)
            
            # 记录检索元数据
            context.processing_metadata["summary_retrieval"] = {
                "documents_found": len(documents),
                "top_k": top_k,
                "score_threshold": score_threshold,
                "avg_score": sum(doc.score for doc in documents) / len(documents) if documents else 0.0
            }
            
            logger.info(f"摘要检索完成: 找到 {len(documents)} 个摘要文档")
            
            return context
            
        except Exception as e:
            logger.error(f"摘要检索失败: {e}")
            raise RAGPipelineError(
                f"摘要检索失败: {e}",
                component_type=self.component_type
            )
    
    async def retrieve(
        self, 
        query: str, 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedDocument]:
        """检索相关摘要"""
        try:
            start_time = time.time()
            
            # 生成查询向量
            query_vector = await self.embedding_service.generate_embedding(query)
            
            # 构建搜索过滤器
            search_filter = None
            if filters:
                search_filter = SearchFilter(
                    metadata_filters=filters.get("metadata_filters"),
                    document_ids=filters.get("document_ids")
                )
            
            # 执行摘要搜索
            search_results = await self.vector_store.search_summaries(
                query_vector=query_vector,
                top_k=top_k,
                score_threshold=0.0,
                filters=search_filter
            )
            
            # 转换为RetrievedDocument格式
            documents = []
            for i, result in enumerate(search_results):
                doc = RetrievedDocument(
                    id=result.document.id,
                    content=result.document.content,
                    score=result.score,
                    source="summary_store",
                    metadata=result.document.metadata,
                    rank=i + 1
                )
                documents.append(doc)
            
            retrieval_time = (time.time() - start_time) * 1000
            logger.debug(f"摘要检索耗时: {retrieval_time:.1f}ms, 结果数: {len(documents)}")
            
            return documents
            
        except Exception as e:
            logger.error(f"摘要检索执行失败: {e}")
            raise RAGPipelineError(f"摘要检索执行失败: {e}")
    
    async def batch_retrieve(
        self, 
        queries: List[str], 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[List[RetrievedDocument]]:
        """批量摘要检索"""
        try:
            tasks = [
                self.retrieve(query, top_k, filters)
                for query in queries
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            batch_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"批量摘要检索第 {i} 个查询失败: {result}")
                    batch_results.append([])
                else:
                    batch_results.append(result)
            
            return batch_results
            
        except Exception as e:
            logger.error(f"批量摘要检索失败: {e}")
            raise RAGPipelineError(f"批量摘要检索失败: {e}")


class HybridRetriever(IRetriever):
    """混合检索器 - 组合多种检索方法"""
    
    def __init__(
        self,
        retrievers: List[IRetriever],
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(config)
        self.retrievers = retrievers
        
        # 配置参数
        self.fusion_method = config.get("fusion_method", "rrf")  # reciprocal rank fusion
        self.rrf_k = config.get("rrf_k", 60)  # RRF参数
        self.weights = config.get("weights", [1.0] * len(retrievers))  # 检索器权重
        
        logger.info(f"HybridRetriever 初始化: {len(retrievers)} 个检索器, 融合方法: {self.fusion_method}")
    
    async def initialize(self) -> None:
        """初始化混合检索器"""
        if self._initialized:
            return
        
        try:
            # 初始化所有子检索器
            for i, retriever in enumerate(self.retrievers):
                if not retriever.is_initialized:
                    await retriever.initialize()
                    logger.info(f"子检索器 {i} 初始化完成: {retriever.component_name}")
            
            self._initialized = True
            logger.info("HybridRetriever 初始化完成")
            
        except Exception as e:
            logger.error(f"HybridRetriever 初始化失败: {e}")
            raise RAGPipelineError(
                f"混合检索器初始化失败: {e}",
                component_type=self.component_type
            )
    
    async def process(self, context: RAGContext) -> RAGContext:
        """处理RAG上下文 - 执行混合检索"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 从上下文获取检索参数
            top_k = context.user_context.get("top_k", 10)
            filters = context.user_context.get("filters")
            
            # 执行混合检索
            documents = await self.retrieve(
                query=context.query,
                top_k=top_k,
                filters=filters
            )
            
            # 更新上下文
            context.retrieved_documents.extend(documents)
            
            # 记录检索元数据
            context.processing_metadata["hybrid_retrieval"] = {
                "documents_found": len(documents),
                "retrievers_used": len(self.retrievers),
                "fusion_method": self.fusion_method,
                "top_k": top_k,
                "avg_score": sum(doc.score for doc in documents) / len(documents) if documents else 0.0
            }
            
            logger.info(f"混合检索完成: 找到 {len(documents)} 个文档")
            
            return context
            
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            raise RAGPipelineError(
                f"混合检索失败: {e}",
                component_type=self.component_type
            )
    
    async def retrieve(
        self, 
        query: str, 
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedDocument]:
        """执行混合检索"""
        try:
            start_time = time.time()
            
            # 并行执行所有检索器
            retrieval_tasks = [
                retriever.retrieve(query, top_k * 2, filters)  # 获取更多候选文档
                for retriever in self.retrievers
            ]
            
            retrieval_results = await asyncio.gather(*retrieval_tasks, return_exceptions=True)
            
            # 收集有效结果
            valid_results = []
            for i, result in enumerate(retrieval_results):
                if isinstance(result, Exception):
                    logger.warning(f"检索器 {i} 失败: {result}")
                    valid_results.append([])
                else:
                    valid_results.append(result)
            
            # 融合结果
            if self.fusion_method == "rrf":
                fused_documents = self._reciprocal_rank_fusion(valid_results, top_k)
            elif self.fusion_method == "weighted":
                fused_documents = self._weighted_fusion(valid_results, top_k)
            else:
                # 简单合并
                fused_documents = self._simple_merge(valid_results, top_k)
            
            retrieval_time = (time.time() - start_time) * 1000
            logger.debug(f"混合检索耗时: {retrieval_time:.1f}ms, 结果数: {len(fused_documents)}")
            
            return fused_documents
            
        except Exception as e:
            logger.error(f"混合检索执行失败: {e}")
            raise RAGPipelineError(f"混合检索执行失败: {e}")
    
    async def batch_retrieve(
        self, 
        queries: List[str], 
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[List[RetrievedDocument]]:
        """批量混合检索"""
        try:
            tasks = [
                self.retrieve(query, top_k, filters)
                for query in queries
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            batch_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"批量混合检索第 {i} 个查询失败: {result}")
                    batch_results.append([])
                else:
                    batch_results.append(result)
            
            return batch_results
            
        except Exception as e:
            logger.error(f"批量混合检索失败: {e}")
            raise RAGPipelineError(f"批量混合检索失败: {e}")
    
    def _reciprocal_rank_fusion(
        self, 
        retrieval_results: List[List[RetrievedDocument]], 
        top_k: int
    ) -> List[RetrievedDocument]:
        """倒数排名融合"""
        document_scores = {}
        
        for retriever_idx, documents in enumerate(retrieval_results):
            weight = self.weights[retriever_idx] if retriever_idx < len(self.weights) else 1.0
            
            for rank, doc in enumerate(documents):
                doc_id = doc.id
                rrf_score = weight / (self.rrf_k + rank + 1)
                
                if doc_id not in document_scores:
                    document_scores[doc_id] = {
                        "document": doc,
                        "score": 0.0,
                        "sources": []
                    }
                
                document_scores[doc_id]["score"] += rrf_score
                document_scores[doc_id]["sources"].append(f"retriever_{retriever_idx}")
        
        # 按分数排序
        sorted_docs = sorted(
            document_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )
        
        # 构建最终结果
        result_documents = []
        for i, doc_info in enumerate(sorted_docs[:top_k]):
            doc = doc_info["document"]
            doc.score = doc_info["score"]
            doc.rank = i + 1
            doc.metadata["fusion_sources"] = doc_info["sources"]
            doc.metadata["fusion_method"] = "rrf"
            result_documents.append(doc)
        
        return result_documents
    
    def _weighted_fusion(
        self, 
        retrieval_results: List[List[RetrievedDocument]], 
        top_k: int
    ) -> List[RetrievedDocument]:
        """加权融合"""
        document_scores = {}
        
        for retriever_idx, documents in enumerate(retrieval_results):
            weight = self.weights[retriever_idx] if retriever_idx < len(self.weights) else 1.0
            
            for doc in documents:
                doc_id = doc.id
                weighted_score = doc.score * weight
                
                if doc_id not in document_scores:
                    document_scores[doc_id] = {
                        "document": doc,
                        "score": 0.0,
                        "count": 0,
                        "sources": []
                    }
                
                document_scores[doc_id]["score"] += weighted_score
                document_scores[doc_id]["count"] += 1
                document_scores[doc_id]["sources"].append(f"retriever_{retriever_idx}")
        
        # 计算平均分数
        for doc_info in document_scores.values():
            doc_info["score"] = doc_info["score"] / doc_info["count"]
        
        # 按分数排序
        sorted_docs = sorted(
            document_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )
        
        # 构建最终结果
        result_documents = []
        for i, doc_info in enumerate(sorted_docs[:top_k]):
            doc = doc_info["document"]
            doc.score = doc_info["score"]
            doc.rank = i + 1
            doc.metadata["fusion_sources"] = doc_info["sources"]
            doc.metadata["fusion_method"] = "weighted"
            result_documents.append(doc)
        
        return result_documents
    
    def _simple_merge(
        self, 
        retrieval_results: List[List[RetrievedDocument]], 
        top_k: int
    ) -> List[RetrievedDocument]:
        """简单合并去重"""
        seen_docs = {}
        all_documents = []
        
        # 合并所有文档
        for retriever_idx, documents in enumerate(retrieval_results):
            for doc in documents:
                if doc.id not in seen_docs:
                    doc.metadata["fusion_sources"] = [f"retriever_{retriever_idx}"]
                    doc.metadata["fusion_method"] = "simple_merge"
                    seen_docs[doc.id] = doc
                    all_documents.append(doc)
                else:
                    # 更新来源信息
                    seen_docs[doc.id].metadata["fusion_sources"].append(f"retriever_{retriever_idx}")
        
        # 按原始分数排序
        all_documents.sort(key=lambda x: x.score, reverse=True)
        
        # 更新排名
        for i, doc in enumerate(all_documents[:top_k]):
            doc.rank = i + 1
        
        return all_documents[:top_k]
