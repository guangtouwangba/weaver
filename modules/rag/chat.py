"""
Advanced Topic Chat System

Main orchestrator for multi-resource topic chat with precise answer generation,
conversation memory, and comprehensive context management.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .vector_store import VectorStoreManager, VectorDocument
from .embedding import EmbeddingManager
from .retrieval import MultiStrategyRetriever, RetrievalConfig, RetrievalResult
from .generation import AdvancedAnswerGenerator, GeneratedAnswer, LLMProvider
from .evaluation import RAGEvaluationFramework

logger = logging.getLogger(__name__)

class ChatMode(str, Enum):
    """Chat mode types"""
    SINGLE_TURN = "single_turn"
    CONVERSATION = "conversation"
    EXPLORATION = "exploration"

class QueryComplexity(str, Enum):
    """Query complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"

@dataclass
class ChatRequest:
    """Chat request from user"""
    query: str
    topic_id: int
    conversation_id: Optional[str] = None
    mode: ChatMode = ChatMode.CONVERSATION
    max_sources: int = 5
    temperature: float = 0.1
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ChatResponse:
    """Chat response to user"""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    conversation_id: str
    response_time: float
    follow_up_questions: Optional[List[str]] = None
    query_analysis: Optional[Dict[str, Any]] = None
    retrieval_stats: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class TopicAnalysis:
    """Topic analysis and statistics"""
    topic_id: int
    document_count: int
    total_chunks: int
    average_chunk_score: float
    content_types: Dict[str, int]
    languages: Dict[str, int]
    last_updated: datetime

@dataclass
class ConversationSummary:
    """Conversation summary and statistics"""
    conversation_id: str
    topic_id: int
    turn_count: int
    average_response_time: float
    user_satisfaction: Optional[float]
    common_topics: List[str]
    unresolved_questions: List[str]
    created_at: datetime
    last_activity: datetime

class TopicChatSystem:
    """Advanced topic-based multi-resource chat system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize core components
        self.vector_store = VectorStoreManager(
            store_type=self.config.get("vector_store_type", "weaviate"),
            config=self.config.get("vector_store_config", {})
        )
        
        self.embedding_manager = EmbeddingManager(
            cache_config=self.config.get("embedding_cache_config", {})
        )
        
        self.retriever = MultiStrategyRetriever(
            vector_store=self.vector_store,
            embedding_manager=self.embedding_manager
        )
        
        self.answer_generator = AdvancedAnswerGenerator(
            provider=LLMProvider(self.config.get("llm_provider", "openai")),
            config=self.config.get("generation_config", {})
        )
        
        self.evaluation_framework = RAGEvaluationFramework()
        
        # State management
        self.topic_analyses = {}
        self.active_conversations = {}
        self.performance_metrics = {
            "total_queries": 0,
            "successful_responses": 0,
            "average_response_time": 0.0,
            "user_ratings": []
        }
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the chat system"""
        try:
            logger.info("Initializing Topic Chat System...")
            
            # Initialize all components
            await self.vector_store.initialize()
            await self.embedding_manager.initialize()
            await self.retriever.initialize()
            await self.answer_generator.initialize()
            
            self._initialized = True
            logger.info("Topic Chat System initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Topic Chat System: {e}")
            raise
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Main chat interface"""
        if not self._initialized:
            await self.initialize()
        
        start_time = asyncio.get_event_loop().time()
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        try:
            logger.info(f"Processing chat request for topic {request.topic_id}: {request.query[:100]}...")
            
            # Update metrics
            self.performance_metrics["total_queries"] += 1
            
            # Analyze query complexity
            query_analysis = await self._analyze_query_complexity(request.query)
            
            # Configure retrieval based on query complexity
            retrieval_config = self._configure_retrieval(query_analysis, request)
            
            # Perform retrieval
            retrieval_results = await self.retriever.retrieve(
                query=request.query,
                topic_id=request.topic_id,
                config=retrieval_config
            )
            
            # Generate answer
            generated_answer = await self.answer_generator.generate_answer(
                query=request.query,
                retrieval_results=retrieval_results,
                conversation_id=conversation_id,
                topic_id=request.topic_id
            )
            
            # Calculate response time
            response_time = asyncio.get_event_loop().time() - start_time
            
            # Build response
            response = ChatResponse(
                answer=generated_answer.content,
                confidence=generated_answer.confidence,
                sources=generated_answer.sources,
                conversation_id=conversation_id,
                response_time=response_time,
                follow_up_questions=generated_answer.follow_up_questions,
                query_analysis={
                    "complexity": query_analysis["complexity"].value,
                    "intent": query_analysis["intent"],
                    "language": query_analysis["language"],
                    "entities": query_analysis["entities"]
                },
                retrieval_stats={
                    "total_results": len(retrieval_results),
                    "strategy_used": retrieval_config.strategy.value,
                    "average_score": sum(r.score for r in retrieval_results) / len(retrieval_results) if retrieval_results else 0,
                    "unique_documents": len(set(r.document_id for r in retrieval_results))
                },
                metadata={
                    "model_used": generated_answer.model_used,
                    "processing_time_breakdown": {
                        "total": response_time,
                        "generation": generated_answer.generation_time,
                        "retrieval": response_time - generated_answer.generation_time
                    }
                }
            )
            
            # Update conversation tracking
            await self._update_conversation_tracking(conversation_id, request, response)
            
            # Update performance metrics
            self.performance_metrics["successful_responses"] += 1
            self._update_average_response_time(response_time)
            
            logger.info(f"Chat completed in {response_time:.2f}s with confidence {response.confidence:.2f}")
            return response
            
        except Exception as e:
            logger.error(f"Chat request failed: {e}")
            response_time = asyncio.get_event_loop().time() - start_time
            
            return ChatResponse(
                answer=f"抱歉，处理您的请求时遇到了问题：{str(e)}",
                confidence=0.0,
                sources=[],
                conversation_id=conversation_id,
                response_time=response_time,
                metadata={"error": str(e)}
            )
    
    async def index_topic_documents(self, topic_id: int, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index documents for a topic"""
        try:
            logger.info(f"Indexing {len(documents)} documents for topic {topic_id}")
            
            # Process documents and create vector documents
            vector_documents = []
            chunk_count = 0
            
            for doc in documents:
                # Extract text content
                content = doc.get("content", "")
                if not content:
                    continue
                
                # Create chunks (simplified chunking for now)
                chunks = self._create_document_chunks(content, doc["id"])
                
                for chunk in chunks:
                    # Generate embedding
                    embedding_result = await self.embedding_manager.get_or_create_embedding(
                        chunk["content"]
                    )
                    
                    # Create vector document
                    vector_doc = VectorDocument(
                        id=chunk["id"],
                        content=chunk["content"],
                        embedding=embedding_result.embedding,
                        metadata={
                            "title": doc.get("title", ""),
                            "document_id": doc["id"],
                            "chunk_index": chunk["index"],
                            "page_number": chunk.get("page_number"),
                            "section": chunk.get("section"),
                            "content_type": embedding_result.content_type.value,
                            "language": embedding_result.language,
                            "indexed_at": datetime.now().isoformat()
                        },
                        topic_id=topic_id,
                        document_id=doc["id"],
                        chunk_index=chunk["index"]
                    )
                    vector_documents.append(vector_doc)
                    chunk_count += 1
            
            # Index in vector store
            await self.vector_store.add_topic_documents(topic_id, vector_documents)
            
            # Build retrieval index
            doc_data = []
            for vec_doc in vector_documents:
                doc_data.append({
                    "id": vec_doc.id,
                    "content": vec_doc.content,
                    "document_id": vec_doc.document_id,
                    "chunk_index": vec_doc.chunk_index,
                    "metadata": vec_doc.metadata
                })
            
            await self.retriever.build_topic_index(topic_id, doc_data)
            
            # Update topic analysis
            await self._update_topic_analysis(topic_id, documents, vector_documents)
            
            return {
                "success": True,
                "topic_id": topic_id,
                "documents_processed": len(documents),
                "chunks_created": chunk_count,
                "indexing_completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to index documents for topic {topic_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "topic_id": topic_id
            }
    
    def _create_document_chunks(self, content: str, document_id: str, 
                               chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Create document chunks with overlap"""
        chunks = []
        
        # Simple sentence-based chunking
        sentences = content.split('.')
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                # Create chunk
                chunk = {
                    "id": f"{document_id}_chunk_{chunk_index}",
                    "content": current_chunk.strip(),
                    "index": chunk_index,
                    "start_char": len(content) - len(current_chunk),
                    "end_char": len(content)
                }
                chunks.append(chunk)
                
                # Start new chunk with overlap
                words = current_chunk.split()
                overlap_words = words[-overlap//10:] if len(words) > overlap//10 else words
                current_chunk = " ".join(overlap_words) + " " + sentence
                chunk_index += 1
            else:
                current_chunk += sentence + "."
        
        # Add final chunk
        if current_chunk.strip():
            chunk = {
                "id": f"{document_id}_chunk_{chunk_index}",
                "content": current_chunk.strip(),
                "index": chunk_index,
                "start_char": len(content) - len(current_chunk),
                "end_char": len(content)
            }
            chunks.append(chunk)
        
        return chunks
    
    async def _analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """Analyze query complexity and characteristics"""
        # Simple complexity analysis
        word_count = len(query.split())
        
        # Determine complexity
        if word_count < 5:
            complexity = QueryComplexity.SIMPLE
        elif word_count < 15:
            complexity = QueryComplexity.MODERATE
        else:
            complexity = QueryComplexity.COMPLEX
        
        # Simple intent classification
        query_lower = query.lower()
        if any(word in query_lower for word in ["what", "who", "when", "where", "什么", "谁", "什么时候", "在哪里"]):
            intent = "factual"
        elif any(word in query_lower for word in ["how", "why", "如何", "为什么"]):
            intent = "explanatory"
        elif any(word in query_lower for word in ["compare", "difference", "比较", "区别"]):
            intent = "comparative"
        else:
            intent = "general"
        
        # Simple language detection
        chinese_chars = sum(1 for char in query if '\u4e00' <= char <= '\u9fff')
        english_chars = sum(1 for char in query if char.isalpha() and ord(char) < 128)
        
        if chinese_chars > english_chars:
            language = "zh"
        elif english_chars > chinese_chars:
            language = "en"
        else:
            language = "mixed"
        
        # Simple entity extraction (capitalized words and numbers)
        import re
        entities = re.findall(r'\b[A-Z][a-z]+\b|\b\d+\.?\d*\b', query)
        
        return {
            "complexity": complexity,
            "word_count": word_count,
            "intent": intent,
            "language": language,
            "entities": entities,
            "has_questions": "?" in query,
            "analysis_time": datetime.now().isoformat()
        }
    
    def _configure_retrieval(self, query_analysis: Dict[str, Any], 
                           request: ChatRequest) -> RetrievalConfig:
        """Configure retrieval based on query analysis"""
        complexity = query_analysis["complexity"]
        
        # Adjust parameters based on complexity
        if complexity == QueryComplexity.SIMPLE:
            return RetrievalConfig(
                strategy=request.config.get("strategy", "keyword") if hasattr(request, 'config') else "keyword",
                max_results=min(request.max_sources, 3),
                semantic_weight=0.4,
                keyword_weight=0.6,
                enable_reranking=False
            )
        elif complexity == QueryComplexity.MODERATE:
            return RetrievalConfig(
                strategy=request.config.get("strategy", "hybrid") if hasattr(request, 'config') else "hybrid",
                max_results=request.max_sources,
                semantic_weight=0.6,
                keyword_weight=0.4,
                enable_reranking=True
            )
        else:  # COMPLEX
            return RetrievalConfig(
                strategy=request.config.get("strategy", "hybrid") if hasattr(request, 'config') else "hybrid",
                max_results=request.max_sources * 2,  # Get more for complex queries
                semantic_weight=0.7,
                keyword_weight=0.3,
                enable_reranking=True,
                diversity_lambda=0.3  # Encourage diversity for complex queries
            )
    
    async def _update_conversation_tracking(self, conversation_id: str, 
                                          request: ChatRequest, response: ChatResponse) -> None:
        """Update conversation tracking and memory"""
        if conversation_id not in self.active_conversations:
            self.active_conversations[conversation_id] = ConversationSummary(
                conversation_id=conversation_id,
                topic_id=request.topic_id,
                turn_count=0,
                average_response_time=0.0,
                user_satisfaction=None,
                common_topics=[],
                unresolved_questions=[],
                created_at=datetime.now(),
                last_activity=datetime.now()
            )
        
        conversation = self.active_conversations[conversation_id]
        conversation.turn_count += 1
        conversation.last_activity = datetime.now()
        
        # Update average response time
        total_time = conversation.average_response_time * (conversation.turn_count - 1)
        conversation.average_response_time = (total_time + response.response_time) / conversation.turn_count
    
    async def _update_topic_analysis(self, topic_id: int, documents: List[Dict[str, Any]], 
                                   vector_documents: List[VectorDocument]) -> None:
        """Update topic analysis and statistics"""
        # Analyze content types
        content_types = {}
        languages = {}
        
        for vec_doc in vector_documents:
            content_type = vec_doc.metadata.get("content_type", "unknown")
            content_types[content_type] = content_types.get(content_type, 0) + 1
            
            language = vec_doc.metadata.get("language", "unknown")
            languages[language] = languages.get(language, 0) + 1
        
        # Calculate average chunk score (placeholder)
        average_chunk_score = 0.8  # Would be calculated based on actual metrics
        
        self.topic_analyses[topic_id] = TopicAnalysis(
            topic_id=topic_id,
            document_count=len(documents),
            total_chunks=len(vector_documents),
            average_chunk_score=average_chunk_score,
            content_types=content_types,
            languages=languages,
            last_updated=datetime.now()
        )
    
    def _update_average_response_time(self, response_time: float) -> None:
        """Update average response time metric"""
        current_avg = self.performance_metrics["average_response_time"]
        total_queries = self.performance_metrics["total_queries"]
        
        new_avg = ((current_avg * (total_queries - 1)) + response_time) / total_queries
        self.performance_metrics["average_response_time"] = new_avg
    
    async def get_topic_statistics(self, topic_id: int) -> Optional[Dict[str, Any]]:
        """Get statistics for a topic"""
        if topic_id not in self.topic_analyses:
            return None
        
        analysis = self.topic_analyses[topic_id]
        return asdict(analysis)
    
    async def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation summary"""
        if conversation_id not in self.active_conversations:
            return None
        
        summary = self.active_conversations[conversation_id]
        return asdict(summary)
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        return {
            **self.performance_metrics,
            "active_conversations": len(self.active_conversations),
            "indexed_topics": len(self.topic_analyses),
            "system_uptime": datetime.now().isoformat(),
            "component_status": await self._get_component_health()
        }
    
    async def _get_component_health(self) -> Dict[str, str]:
        """Get health status of all components"""
        health_checks = {}
        
        try:
            vector_health = await self.vector_store.health_check()
            health_checks["vector_store"] = vector_health.get("status", "unknown")
        except:
            health_checks["vector_store"] = "unhealthy"
        
        try:
            embedding_health = await self.embedding_manager.health_check()
            health_checks["embedding_manager"] = embedding_health.get("status", "unknown")
        except:
            health_checks["embedding_manager"] = "unhealthy"
        
        try:
            retriever_health = await self.retriever.health_check()
            health_checks["retriever"] = retriever_health.get("status", "unknown")
        except:
            health_checks["retriever"] = "unhealthy"
        
        try:
            generator_health = await self.answer_generator.health_check()
            health_checks["answer_generator"] = generator_health.get("status", "unknown")
        except:
            health_checks["answer_generator"] = "unhealthy"
        
        return health_checks
    
    async def evaluate_system_performance(self, test_cases_file: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate system performance using the evaluation framework"""
        try:
            # Load test cases
            test_cases = await self.evaluation_framework.load_test_cases(test_cases_file)
            
            # Run evaluation
            report = await self.evaluation_framework.run_comprehensive_evaluation(
                test_cases, self
            )
            
            return {
                "evaluation_completed": True,
                "overall_score": report.overall_score,
                "metric_scores": report.metric_scores,
                "recommendations": report.recommendations,
                "test_summary": report.test_summary,
                "report_timestamp": report.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"System evaluation failed: {e}")
            return {
                "evaluation_completed": False,
                "error": str(e)
            }
    
    async def cleanup_inactive_conversations(self, max_age_hours: int = 24) -> int:
        """Cleanup inactive conversations"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        inactive_conversations = []
        
        for conv_id, conv_summary in self.active_conversations.items():
            if conv_summary.last_activity < cutoff_time:
                inactive_conversations.append(conv_id)
        
        for conv_id in inactive_conversations:
            del self.active_conversations[conv_id]
        
        logger.info(f"Cleaned up {len(inactive_conversations)} inactive conversations")
        return len(inactive_conversations)
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive system health check"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Check all components
            component_health = await self._get_component_health()
            
            # Overall health determination
            healthy_components = sum(1 for status in component_health.values() if status == "healthy")
            total_components = len(component_health)
            health_ratio = healthy_components / total_components if total_components > 0 else 0
            
            if health_ratio >= 1.0:
                overall_status = "healthy"
            elif health_ratio >= 0.5:
                overall_status = "degraded"
            else:
                overall_status = "unhealthy"
            
            health_check_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "status": overall_status,
                "initialized": self._initialized,
                "components": component_health,
                "health_ratio": health_ratio,
                "performance_metrics": self.performance_metrics,
                "active_conversations": len(self.active_conversations),
                "indexed_topics": len(self.topic_analyses),
                "health_check_time": health_check_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the system"""
        try:
            logger.info("Shutting down Topic Chat System...")
            
            # Save conversation summaries (in production, this would persist to database)
            logger.info(f"Saving {len(self.active_conversations)} active conversations")
            
            # Cleanup resources
            self.active_conversations.clear()
            self.topic_analyses.clear()
            
            logger.info("Topic Chat System shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")