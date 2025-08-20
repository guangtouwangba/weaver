"""
Advanced Multi-Strategy Retrieval System

Implements sophisticated retrieval strategies including semantic search,
keyword search, hybrid search, and cross-encoder re-ranking.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import numpy as np
import json
from datetime import datetime
import math
from collections import defaultdict, Counter

from .vector_store import VectorStoreManager, SearchResult as VectorSearchResult
from .embedding import EmbeddingManager, EmbeddingResult

logger = logging.getLogger(__name__)

class RetrievalStrategy(str, Enum):
    """Retrieval strategy types"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    GRAPH = "graph"

class RankingAlgorithm(str, Enum):
    """Ranking algorithm types"""
    COSINE_SIMILARITY = "cosine"
    BM25 = "bm25"
    RRF = "rrf"  # Reciprocal Rank Fusion
    CROSS_ENCODER = "cross_encoder"

@dataclass
class RetrievalResult:
    """Enhanced retrieval result"""
    id: str
    content: str
    score: float
    document_id: str
    topic_id: int
    chunk_index: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    source_strategy: Optional[str] = None
    ranking_features: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class QueryAnalysis:
    """Query analysis result"""
    original_query: str
    processed_query: str
    query_type: str
    language: str
    complexity: float
    entities: List[str]
    keywords: List[str]
    intent: str
    best_strategy: RetrievalStrategy

@dataclass 
class RetrievalConfig:
    """Retrieval configuration"""
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    max_results: int = 10
    semantic_weight: float = 0.6
    keyword_weight: float = 0.4
    enable_reranking: bool = True
    diversity_lambda: float = 0.5
    min_score_threshold: float = 0.3

class IRetriever(ABC):
    """Abstract retriever interface"""
    
    @abstractmethod
    async def retrieve(self, query: str, topic_id: int, 
                      limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """Retrieve relevant documents"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get retriever name"""
        pass

class SemanticRetriever(IRetriever):
    """Semantic similarity retriever"""
    
    def __init__(self, vector_store: VectorStoreManager, 
                 embedding_manager: EmbeddingManager):
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager
    
    async def retrieve(self, query: str, topic_id: int,
                      limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """Perform semantic retrieval"""
        try:
            # Generate query embedding
            query_embedding_result = await self.embedding_manager.get_or_create_embedding(query)
            query_vector = query_embedding_result.embedding
            
            # Search in vector store
            vector_results = await self.vector_store.search_topic(
                topic_id=topic_id,
                query_vector=query_vector,
                limit=limit,
                filters=filters
            )
            
            # Convert to RetrievalResult format
            results = []
            for vr in vector_results:
                result = RetrievalResult(
                    id=vr.id,
                    content=vr.content,
                    score=vr.score,
                    document_id=vr.document_id or "",
                    topic_id=vr.topic_id or topic_id,
                    metadata=vr.metadata,
                    source_strategy="semantic",
                    ranking_features={
                        "cosine_similarity": vr.score,
                        "query_model": query_embedding_result.model_used,
                        "query_language": query_embedding_result.language
                    }
                )
                results.append(result)
            
            logger.info(f"Semantic retrieval returned {len(results)} results for topic {topic_id}")
            return results
            
        except Exception as e:
            logger.error(f"Semantic retrieval failed: {e}")
            return []
    
    def get_name(self) -> str:
        return "semantic"

class KeywordRetriever(IRetriever):
    """BM25-based keyword retriever"""
    
    def __init__(self, corpus_manager: 'CorpusManager'):
        self.corpus_manager = corpus_manager
        self.k1 = 1.5  # BM25 k1 parameter
        self.b = 0.75  # BM25 b parameter
    
    async def retrieve(self, query: str, topic_id: int,
                      limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """Perform BM25 keyword retrieval"""
        try:
            # Get topic corpus
            corpus = await self.corpus_manager.get_topic_corpus(topic_id)
            
            if not corpus:
                logger.warning(f"No corpus found for topic {topic_id}")
                return []
            
            # Tokenize query
            query_terms = self._tokenize(query.lower())
            
            # Calculate BM25 scores
            scores = self._calculate_bm25_scores(query_terms, corpus)
            
            # Sort and limit results
            scored_docs = [(doc_id, score) for doc_id, score in scores.items() if score > 0]
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            scored_docs = scored_docs[:limit]
            
            # Build results
            results = []
            for doc_id, score in scored_docs:
                doc_info = corpus["documents"][doc_id]
                
                result = RetrievalResult(
                    id=doc_id,
                    content=doc_info["content"],
                    score=score,
                    document_id=doc_info["document_id"],
                    topic_id=topic_id,
                    chunk_index=doc_info.get("chunk_index"),
                    metadata=doc_info.get("metadata", {}),
                    source_strategy="keyword",
                    ranking_features={
                        "bm25_score": score,
                        "term_matches": len([t for t in query_terms if t in doc_info["tokens"]]),
                        "doc_length": len(doc_info["tokens"])
                    }
                )
                results.append(result)
            
            logger.info(f"Keyword retrieval returned {len(results)} results for topic {topic_id}")
            return results
            
        except Exception as e:
            logger.error(f"Keyword retrieval failed: {e}")
            return []
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        import re
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def _calculate_bm25_scores(self, query_terms: List[str], 
                             corpus: Dict[str, Any]) -> Dict[str, float]:
        """Calculate BM25 scores for all documents"""
        scores = defaultdict(float)
        
        N = len(corpus["documents"])  # Total number of documents
        avgdl = corpus["stats"]["avg_doc_length"]  # Average document length
        
        for term in query_terms:
            if term not in corpus["term_frequencies"]:
                continue
            
            df = len(corpus["term_frequencies"][term])  # Document frequency
            idf = math.log((N - df + 0.5) / (df + 0.5))
            
            for doc_id, tf in corpus["term_frequencies"][term].items():
                doc_length = len(corpus["documents"][doc_id]["tokens"])
                
                # BM25 formula
                score = idf * (tf * (self.k1 + 1)) / (
                    tf + self.k1 * (1 - self.b + self.b * (doc_length / avgdl))
                )
                scores[doc_id] += score
        
        return scores
    
    def get_name(self) -> str:
        return "keyword"

class HybridRetriever(IRetriever):
    """Hybrid retriever combining semantic and keyword search"""
    
    def __init__(self, semantic_retriever: SemanticRetriever,
                 keyword_retriever: KeywordRetriever,
                 semantic_weight: float = 0.6,
                 keyword_weight: float = 0.4):
        self.semantic_retriever = semantic_retriever
        self.keyword_retriever = keyword_retriever
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
    
    async def retrieve(self, query: str, topic_id: int,
                      limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """Perform hybrid retrieval with score fusion"""
        try:
            # Run both retrievers in parallel
            semantic_task = self.semantic_retriever.retrieve(
                query, topic_id, limit * 2, filters
            )
            keyword_task = self.keyword_retriever.retrieve(
                query, topic_id, limit * 2, filters
            )
            
            semantic_results, keyword_results = await asyncio.gather(
                semantic_task, keyword_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(semantic_results, Exception):
                logger.error(f"Semantic retrieval failed: {semantic_results}")
                semantic_results = []
            if isinstance(keyword_results, Exception):
                logger.error(f"Keyword retrieval failed: {keyword_results}")
                keyword_results = []
            
            # Fuse results using Reciprocal Rank Fusion (RRF)
            fused_results = self._reciprocal_rank_fusion(
                semantic_results, keyword_results, limit
            )
            
            logger.info(f"Hybrid retrieval returned {len(fused_results)} results for topic {topic_id}")
            return fused_results
            
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}")
            return []
    
    def _reciprocal_rank_fusion(self, semantic_results: List[RetrievalResult],
                              keyword_results: List[RetrievalResult],
                              limit: int, k: int = 60) -> List[RetrievalResult]:
        """Reciprocal Rank Fusion algorithm"""
        # Create document score mapping
        doc_scores = defaultdict(float)
        doc_info = {}
        
        # Process semantic results
        for rank, result in enumerate(semantic_results):
            rrf_score = self.semantic_weight / (k + rank + 1)
            doc_scores[result.id] += rrf_score
            
            if result.id not in doc_info:
                doc_info[result.id] = result
                # Update ranking features
                if not result.ranking_features:
                    result.ranking_features = {}
                result.ranking_features["semantic_rank"] = rank + 1
                result.ranking_features["semantic_rrf"] = rrf_score
        
        # Process keyword results
        for rank, result in enumerate(keyword_results):
            rrf_score = self.keyword_weight / (k + rank + 1)
            doc_scores[result.id] += rrf_score
            
            if result.id not in doc_info:
                doc_info[result.id] = result
            
            # Update ranking features
            if not result.ranking_features:
                result.ranking_features = {}
            result.ranking_features["keyword_rank"] = rank + 1
            result.ranking_features["keyword_rrf"] = rrf_score
        
        # Sort by fused score and build results
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        fused_results = []
        for doc_id, fused_score in sorted_docs:
            result = doc_info[doc_id]
            result.score = fused_score
            result.source_strategy = "hybrid"
            
            if not result.ranking_features:
                result.ranking_features = {}
            result.ranking_features["hybrid_score"] = fused_score
            
            fused_results.append(result)
        
        return fused_results
    
    def get_name(self) -> str:
        return "hybrid"

class CrossEncoderReranker:
    """Cross-encoder based re-ranking"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize cross-encoder model"""
        try:
            from sentence_transformers import CrossEncoder
            
            self.model = CrossEncoder(self.model_name)
            self._initialized = True
            
            logger.info(f"Cross-encoder {self.model_name} initialized")
            
        except ImportError:
            raise ImportError("sentence-transformers package required for CrossEncoderReranker")
        except Exception as e:
            logger.error(f"Failed to initialize cross-encoder: {e}")
            raise
    
    async def rerank(self, query: str, results: List[RetrievalResult],
                    top_k: Optional[int] = None) -> List[RetrievalResult]:
        """Re-rank results using cross-encoder"""
        if not self._initialized:
            await self.initialize()
        
        if not results:
            return results
        
        try:
            # Prepare query-document pairs
            pairs = [(query, result.content) for result in results]
            
            # Get cross-encoder scores
            scores = self.model.predict(pairs)
            
            # Update results with new scores
            reranked_results = []
            for result, score in zip(results, scores):
                # Create new result with updated score
                new_result = RetrievalResult(
                    id=result.id,
                    content=result.content,
                    score=float(score),
                    document_id=result.document_id,
                    topic_id=result.topic_id,
                    chunk_index=result.chunk_index,
                    metadata=result.metadata,
                    source_strategy=result.source_strategy,
                    ranking_features={
                        **(result.ranking_features or {}),
                        "cross_encoder_score": float(score),
                        "original_score": result.score
                    }
                )
                reranked_results.append(new_result)
            
            # Sort by cross-encoder score
            reranked_results.sort(key=lambda x: x.score, reverse=True)
            
            # Limit results if specified
            if top_k:
                reranked_results = reranked_results[:top_k]
            
            logger.info(f"Re-ranked {len(results)} results using cross-encoder")
            return reranked_results
            
        except Exception as e:
            logger.error(f"Cross-encoder re-ranking failed: {e}")
            return results  # Return original results on failure

class QueryProcessor:
    """Advanced query processing and analysis"""
    
    def __init__(self):
        self.stopwords = set([
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
            "是", "的", "了", "在", "有", "和", "或", "但是", "因为", "所以", "这个", "那个", "什么", "怎么"
        ])
    
    async def analyze_query(self, query: str, topic_context: Optional[Dict[str, Any]] = None) -> QueryAnalysis:
        """Comprehensive query analysis"""
        try:
            # Basic processing
            processed_query = self._preprocess_query(query)
            language = self._detect_language(query)
            query_type = self._classify_query_type(query)
            complexity = self._calculate_complexity(query)
            
            # Extract entities and keywords
            entities = self._extract_entities(query)
            keywords = self._extract_keywords(query)
            
            # Determine intent
            intent = self._classify_intent(query, query_type)
            
            # Select best strategy
            best_strategy = self._select_strategy(query_type, complexity, language)
            
            return QueryAnalysis(
                original_query=query,
                processed_query=processed_query,
                query_type=query_type,
                language=language,
                complexity=complexity,
                entities=entities,
                keywords=keywords,
                intent=intent,
                best_strategy=best_strategy
            )
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            # Return basic analysis on failure
            return QueryAnalysis(
                original_query=query,
                processed_query=query,
                query_type="factual",
                language="unknown",
                complexity=0.5,
                entities=[],
                keywords=query.split(),
                intent="search",
                best_strategy=RetrievalStrategy.HYBRID
            )
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess query text"""
        # Remove extra whitespace
        processed = " ".join(query.split())
        
        # Expand common abbreviations
        abbreviations = {
            "what's": "what is",
            "how's": "how is",
            "why's": "why is",
            "什么是": "什么是",
            "怎么样": "如何",
            "为什么": "为什么"
        }
        
        for abbr, full in abbreviations.items():
            processed = processed.replace(abbr, full)
        
        return processed
    
    def _detect_language(self, query: str) -> str:
        """Detect query language"""
        chinese_chars = len([c for c in query if '\u4e00' <= c <= '\u9fff'])
        english_chars = len([c for c in query if c.isalpha() and c.isascii()])
        
        if chinese_chars > english_chars:
            return "zh"
        elif english_chars > chinese_chars:
            return "en"
        else:
            return "mixed"
    
    def _classify_query_type(self, query: str) -> str:
        """Classify query type"""
        query_lower = query.lower()
        
        # Question words
        if any(word in query_lower for word in ["what", "how", "why", "when", "where", "who", "which"]):
            return "question"
        elif any(word in query_lower for word in ["什么", "怎么", "为什么", "什么时候", "在哪里", "谁", "哪个"]):
            return "question"
        
        # Comparison
        if any(word in query_lower for word in ["compare", "difference", "vs", "versus", "比较", "区别"]):
            return "comparison"
        
        # Definition
        if any(word in query_lower for word in ["define", "definition", "meaning", "定义", "含义"]):
            return "definition"
        
        # Procedural
        if any(word in query_lower for word in ["how to", "step", "process", "如何", "步骤", "过程"]):
            return "procedural"
        
        return "factual"
    
    def _calculate_complexity(self, query: str) -> float:
        """Calculate query complexity"""
        words = query.split()
        
        # Length factor
        length_factor = min(len(words) / 20.0, 1.0)
        
        # Question word count
        question_words = ["what", "how", "why", "when", "where", "who", "which", 
                         "什么", "怎么", "为什么", "什么时候", "在哪里", "谁", "哪个"]
        question_factor = sum(1 for word in words if word.lower() in question_words) / len(words)
        
        # Complex indicators
        complex_indicators = ["compare", "analyze", "explain", "relationship", "impact",
                            "比较", "分析", "解释", "关系", "影响"]
        complexity_factor = sum(1 for word in words if word.lower() in complex_indicators) / len(words)
        
        return min((length_factor + question_factor + complexity_factor) / 3, 1.0)
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities (basic implementation)"""
        import re
        
        # Capitalized words (potential entities)
        entities = re.findall(r'\b[A-Z][a-z]+\b', query)
        
        # Numbers
        numbers = re.findall(r'\b\d+\.?\d*\b', query)
        entities.extend(numbers)
        
        return list(set(entities))
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query"""
        import re
        
        # Tokenize
        tokens = re.findall(r'\b\w+\b', query.lower())
        
        # Remove stopwords
        keywords = [token for token in tokens if token not in self.stopwords]
        
        # Remove very short words
        keywords = [kw for kw in keywords if len(kw) > 2]
        
        return keywords
    
    def _classify_intent(self, query: str, query_type: str) -> str:
        """Classify user intent"""
        query_lower = query.lower()
        
        if query_type == "definition":
            return "understand"
        elif query_type == "procedural":
            return "learn_how"
        elif query_type == "comparison":
            return "compare"
        elif any(word in query_lower for word in ["find", "search", "look for", "查找", "搜索"]):
            return "find"
        elif any(word in query_lower for word in ["explain", "tell me", "describe", "解释", "告诉我", "描述"]):
            return "understand"
        else:
            return "search"
    
    def _select_strategy(self, query_type: str, complexity: float, language: str) -> RetrievalStrategy:
        """Select optimal retrieval strategy"""
        if query_type == "definition" and complexity < 0.3:
            return RetrievalStrategy.KEYWORD
        elif complexity > 0.7:
            return RetrievalStrategy.HYBRID
        elif language == "mixed":
            return RetrievalStrategy.SEMANTIC
        else:
            return RetrievalStrategy.HYBRID

class CorpusManager:
    """Manage document corpus for keyword search"""
    
    def __init__(self):
        self.topic_corpora = {}
        self._corpus_cache = {}
    
    async def build_topic_corpus(self, topic_id: int, documents: List[Dict[str, Any]]) -> None:
        """Build corpus for a topic"""
        try:
            corpus = {
                "documents": {},
                "term_frequencies": defaultdict(dict),
                "stats": {}
            }
            
            total_tokens = 0
            
            for doc in documents:
                doc_id = doc["id"]
                content = doc["content"]
                tokens = self._tokenize(content.lower())
                
                # Store document info
                corpus["documents"][doc_id] = {
                    "content": content,
                    "tokens": tokens,
                    "document_id": doc.get("document_id", doc_id),
                    "chunk_index": doc.get("chunk_index"),
                    "metadata": doc.get("metadata", {})
                }
                
                # Build term frequencies
                token_counts = Counter(tokens)
                for term, count in token_counts.items():
                    corpus["term_frequencies"][term][doc_id] = count
                
                total_tokens += len(tokens)
            
            # Calculate stats
            corpus["stats"] = {
                "total_documents": len(documents),
                "avg_doc_length": total_tokens / len(documents) if documents else 0,
                "total_terms": len(corpus["term_frequencies"]),
                "build_time": datetime.now().isoformat()
            }
            
            self._corpus_cache[topic_id] = corpus
            logger.info(f"Built corpus for topic {topic_id} with {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Failed to build corpus for topic {topic_id}: {e}")
            raise
    
    async def get_topic_corpus(self, topic_id: int) -> Optional[Dict[str, Any]]:
        """Get corpus for a topic"""
        return self._corpus_cache.get(topic_id)
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text"""
        import re
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens

class MultiStrategyRetriever:
    """Main retrieval orchestrator"""
    
    def __init__(self, vector_store: VectorStoreManager, 
                 embedding_manager: EmbeddingManager):
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager
        
        # Initialize corpus manager
        self.corpus_manager = CorpusManager()
        
        # Initialize retrievers
        self.semantic_retriever = SemanticRetriever(vector_store, embedding_manager)
        self.keyword_retriever = KeywordRetriever(self.corpus_manager)
        self.hybrid_retriever = HybridRetriever(
            self.semantic_retriever, self.keyword_retriever
        )
        
        # Initialize re-ranker
        self.reranker = CrossEncoderReranker()
        
        # Initialize query processor
        self.query_processor = QueryProcessor()
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all components"""
        try:
            await self.vector_store.initialize()
            await self.embedding_manager.initialize()
            await self.reranker.initialize()
            
            self._initialized = True
            logger.info("Multi-strategy retriever initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize multi-strategy retriever: {e}")
            raise
    
    async def retrieve(self, query: str, topic_id: int,
                      config: Optional[RetrievalConfig] = None) -> List[RetrievalResult]:
        """Main retrieval interface"""
        if not self._initialized:
            await self.initialize()
        
        if config is None:
            config = RetrievalConfig()
        
        try:
            # Analyze query
            query_analysis = await self.query_processor.analyze_query(query)
            
            # Select retriever based on strategy
            if config.strategy == RetrievalStrategy.SEMANTIC:
                retriever = self.semantic_retriever
            elif config.strategy == RetrievalStrategy.KEYWORD:
                retriever = self.keyword_retriever
            elif config.strategy == RetrievalStrategy.HYBRID:
                retriever = self.hybrid_retriever
            else:
                # Use query analysis best strategy
                if query_analysis.best_strategy == RetrievalStrategy.SEMANTIC:
                    retriever = self.semantic_retriever
                elif query_analysis.best_strategy == RetrievalStrategy.KEYWORD:
                    retriever = self.keyword_retriever
                else:
                    retriever = self.hybrid_retriever
            
            # Perform retrieval
            results = await retriever.retrieve(
                query=query,
                topic_id=topic_id,
                limit=config.max_results * 2,  # Get more for re-ranking
                filters=None
            )
            
            # Apply score threshold
            filtered_results = [
                r for r in results if r.score >= config.min_score_threshold
            ]
            
            # Re-rank if enabled
            if config.enable_reranking and filtered_results:
                reranked_results = await self.reranker.rerank(
                    query, filtered_results, top_k=config.max_results
                )
            else:
                reranked_results = filtered_results[:config.max_results]
            
            # Apply diversity if needed
            if config.diversity_lambda > 0:
                diverse_results = self._apply_diversity(reranked_results, config.diversity_lambda)
            else:
                diverse_results = reranked_results
            
            logger.info(f"Retrieved {len(diverse_results)} results for query: {query[:50]}...")
            return diverse_results
            
        except Exception as e:
            logger.error(f"Retrieval failed for query '{query}': {e}")
            return []
    
    def _apply_diversity(self, results: List[RetrievalResult], 
                        lambda_param: float) -> List[RetrievalResult]:
        """Apply Maximal Marginal Relevance for diversity"""
        if len(results) <= 1:
            return results
        
        # Simple diversity based on content similarity
        diverse_results = [results[0]]  # Start with highest scoring result
        remaining_results = results[1:]
        
        while remaining_results and len(diverse_results) < len(results):
            best_candidate = None
            best_score = -float('inf')
            
            for candidate in remaining_results:
                # Calculate relevance score
                relevance = candidate.score
                
                # Calculate maximum similarity to already selected results
                max_similarity = 0
                for selected in diverse_results:
                    similarity = self._calculate_content_similarity(
                        candidate.content, selected.content
                    )
                    max_similarity = max(max_similarity, similarity)
                
                # MMR score
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_candidate = candidate
            
            if best_candidate:
                diverse_results.append(best_candidate)
                remaining_results.remove(best_candidate)
            else:
                break
        
        return diverse_results
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Simple content similarity calculation"""
        # Use Jaccard similarity of words
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def build_topic_index(self, topic_id: int, documents: List[Dict[str, Any]]) -> None:
        """Build search index for a topic"""
        try:
            # Build corpus for keyword search
            await self.corpus_manager.build_topic_corpus(topic_id, documents)
            
            logger.info(f"Built search index for topic {topic_id}")
            
        except Exception as e:
            logger.error(f"Failed to build topic index: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Test retrieval
            test_query = "test query"
            test_topic_id = 1
            
            # This will fail if no documents, but that's ok for health check
            try:
                results = await self.semantic_retriever.retrieve(
                    test_query, test_topic_id, limit=1
                )
                retrieval_status = "healthy"
            except:
                retrieval_status = "no_data"  # Expected if no documents indexed
            
            return {
                "status": "healthy",
                "components": {
                    "vector_store": await self.vector_store.health_check(),
                    "embedding_manager": await self.embedding_manager.health_check(),
                    "retrieval": retrieval_status,
                    "reranker": "healthy" if self.reranker._initialized else "uninitialized"
                },
                "initialized": self._initialized,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }