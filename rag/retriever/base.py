"""
检索器基础接口
支持多策略文档检索和重排序
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import time

from ..models import DocumentChunk, QueryResult, SearchFilter
from ..vector_store.base import BaseVectorStore
from ..knowledge_store.base import BaseKnowledgeStore


class BaseRetriever(ABC):
    """检索器基类"""
    
    def __init__(self, 
                 vector_store: BaseVectorStore,
                 knowledge_store: BaseKnowledgeStore,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化检索器
        
        Args:
            vector_store: 向量存储实例
            knowledge_store: 知识存储实例
            config: 配置参数
        """
        self.vector_store = vector_store
        self.knowledge_store = knowledge_store
        self.config = config or {}
        
        self.top_k = self.config.get('top_k', 10)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.7)
        self.enable_reranking = self.config.get('enable_reranking', False)
    
    @abstractmethod
    async def retrieve(self, 
                      query: str, 
                      top_k: Optional[int] = None,
                      filters: Optional[SearchFilter] = None,
                      **kwargs) -> QueryResult:
        """
        执行检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量，如果为None则使用默认值
            filters: 搜索过滤器
            **kwargs: 其他检索参数
            
        Returns:
            QueryResult: 查询结果对象
        """
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


class SemanticRetriever(BaseRetriever):
    """语义检索器"""
    
    async def retrieve(self, 
                      query: str, 
                      top_k: Optional[int] = None,
                      filters: Optional[SearchFilter] = None,
                      **kwargs) -> QueryResult:
        """执行语义检索"""
        start_time = time.time()
        
        k = top_k or self.top_k
        
        try:
            # 使用向量存储进行语义搜索
            chunks_with_scores = await self.vector_store.search_by_text(
                query_text=query,
                top_k=k * 2,  # 获取更多候选结果用于重排序
                filter_criteria=filters
            )
            
            # 应用相似度阈值
            chunks_with_scores = self._apply_similarity_threshold(chunks_with_scores)
            
            # 重排序（如果启用）
            if self.enable_reranking and len(chunks_with_scores) > k:
                chunks_with_scores = await self._rerank_results(query, chunks_with_scores)
            
            # 截取到指定数量
            chunks_with_scores = chunks_with_scores[:k]
            
            query_time = (time.time() - start_time) * 1000
            
            return self._create_query_result(
                query=query,
                chunks_with_scores=chunks_with_scores,
                query_time_ms=query_time,
                retrieval_method="semantic",
                filters_applied=filters is not None
            )
            
        except Exception as e:
            query_time = (time.time() - start_time) * 1000
            return self._create_query_result(
                query=query,
                chunks_with_scores=[],
                query_time_ms=query_time,
                error=str(e),
                retrieval_method="semantic"
            )
    
    async def _rerank_results(self, query: str, chunks_with_scores: List[tuple]) -> List[tuple]:
        """重排序结果（简单实现）"""
        # 这里可以实现更复杂的重排序逻辑
        # 例如使用交叉编码器、BM25分数等
        
        # 简单的基于文本匹配的重排序
        query_words = set(query.lower().split())
        
        def calculate_text_score(chunk_content: str) -> float:
            chunk_words = set(chunk_content.lower().split())
            overlap = len(query_words.intersection(chunk_words))
            return overlap / len(query_words) if query_words else 0
        
        # 结合语义分数和文本匹配分数
        reranked = []
        for chunk, semantic_score in chunks_with_scores:
            text_score = calculate_text_score(chunk.content)
            combined_score = 0.7 * semantic_score + 0.3 * text_score
            reranked.append((chunk, combined_score))
        
        # 按组合分数排序
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked


class HybridRetriever(BaseRetriever):
    """混合检索器（语义+关键词）"""
    
    def __init__(self, vector_store, knowledge_store, config=None):
        super().__init__(vector_store, knowledge_store, config)
        self.semantic_weight = self.config.get('semantic_weight', 0.7)
        self.keyword_weight = self.config.get('keyword_weight', 0.3)
    
    async def retrieve(self, 
                      query: str, 
                      top_k: Optional[int] = None,
                      filters: Optional[SearchFilter] = None,
                      **kwargs) -> QueryResult:
        """执行混合检索"""
        start_time = time.time()
        
        k = top_k or self.top_k
        
        try:
            # 并行执行语义检索和关键词检索
            import asyncio
            
            semantic_task = self.vector_store.search_by_text(query, k * 2, filters)
            keyword_task = self._keyword_search(query, k * 2, filters)
            
            semantic_results, keyword_results = await asyncio.gather(
                semantic_task, keyword_task
            )
            
            # 合并和重排序结果
            combined_results = self._merge_results(
                semantic_results, keyword_results, query
            )
            
            # 截取到指定数量
            combined_results = combined_results[:k]
            
            query_time = (time.time() - start_time) * 1000
            
            return self._create_query_result(
                query=query,
                chunks_with_scores=combined_results,
                query_time_ms=query_time,
                retrieval_method="hybrid",
                semantic_weight=self.semantic_weight,
                keyword_weight=self.keyword_weight
            )
            
        except Exception as e:
            query_time = (time.time() - start_time) * 1000
            return self._create_query_result(
                query=query,
                chunks_with_scores=[],
                query_time_ms=query_time,
                error=str(e),
                retrieval_method="hybrid"
            )
    
    async def _keyword_search(self, query: str, top_k: int, filters) -> List[tuple]:
        """关键词搜索（简单实现）"""
        # 这里可以集成专门的关键词搜索引擎如Elasticsearch
        # 目前使用简单的文本匹配
        return await self.vector_store.search_by_text(query, top_k, filters)
    
    def _merge_results(self, 
                      semantic_results: List[tuple], 
                      keyword_results: List[tuple],
                      query: str) -> List[tuple]:
        """合并语义和关键词检索结果"""
        # 创建结果字典，避免重复
        chunk_scores = {}
        
        # 添加语义检索结果
        for chunk, score in semantic_results:
            chunk_scores[chunk.id] = {
                'chunk': chunk,
                'semantic_score': score,
                'keyword_score': 0.0
            }
        
        # 添加关键词检索结果
        for chunk, score in keyword_results:
            if chunk.id in chunk_scores:
                chunk_scores[chunk.id]['keyword_score'] = score
            else:
                chunk_scores[chunk.id] = {
                    'chunk': chunk,
                    'semantic_score': 0.0,
                    'keyword_score': score
                }
        
        # 计算组合分数
        combined_results = []
        for chunk_data in chunk_scores.values():
            combined_score = (
                self.semantic_weight * chunk_data['semantic_score'] +
                self.keyword_weight * chunk_data['keyword_score']
            )
            combined_results.append((chunk_data['chunk'], combined_score))
        
        # 按组合分数排序
        combined_results.sort(key=lambda x: x[1], reverse=True)
        return combined_results