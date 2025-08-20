"""
Advanced RAG System Implementation

This module implements the advanced RAG system for multi-resource topic chat
with precise answer generation and comprehensive evaluation capabilities.

## Features
- Multi-strategy retrieval (semantic, keyword, hybrid)
- Advanced answer generation with source attribution
- Conversation memory and context management
- Comprehensive evaluation framework
- Topic-based document organization
- Multi-model embedding support
- Real-time performance monitoring

## Components
- **Vector Storage**: Weaviate/ChromaDB with topic-based sharding
- **Embedding**: Multi-model support (BGE, OpenAI) with caching
- **Retrieval**: Semantic + keyword + hybrid strategies with re-ranking
- **Generation**: LLM-powered answer synthesis with citations
- **Evaluation**: Multi-dimensional quality assessment
- **Chat System**: Topic-scoped conversational AI

## Usage
```python
from modules.rag import TopicChatSystem, ChatRequest

# Initialize system
chat_system = TopicChatSystem()
await chat_system.initialize()

# Index documents
await chat_system.index_topic_documents(
    topic_id=1,
    documents=[{"id": "doc1", "content": "..."}]
)

# Chat with documents
request = ChatRequest(
    query="What is artificial intelligence?",
    topic_id=1
)
response = await chat_system.chat(request)
print(response.answer)
```
"""

from .vector_store import (
    VectorStoreManager, 
    WeaviateVectorStore, 
    ChromaDBVectorStore,
    VectorDocument,
    SearchResult
)
from .embedding import (
    EmbeddingManager, 
    MultiModelEmbedding,
    BGEEmbedding,
    OpenAIEmbedding,
    EmbeddingResult
)
from .retrieval import (
    MultiStrategyRetriever, 
    HybridRetriever,
    SemanticRetriever,
    KeywordRetriever,
    CrossEncoderReranker,
    RetrievalResult,
    RetrievalConfig
)
from .generation import (
    AdvancedAnswerGenerator, 
    ContextManager,
    OpenAIClient,
    AnthropicClient,
    GeneratedAnswer
)
from .evaluation import (
    RAGEvaluationFramework,
    RetrievalMetrics,
    GenerationMetrics,
    EndToEndMetrics,
    UserExperienceMetrics,
    EvaluationReport
)
from .chat import (
    TopicChatSystem,
    ChatRequest,
    ChatResponse,
    ChatMode
)
from .api import (
    router as rag_router,
    include_rag_routes,
    ChatRequestModel,
    ChatResponseModel
)

__all__ = [
    # Core system
    "TopicChatSystem",
    "ChatRequest", 
    "ChatResponse",
    "ChatMode",
    
    # Vector storage
    "VectorStoreManager",
    "WeaviateVectorStore",
    "ChromaDBVectorStore", 
    "VectorDocument",
    "SearchResult",
    
    # Embedding
    "EmbeddingManager",
    "MultiModelEmbedding",
    "BGEEmbedding",
    "OpenAIEmbedding",
    "EmbeddingResult",
    
    # Retrieval
    "MultiStrategyRetriever",
    "HybridRetriever",
    "SemanticRetriever",
    "KeywordRetriever",
    "CrossEncoderReranker",
    "RetrievalResult",
    "RetrievalConfig",
    
    # Generation
    "AdvancedAnswerGenerator",
    "ContextManager", 
    "OpenAIClient",
    "AnthropicClient",
    "GeneratedAnswer",
    
    # Evaluation
    "RAGEvaluationFramework",
    "RetrievalMetrics",
    "GenerationMetrics", 
    "EndToEndMetrics",
    "UserExperienceMetrics",
    "EvaluationReport",
    
    # API
    "rag_router",
    "include_rag_routes",
    "ChatRequestModel",
    "ChatResponseModel"
]

# Version info
__version__ = "1.0.0"
__author__ = "Advanced RAG Team"
__description__ = "Multi-resource topic chat with precise answer generation"