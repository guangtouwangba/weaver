"""
检索器基础接口
支持多策略文档检索和重排序
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
import time
from enum import Enum

from ..models import DocumentChunk, QueryResult, SearchFilter
from ..vector_store.base import BaseVectorStore
from ..document_repository.base import BaseDocumentRepository
from .processors import QueryPreProcessor, QueryPostProcessor, RetrievalStrategy




class BaseRetriever(ABC):
    """检索器基类"""
    
    def __init__(self, 
                 vector_store: BaseVectorStore,
                 document_repository: BaseDocumentRepository,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化检索器
        
        Args:
            vector_store: 向量存储实例
            document_repository: 文档仓储实例
            config: 配置参数
        """
        self.vector_store = vector_store
        self.document_repository = document_repository
        self.config = config or {}
        
        self.top_k = self.config.get('top_k', 10)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.7)
        
        # 初始化处理器
        self.pre_processor = QueryPreProcessor(self.config.get('pre_processor', {}))
        self.post_processor = QueryPostProcessor(self.config.get('post_processor', {}))
        
        # 注册可用的检索策略
        self.strategies: Dict[RetrievalStrategy, callable] = {
            RetrievalStrategy.SEMANTIC: self._semantic_retrieve,
            RetrievalStrategy.KEYWORD: self._keyword_retrieve,
            RetrievalStrategy.HYBRID: self._hybrid_retrieve
        }
    
    async def retrieve(self, 
                      query: str, 
                      top_k: Optional[int] = None,
                      filters: Optional[SearchFilter] = None,
                      strategy: Optional[RetrievalStrategy] = None,
                      **kwargs) -> QueryResult:
        """
        执行智能检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量，如果为None则使用默认值
            filters: 搜索过滤器
            strategy: 指定检索策略，如果为None则自动选择
            **kwargs: 其他检索参数
            
        Returns:
            QueryResult: 查询结果对象
        """
        start_time = time.time()
        
        try:
            # 1. 查询预处理
            pre_result = await self.pre_processor.process(query, kwargs.get('context'))
            processed_query = pre_result['processed_query']
            selected_strategy = strategy or pre_result['strategy']
            
            # 2. 执行检索策略
            if selected_strategy not in self.strategies:
                selected_strategy = RetrievalStrategy.SEMANTIC
            
            retrieve_func = self.strategies[selected_strategy]
            chunks_with_scores = await retrieve_func(
                processed_query, 
                top_k or self.top_k, 
                filters,
                **kwargs
            )
            
            # 3. 查询后处理
            post_context = {'chunks_with_scores': chunks_with_scores}
            post_result = await self.post_processor.process(processed_query, post_context)
            final_chunks_with_scores = post_result.get('chunks_with_scores', chunks_with_scores)
            
            query_time = (time.time() - start_time) * 1000
            
            return self._create_query_result(
                query=query,
                chunks_with_scores=final_chunks_with_scores,
                query_time_ms=query_time,
                strategy=selected_strategy.value,
                pre_processing=pre_result,
                post_processing=post_result,
                filters_applied=filters is not None
            )
            
        except Exception as e:
            query_time = (time.time() - start_time) * 1000
            return self._create_query_result(
                query=query,
                chunks_with_scores=[],
                query_time_ms=query_time,
                error=str(e),
                strategy=strategy.value if strategy else 'unknown'
            )
    
    @abstractmethod
    async def _semantic_retrieve(self, query: str, top_k: int, filters: Optional[SearchFilter], **kwargs) -> List[tuple]:
        """语义检索实现"""
        pass
    
    @abstractmethod
    async def _keyword_retrieve(self, query: str, top_k: int, filters: Optional[SearchFilter], **kwargs) -> List[tuple]:
        """关键词检索实现"""
        pass
    
    @abstractmethod
    async def _hybrid_retrieve(self, query: str, top_k: int, filters: Optional[SearchFilter], **kwargs) -> List[tuple]:
        """混合检索实现"""
        pass
    
    async def batch_retrieve(self, 
                            queries: List[str],
                            top_k: Optional[int] = None,
                            filters: Optional[SearchFilter] = None) -> List[QueryResult]:
        """
        批量检索
        
        Args:
            queries: 查询列表
            top_k: 每个查询的返回结果数量
            filters: 搜索过滤器
            
        Returns:
            List[QueryResult]: 查询结果列表
        """
        results = []
        for query in queries:
            result = await self.retrieve(query, top_k, filters)
            results.append(result)
        return results
    
    def _create_query_result(self, 
                           query: str,
                           chunks_with_scores: List[tuple],
                           query_time_ms: float,
                           **metadata) -> QueryResult:
        """
        创建查询结果对象
        
        Args:
            query: 原始查询
            chunks_with_scores: (chunk, score)元组列表
            query_time_ms: 查询耗时
            **metadata: 其他元数据
            
        Returns:
            QueryResult: 查询结果
        """
        chunks = [chunk for chunk, _ in chunks_with_scores]
        scores = [score for _, score in chunks_with_scores]
        
        return QueryResult(
            query=query,
            chunks=chunks,
            relevance_scores=scores,
            total_found=len(chunks),
            query_time_ms=query_time_ms,
            metadata=metadata
        )
    
    def _apply_similarity_threshold(self, 
                                  chunks_with_scores: List[tuple],
                                  threshold: Optional[float] = None) -> List[tuple]:
        """
        应用相似度阈值过滤
        
        Args:
            chunks_with_scores: (chunk, score)元组列表
            threshold: 相似度阈值
            
        Returns:
            List[tuple]: 过滤后的结果
        """
        threshold = threshold or self.similarity_threshold
        return [(chunk, score) for chunk, score in chunks_with_scores if score >= threshold]


