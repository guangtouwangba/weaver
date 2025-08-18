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
        
        # Query cleaning
        processed_query = self._clean_query(processed_query)
        
        # Spell checking
        if self.enable_spell_check:
            processed_query = self._spell_check(processed_query)
        
        # Query expansion
        expanded_terms = []
        if self.enable_query_expansion:
            expanded_terms = self._expand_query(processed_query)
        
        # Intent detection
        query_type = QueryType.CONVERSATIONAL
        if self.enable_intent_detection:
            query_type = self._detect_intent(processed_query)
        
        # Select retrieval strategy
        strategy = self._select_strategy(processed_query, query_type)
        
        return {
            'processed_query': processed_query,
            'expanded_terms': expanded_terms,
            'query_type': query_type,
            'strategy': strategy,
            'metadata': metadata
        }
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize the query."""
        # Remove extra whitespace
        cleaned = ' '.join(query.split())
        # Remove special characters (keep basic punctuation)
        cleaned = re.sub(r'[^\w\s\.\?\!\,\;\:\-\(\)]', '', cleaned)
        return cleaned
    
    def _spell_check(self, query: str) -> str:
        """Check and correct spelling in the query."""
        # Here you can integrate professional spelling check tools
        # For now, return the original query
        return query
    
    def _expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms."""
        # Simple synonym expansion
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
        """Detect query intent."""
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
        """Select retrieval strategy."""
        # Select strategy based on query type and complexity
        complexity = self._get_query_complexity(query)
        
        if query_type in [QueryType.FACTUAL, QueryType.SEARCH] and complexity < 0.3:
            return RetrievalStrategy.SEMANTIC
        elif query_type == QueryType.ANALYTICAL or complexity > 0.5:
            return RetrievalStrategy.HYBRID
        else:
            return RetrievalStrategy.SEMANTIC
    
    def _get_query_complexity(self, query: str) -> float:
        """Evaluate query complexity."""
        factors = []
        
        # Length factor
        length_factor = min(len(query.split()) / 20, 1.0)
        factors.append(length_factor)
        
        # Complex word factor
        complex_words = ['analyze', 'compare', 'synthesize', 'evaluate', 'relationship']
        complex_factor = sum(1 for word in complex_words if word in query.lower()) / len(complex_words)
        factors.append(complex_factor)
        
        # Question mark factor
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
        
        # Reranking
        if self.enable_reranking and len(processed_chunks) > 1:
            processed_chunks = await self._rerank_results(query, processed_chunks)
        
        # Deduplication
        processed_chunks = self._deduplicate_chunks(processed_chunks)
        
        # Compress results
        if self.enable_compression and len(processed_chunks) > self.max_chunks:
            processed_chunks = self._compress_results(processed_chunks)
        
        # Context building
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
            
            # Vocabulary overlap score
            overlap = len(query_words.intersection(chunk_words))
            overlap_score = overlap / len(query_words) if query_words else 0
            
            # Position score (headers and opening paragraphs have higher weight)
            position_score = 1.0  # Simplified implementation
            
            # Length score (moderate length chunks score higher)
            ideal_length = 200
            length_score = 1.0 - abs(len(chunk_content) - ideal_length) / ideal_length
            length_score = max(0.1, length_score)
            
            # Combined score
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
        
        # Sort by new score
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked
    
    def _deduplicate_chunks(self, chunks_with_scores: List[tuple]) -> List[tuple]:
        """去重处理"""
        seen_content = set()
        deduplicated = []
        
        for chunk, score in chunks_with_scores:
            # Use first 100 characters of content as deduplication key
            content_key = chunk.content[:100].strip()
            
            if content_key not in seen_content:
                seen_content.add(content_key)
                deduplicated.append((chunk, score))
        
        return deduplicated
    
    def _compress_results(self, chunks_with_scores: List[tuple]) -> List[tuple]:
        """压缩结果数量"""
        target_count = int(len(chunks_with_scores) * self.compression_ratio)
        target_count = max(target_count, self.max_chunks)
        
        # Keep chunks with highest scores
        sorted_chunks = sorted(chunks_with_scores, key=lambda x: x[1], reverse=True)
        return sorted_chunks[:target_count]
    
    def _build_context(self, chunks_with_scores: List[tuple]) -> Dict[str, Any]:
        """构建上下文信息"""
        if not chunks_with_scores:
            return {}
        
        # Document distribution
        doc_distribution = {}
        for chunk, score in chunks_with_scores:
            doc_id = chunk.document_id
            if doc_id not in doc_distribution:
                doc_distribution[doc_id] = {'count': 0, 'avg_score': 0.0, 'chunks': []}
            doc_distribution[doc_id]['count'] += 1
            doc_distribution[doc_id]['chunks'].append((chunk, score))
        
        # Calculate average score for each document
        for doc_id, info in doc_distribution.items():
            total_score = sum(score for _, score in info['chunks'])
            info['avg_score'] = total_score / info['count']
        
        # Score statistics
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
        
        # Initialize processors
        self.pre_processor = QueryPreProcessor(self.config.get('pre_processor', {}))
        self.post_processor = QueryPostProcessor(self.config.get('post_processor', {}))
        
        # Register available retrieval strategies
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
            # 1. Query preprocessing
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
            # Determine search scope
            document_ids = None
            if filters and filters.document_ids:
                document_ids = filters.document_ids
            
            # Use vector store for semantic search
            chunks_with_scores = await self.vector_store.search_by_text(
                query_text=query,
                top_k=k * 2,  # Get more candidate results for reranking
                document_ids=document_ids
            )
            
            # Apply similarity threshold
            chunks_with_scores = self._apply_similarity_threshold(chunks_with_scores)
            
            # Rerank (if enabled)
            if self.enable_reranking and len(chunks_with_scores) > k:
                chunks_with_scores = await self._rerank_results(query, chunks_with_scores)
            
            # Truncate to specified number
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
        # Here you can implement more complex reranking logic
        # For example, using cross-encoders, BM25 scores, etc.
        
        # Simple reranking based on text matching
        query_words = set(query.lower().split())
        
        def calculate_text_score(chunk_content: str) -> float:
            chunk_words = set(chunk_content.lower().split())
            overlap = len(query_words.intersection(chunk_words))
            return overlap / len(query_words) if query_words else 0
        
        # Combine semantic score and text matching score
        reranked = []
        for chunk, semantic_score in chunks_with_scores:
            text_score = calculate_text_score(chunk.content)
            combined_score = 0.7 * semantic_score + 0.3 * text_score
            reranked.append((chunk, combined_score))
        
        # Sort by combined score
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked


class HybridRetriever(BaseRetriever):
    """混合检索器（语义+关键词）"""
    
    def __init__(self, vector_store, document_repository, config=None):
        super().__init__(vector_store, document_repository, config)
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
            # Determine search scope
            document_ids = None
            if filters and filters.document_ids:
                document_ids = filters.document_ids
            
            # Parallel execution of semantic and keyword search
            import asyncio
            
            semantic_task = self.vector_store.search_by_text(query, k * 2, document_ids)
            keyword_task = self._keyword_search(query, k * 2, document_ids)
            
            semantic_results, keyword_results = await asyncio.gather(
                semantic_task, keyword_task
            )
            
            # Merge and rerank results
            combined_results = self._merge_results(
                semantic_results, keyword_results, query
            )
            
            # Truncate to specified number
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
    
    async def _keyword_search(self, query: str, top_k: int, document_ids) -> List[tuple]:
        """关键词搜索（简单实现）"""
        # Here you can integrate a dedicated keyword search engine like Elasticsearch
        # Currently using simple text matching
        return await self.vector_store.search_by_text(query, top_k, document_ids)
    
    def _merge_results(self, 
                      semantic_results: List[tuple], 
                      keyword_results: List[tuple],
                      query: str) -> List[tuple]:
        """合并语义和关键词检索结果"""
        # Create a result dictionary to avoid duplicates
        chunk_scores = {}
        
        # Add semantic search results
        for chunk, score in semantic_results:
            chunk_scores[chunk.id] = {
                'chunk': chunk,
                'semantic_score': score,
                'keyword_score': 0.0
            }
        
        # Add keyword search results
        for chunk, score in keyword_results:
            if chunk.id in chunk_scores:
                chunk_scores[chunk.id]['keyword_score'] = score
            else:
                chunk_scores[chunk.id] = {
                    'chunk': chunk,
                    'semantic_score': 0.0,
                    'keyword_score': score
                }
        
        # Calculate combined score
        combined_results = []
        for chunk_data in chunk_scores.values():
            combined_score = (
                self.semantic_weight * chunk_data['semantic_score'] +
                self.keyword_weight * chunk_data['keyword_score']
            )
            combined_results.append((chunk_data['chunk'], combined_score))
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x[1], reverse=True)
        return combined_results