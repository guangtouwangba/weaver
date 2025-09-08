"""
增强RAG处理器

集成新的模块化RAG组件，提供更强大的文档处理能力。
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .rag_processor import RAGProcessor, RAGProcessorConfig, RAGProcessingResult, RAGProcessingError
from modules.schemas import Document, DocumentChunk
from modules.schemas.enums import ContentType, ProcessingStatus
from modules.rag.base import RetrievedDocument
from modules.rag.bm25_retriever import BM25Retriever
from modules.rag.factory import RAGComponentFactory

logger = logging.getLogger(__name__)


class EnhancedRAGProcessorConfig(RAGProcessorConfig):
    """增强RAG处理器配置"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 新增配置
        self.enable_bm25_indexing = kwargs.get("enable_bm25_indexing", True)
        self.enable_hybrid_retrieval = kwargs.get("enable_hybrid_retrieval", True)
        self.enable_reranking = kwargs.get("enable_reranking", True)
        self.reranker_type = kwargs.get("reranker_type", "score_based")
        
        # BM25配置
        self.bm25_config = kwargs.get("bm25_config", {
            "k1": 1.5,
            "b": 0.75,
            "min_word_length": 2,
            "max_word_length": 20
        })
        
        # 重排序配置
        self.reranker_config = kwargs.get("reranker_config", {
            "score_weights": {
                "vector_score": 0.7,
                "bm25_score": 0.3
            },
            "diversity_factor": 0.1,
            "enable_diversity": True
        })


class EnhancedRAGProcessor(RAGProcessor):
    """增强RAG处理器 - 集成新的模块化组件"""
    
    def __init__(
        self,
        config: Optional[EnhancedRAGProcessorConfig] = None,
        embedding_service = None,
        vector_store = None,
    ):
        # 使用增强配置
        if config is None:
            config = EnhancedRAGProcessorConfig()
        
        super().__init__(config, embedding_service, vector_store)
        
        # 新组件
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.reranker = None
        
        # 增强配置
        self.enhanced_config = config
        
        logger.info("EnhancedRAGProcessor 初始化完成")
    
    async def initialize(self) -> None:
        """初始化增强RAG处理器"""
        # 调用父类初始化
        await super().initialize()
        
        try:
            # 初始化BM25检索器
            if self.enhanced_config.enable_bm25_indexing:
                await self._initialize_bm25_retriever()
            
            # 初始化重排序器
            if self.enhanced_config.enable_reranking:
                await self._initialize_reranker()
            
            logger.info("EnhancedRAGProcessor 增强组件初始化完成")
            
        except Exception as e:
            logger.error(f"增强组件初始化失败: {e}")
            raise RAGProcessingError(f"增强组件初始化失败: {e}", stage="initialization")
    
    async def _initialize_bm25_retriever(self) -> None:
        """初始化BM25检索器"""
        try:
            self.bm25_retriever = RAGComponentFactory.create_bm25_retriever(
                "memory", 
                config=self.enhanced_config.bm25_config
            )
            await self.bm25_retriever.initialize()
            
            logger.info("BM25检索器初始化完成")
            
        except Exception as e:
            logger.error(f"BM25检索器初始化失败: {e}")
            raise
    
    async def _initialize_reranker(self) -> None:
        """初始化重排序器"""
        try:
            self.reranker = RAGComponentFactory.create_reranker(
                self.enhanced_config.reranker_type,
                self.enhanced_config.reranker_config
            )
            await self.reranker.initialize()
            
            logger.info(f"重排序器初始化完成: {self.enhanced_config.reranker_type}")
            
        except Exception as e:
            logger.error(f"重排序器初始化失败: {e}")
            # 重排序器失败不影响主流程
            self.reranker = None
            logger.warning("重排序器初始化失败，将跳过重排序步骤")
    
    async def process_document(
        self,
        document: Document,
        chunking_config: Optional[Dict[str, Any]] = None,
        topic_id: Optional[str] = None,
        file_id: Optional[str] = None,
    ) -> RAGProcessingResult:
        """
        处理单个文档的完整RAG流程 - 增强版本
        """
        start_time = time.time()
        
        # 确保初始化
        await self.initialize()
        
        try:
            # 调用父类的文档处理
            result = await super().process_document(
                document, chunking_config, topic_id, file_id
            )
            
            # 如果基础处理失败，直接返回
            if result.status != ProcessingStatus.COMPLETED:
                return result
            
            # 增强处理：添加到BM25索引
            if self.bm25_retriever and result.chunks_created > 0:
                await self._add_to_bm25_index(document, result)
            
            # 更新结果信息
            result.stage_details["enhanced_processing"] = {
                "bm25_indexed": self.bm25_retriever is not None,
                "reranker_available": self.reranker is not None,
                "hybrid_retrieval_enabled": self.enhanced_config.enable_hybrid_retrieval
            }
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            
            logger.info(f"增强RAG处理完成: 文档 {document.id}, 耗时 {processing_time:.1f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"增强RAG处理失败: {e}")
            return RAGProcessingResult(
                document_id=document.id,
                status=ProcessingStatus.FAILED,
                processing_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )
    
    async def _add_to_bm25_index(self, document: Document, result: RAGProcessingResult) -> None:
        """将文档添加到BM25索引"""
        try:
            # 从处理结果重建文档块
            # 这里需要从向量存储或其他地方获取文档块
            # 简化实现：直接使用文档内容
            
            retrieved_doc = RetrievedDocument(
                id=document.id,
                content=document.content,
                score=0.0,
                source="document_processor",
                metadata={
                    "title": document.title,
                    "content_type": document.content_type.value if hasattr(document.content_type, 'value') else str(document.content_type),
                    "topic_id": result.stage_details.get("topic_id"),
                    "file_id": result.stage_details.get("file_id"),
                    "chunks_created": result.chunks_created
                }
            )
            
            await self.bm25_retriever.add_document(retrieved_doc)
            
            logger.debug(f"文档 {document.id} 已添加到BM25索引")
            
        except Exception as e:
            logger.warning(f"添加文档到BM25索引失败: {e}")
    
    async def search_documents(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.0,
        use_hybrid: bool = None,
        use_reranking: bool = None
    ) -> List[RetrievedDocument]:
        """
        搜索文档 - 支持混合检索和重排序
        """
        try:
            # 确保初始化
            await self.initialize()
            
            # 决定是否使用混合检索
            if use_hybrid is None:
                use_hybrid = self.enhanced_config.enable_hybrid_retrieval and self.bm25_retriever is not None
            
            # 决定是否使用重排序
            if use_reranking is None:
                use_reranking = self.enhanced_config.enable_reranking and self.reranker is not None
            
            documents = []
            
            if use_hybrid and self.bm25_retriever:
                # 混合检索：向量 + BM25
                documents = await self._hybrid_search(query, top_k * 2, score_threshold)
            else:
                # 仅向量检索
                documents = await self._vector_search(query, top_k, score_threshold)
            
            # 重排序
            if use_reranking and self.reranker and documents:
                documents = await self.reranker.rerank(query, documents, top_k)
            else:
                # 限制结果数量
                documents = documents[:top_k]
            
            logger.info(f"文档搜索完成: 查询='{query[:50]}...', "
                       f"结果数={len(documents)}, 混合检索={use_hybrid}, 重排序={use_reranking}")
            
            return documents
            
        except Exception as e:
            logger.error(f"文档搜索失败: {e}")
            return []
    
    async def _vector_search(
        self, 
        query: str, 
        top_k: int, 
        score_threshold: float
    ) -> List[RetrievedDocument]:
        """向量检索"""
        try:
            if not self.embedding_service or not self.vector_store:
                return []
            
            # 生成查询向量
            query_vector = await self.embedding_service.generate_embedding(query)
            
            # 执行向量搜索
            search_results = await self.vector_store.search_similar(
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                collection_name=self.config.collection_name
            )
            
            # 转换为RetrievedDocument格式
            documents = []
            for result in search_results:
                doc = RetrievedDocument(
                    id=result.document.id,
                    content=result.document.content,
                    score=result.score,
                    source="vector_search",
                    metadata=result.document.metadata,
                    rank=len(documents) + 1
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []
    
    async def _hybrid_search(
        self, 
        query: str, 
        top_k: int, 
        score_threshold: float
    ) -> List[RetrievedDocument]:
        """混合检索：向量 + BM25"""
        try:
            # 并行执行向量检索和BM25检索
            vector_task = self._vector_search(query, top_k, score_threshold)
            bm25_task = self.bm25_retriever.retrieve(query, top_k)
            
            vector_results, bm25_results = await asyncio.gather(
                vector_task, bm25_task, return_exceptions=True
            )
            
            # 处理异常
            if isinstance(vector_results, Exception):
                logger.warning(f"向量检索失败: {vector_results}")
                vector_results = []
            
            if isinstance(bm25_results, Exception):
                logger.warning(f"BM25检索失败: {bm25_results}")
                bm25_results = []
            
            # 融合结果（使用倒数排名融合）
            fused_documents = self._reciprocal_rank_fusion(
                [vector_results, bm25_results], 
                top_k
            )
            
            return fused_documents
            
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            # 回退到向量检索
            return await self._vector_search(query, top_k, score_threshold)
    
    def _reciprocal_rank_fusion(
        self, 
        retrieval_results: List[List[RetrievedDocument]], 
        top_k: int,
        k: int = 60
    ) -> List[RetrievedDocument]:
        """倒数排名融合"""
        document_scores = {}
        
        for retriever_idx, documents in enumerate(retrieval_results):
            weight = 0.7 if retriever_idx == 0 else 0.3  # 向量检索权重更高
            
            for rank, doc in enumerate(documents):
                doc_id = doc.id
                rrf_score = weight / (k + rank + 1)
                
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
            doc.source = "hybrid_search"
            result_documents.append(doc)
        
        return result_documents
    
    async def get_bm25_stats(self) -> Dict[str, Any]:
        """获取BM25索引统计信息"""
        if not self.bm25_retriever:
            return {"enabled": False}
        
        try:
            stats = await self.bm25_retriever.get_index_stats()
            stats["enabled"] = True
            return stats
        except Exception as e:
            logger.warning(f"获取BM25统计失败: {e}")
            return {"enabled": True, "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        # 调用父类健康检查
        health = await super().health_check()
        
        # 添加增强组件状态
        health["enhanced_components"] = {
            "bm25_retriever": {
                "enabled": self.enhanced_config.enable_bm25_indexing,
                "initialized": self.bm25_retriever is not None
            },
            "reranker": {
                "enabled": self.enhanced_config.enable_reranking,
                "initialized": self.reranker is not None,
                "type": self.enhanced_config.reranker_type
            },
            "hybrid_retrieval": {
                "enabled": self.enhanced_config.enable_hybrid_retrieval
            }
        }
        
        # BM25检索器健康检查
        if self.bm25_retriever:
            try:
                bm25_stats = await self.get_bm25_stats()
                health["enhanced_components"]["bm25_retriever"]["stats"] = bm25_stats
            except Exception as e:
                health["enhanced_components"]["bm25_retriever"]["error"] = str(e)
        
        return health


# 工厂函数
def create_enhanced_rag_processor(
    embedding_service = None,
    vector_store = None,
    config: Optional[Dict[str, Any]] = None
) -> EnhancedRAGProcessor:
    """创建增强RAG处理器"""
    
    # 构建配置
    processor_config = EnhancedRAGProcessorConfig(**(config or {}))
    
    return EnhancedRAGProcessor(
        config=processor_config,
        embedding_service=embedding_service,
        vector_store=vector_store
    )
