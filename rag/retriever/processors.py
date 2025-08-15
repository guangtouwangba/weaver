"""
查询处理器模块
包含查询预处理和后处理功能
"""

import re
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from enum import Enum

from ..models import DocumentChunk


class QueryType(Enum):
    """查询类型枚举"""
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    CONVERSATIONAL = "conversational"
    SEARCH = "search"


class RetrievalStrategy(Enum):
    """检索策略枚举"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    KNOWLEDGE_GRAPH = "knowledge_graph"


class BaseQueryProcessor(ABC):
    """查询处理器基类"""
    
    @abstractmethod
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理查询"""
        pass


class QueryPreProcessor(BaseQueryProcessor):
    """查询预处理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enable_spell_check = self.config.get('enable_spell_check', False)
        self.enable_query_expansion = self.config.get('enable_query_expansion', True)
        self.enable_intent_detection = self.config.get('enable_intent_detection', True)
    
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """预处理查询"""
        processed_query = query.strip()
        metadata = {'original_query': query}
        
        # 查询清理
        processed_query = self._clean_query(processed_query)
        
        # 拼写检查
        if self.enable_spell_check:
            processed_query = self._spell_check(processed_query)
        
        # 查询扩展
        expanded_terms = []
        if self.enable_query_expansion:
            expanded_terms = self._expand_query(processed_query)
        
        # 意图检测
        query_type = QueryType.CONVERSATIONAL
        if self.enable_intent_detection:
            query_type = self._detect_intent(processed_query)
        
        # 选择检索策略
        strategy = self._select_strategy(processed_query, query_type)
        
        return {
            'processed_query': processed_query,
            'expanded_terms': expanded_terms,
            'query_type': query_type,
            'strategy': strategy,
            'metadata': metadata
        }
    
    def _clean_query(self, query: str) -> str:
        """清理查询文本"""
        # 移除多余空格
        query = ' '.join(query.split())
        # 移除特殊字符（保留基本标点）
        query = re.sub(r'[^\w\s\?\!\.,;:-]', '', query)
        return query
    
    def _spell_check(self, query: str) -> str:
        """拼写检查（简单实现）"""
        # 这里可以集成专业的拼写检查工具
        # 暂时返回原查询
        return query
    
    def _expand_query(self, query: str) -> List[str]:
        """查询扩展"""
        # 简单的同义词扩展
        synonyms_map = {
            'AI': ['artificial intelligence', 'machine learning', 'deep learning'],
            'ML': ['machine learning', 'artificial intelligence'],
            'NLP': ['natural language processing', 'text processing'],
        }
        
        expanded = []
        words = query.split()
        for word in words:
            if word.upper() in synonyms_map:
                expanded.extend(synonyms_map[word.upper()])
        
        return expanded
    
    def _detect_intent(self, query: str) -> QueryType:
        """检测查询意图"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['what', 'who', 'when', 'where', 'how many']):
            return QueryType.FACTUAL
        elif any(word in query_lower for word in ['why', 'how', 'analyze', 'compare', 'explain']):
            return QueryType.ANALYTICAL
        elif any(word in query_lower for word in ['create', 'generate', 'write', 'make']):
            return QueryType.CREATIVE
        elif any(word in query_lower for word in ['find', 'search', 'look for']):
            return QueryType.SEARCH
        else:
            return QueryType.CONVERSATIONAL
    
    def _select_strategy(self, query: str, query_type: QueryType) -> RetrievalStrategy:
        """选择检索策略"""
        # 根据查询类型和复杂度选择策略
        complexity = self._get_query_complexity(query)
        
        if query_type in [QueryType.FACTUAL, QueryType.SEARCH] and complexity < 0.3:
            return RetrievalStrategy.SEMANTIC
        elif query_type == QueryType.ANALYTICAL or complexity > 0.5:
            return RetrievalStrategy.HYBRID
        else:
            return RetrievalStrategy.SEMANTIC
    
    def _get_query_complexity(self, query: str) -> float:
        """评估查询复杂度"""
        factors = []
        
        # 长度因子
        length_factor = min(len(query.split()) / 20, 1.0)
        factors.append(length_factor)
        
        # 复杂词汇因子
        complex_words = ['analyze', 'compare', 'synthesize', 'evaluate', 'relationship']
        complex_factor = sum(1 for word in complex_words if word in query.lower()) / len(complex_words)
        factors.append(complex_factor)
        
        # 问号数量
        question_factor = min(query.count('?') / 3, 1.0)
        factors.append(question_factor)
        
        return sum(factors) / len(factors)


class QueryPostProcessor(BaseQueryProcessor):
    """查询后处理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enable_reranking = self.config.get('enable_reranking', True)
        self.enable_compression = self.config.get('enable_compression', True)
        self.max_chunks = self.config.get('max_chunks', 10)
        self.compression_ratio = self.config.get('compression_ratio', 0.7)
    
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """后处理查询结果"""
        if not context or 'chunks_with_scores' not in context:
            return context or {}
        
        chunks_with_scores = context['chunks_with_scores']
        processed_chunks = chunks_with_scores.copy()
        
        # 重排序
        if self.enable_reranking and len(processed_chunks) > 1:
            processed_chunks = await self._rerank_results(query, processed_chunks)
        
        # 去重
        processed_chunks = self._deduplicate_chunks(processed_chunks)
        
        # 压缩结果
        if self.enable_compression and len(processed_chunks) > self.max_chunks:
            processed_chunks = self._compress_results(processed_chunks)
        
        # 上下文构建
        context_info = self._build_context(processed_chunks)
        
        return {
            'chunks_with_scores': processed_chunks,
            'context_info': context_info,
            'total_compressed': len(chunks_with_scores) - len(processed_chunks),
            'reranked': self.enable_reranking,
            'compressed': self.enable_compression
        }
    
    async def _rerank_results(self, query: str, chunks_with_scores: List[tuple]) -> List[tuple]:
        """重排序结果"""
        query_words = set(query.lower().split())
        
        def calculate_relevance_score(chunk_content: str, semantic_score: float) -> float:
            chunk_words = set(chunk_content.lower().split())
            
            # 词汇重叠分数
            overlap = len(query_words.intersection(chunk_words))
            overlap_score = overlap / len(query_words) if query_words else 0
            
            # 位置分数（标题、开头段落权重更高）
            position_score = 1.0  # 简化实现
            
            # 长度分数（适中长度的块得分更高）
            ideal_length = 200
            length_score = 1.0 - abs(len(chunk_content) - ideal_length) / ideal_length
            length_score = max(0.1, length_score)
            
            # 组合分数
            combined_score = (
                0.5 * semantic_score +
                0.3 * overlap_score +
                0.1 * position_score +
                0.1 * length_score
            )
            
            return combined_score
        
        reranked = []
        for chunk, semantic_score in chunks_with_scores:
            new_score = calculate_relevance_score(chunk.content, semantic_score)
            reranked.append((chunk, new_score))
        
        # 按新分数排序
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked
    
    def _deduplicate_chunks(self, chunks_with_scores: List[tuple]) -> List[tuple]:
        """去重处理"""
        seen_content = set()
        deduplicated = []
        
        for chunk, score in chunks_with_scores:
            # 使用内容的前100个字符作为去重键
            content_key = chunk.content[:100].strip()
            
            if content_key not in seen_content:
                seen_content.add(content_key)
                deduplicated.append((chunk, score))
        
        return deduplicated
    
    def _compress_results(self, chunks_with_scores: List[tuple]) -> List[tuple]:
        """压缩结果数量"""
        target_count = int(len(chunks_with_scores) * self.compression_ratio)
        target_count = max(target_count, self.max_chunks)
        
        # 保留分数最高的块
        sorted_chunks = sorted(chunks_with_scores, key=lambda x: x[1], reverse=True)
        return sorted_chunks[:target_count]
    
    def _build_context(self, chunks_with_scores: List[tuple]) -> Dict[str, Any]:
        """构建上下文信息"""
        if not chunks_with_scores:
            return {}
        
        # 文档分布
        doc_distribution = {}
        for chunk, score in chunks_with_scores:
            doc_id = chunk.document_id
            if doc_id not in doc_distribution:
                doc_distribution[doc_id] = {'count': 0, 'avg_score': 0.0, 'chunks': []}
            doc_distribution[doc_id]['count'] += 1
            doc_distribution[doc_id]['chunks'].append((chunk, score))
        
        # 计算每个文档的平均分数
        for doc_id, info in doc_distribution.items():
            total_score = sum(score for _, score in info['chunks'])
            info['avg_score'] = total_score / info['count']
        
        # 分数统计
        scores = [score for _, score in chunks_with_scores]
        score_stats = {
            'min': min(scores),
            'max': max(scores),
            'avg': sum(scores) / len(scores),
            'count': len(scores)
        }
        
        return {
            'document_distribution': doc_distribution,
            'score_statistics': score_stats,
            'total_chunks': len(chunks_with_scores)
        }