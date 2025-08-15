"""
语义检索器实现
"""

from typing import List, Optional, Dict, Any, tuple
import asyncio

from ..models import SearchFilter
from .base import BaseRetriever
from .processors import RetrievalStrategy


class SemanticRetriever(BaseRetriever):
    """语义检索器"""
    
    async def _semantic_retrieve(self, query: str, top_k: int, filters: Optional[SearchFilter], **kwargs) -> List[tuple]:
        """语义检索实现"""
        # 确定搜索范围
        document_ids = None
        if filters and filters.document_ids:
            document_ids = filters.document_ids
        
        # 使用向量存储进行语义搜索
        chunks_with_scores = await self.vector_store.search_by_text(
            query_text=query,
            top_k=top_k * 2,  # 获取更多候选结果用于后处理
            document_ids=document_ids
        )
        
        # 应用相似度阈值
        return self._apply_similarity_threshold(chunks_with_scores)
    
    async def _keyword_retrieve(self, query: str, top_k: int, filters: Optional[SearchFilter], **kwargs) -> List[tuple]:
        """关键词检索实现（简单文本匹配）"""
        # 确定搜索范围
        document_ids = None
        if filters and filters.document_ids:
            document_ids = filters.document_ids
        
        # 使用向量存储的文本搜索功能
        return await self.vector_store.search_by_text(
            query_text=query,
            top_k=top_k,
            document_ids=document_ids
        )
    
    async def _hybrid_retrieve(self, query: str, top_k: int, filters: Optional[SearchFilter], **kwargs) -> List[tuple]:
        """混合检索实现"""
        # 并行执行语义和关键词检索
        semantic_task = self._semantic_retrieve(query, top_k, filters, **kwargs)
        keyword_task = self._keyword_retrieve(query, top_k, filters, **kwargs)
        
        semantic_results, keyword_results = await asyncio.gather(semantic_task, keyword_task)
        
        # 合并结果
        return self._merge_hybrid_results(semantic_results, keyword_results)
    
    def _merge_hybrid_results(self, semantic_results: List[tuple], keyword_results: List[tuple]) -> List[tuple]:
        """合并混合检索结果"""
        # 创建结果字典，避免重复
        chunk_scores = {}
        semantic_weight = 0.7
        keyword_weight = 0.3
        
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
                semantic_weight * chunk_data['semantic_score'] +
                keyword_weight * chunk_data['keyword_score']
            )
            combined_results.append((chunk_data['chunk'], combined_score))
        
        # 按组合分数排序
        combined_results.sort(key=lambda x: x[1], reverse=True)
        return combined_results