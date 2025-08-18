"""
RAG Domain Interfaces

This module defines the core domain interfaces for the RAG system,
following SOLID principles to ensure clean architecture and extensibility.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Iterator, Union, AsyncIterator
from datetime import datetime
from enum import Enum

# Import models from existing RAG structure
from rag.models import (
    Document, DocumentChunk, ProcessingResult, QueryResult, 
    RetrievalResult, DocumentStatus, SearchFilter
)


class ProcessingStatus(Enum):
    """Document processing status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SearchStrategy(Enum):
    """Search strategy enumeration."""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    FUZZY = "fuzzy"


# Core Domain Interfaces (following Interface Segregation Principle)

class IDocumentLoader(ABC):
    """
    Document loading interface (SRP: responsible only for loading documents).
    
    This interface abstracts document loading from various sources,
    allowing for different implementations (file system, cloud storage, etc.).
    """
    
    @abstractmethod
    async def load_document(self, source: str, **kwargs) -> Document:
        """
        Load a single document from the specified source.
        
        Args:
            source: Document source (file path, URL, etc.)
            **kwargs: Additional loading parameters
            
        Returns:
            Document: Loaded document object
            
        Raises:
            DocumentLoadError: If document cannot be loaded
        """
        pass
    
    @abstractmethod
    async def load_documents_batch(self, sources: List[str], **kwargs) -> AsyncIterator[ProcessingResult]:
        """
        Load multiple documents in batch.
        
        Args:
            sources: List of document sources
            **kwargs: Additional loading parameters
            
        Yields:
            ProcessingResult: Result for each document loading attempt
        """
        pass
    
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """
        Get list of supported document formats.
        
        Returns:
            List[str]: List of supported file extensions
        """
        pass


class IDocumentProcessor(ABC):
    """
    Document processing interface (SRP: responsible only for processing documents).
    
    This interface handles document parsing, chunking, and preprocessing
    before indexing.
    """
    
    @abstractmethod
    async def process_document(self, document: Document, **config) -> ProcessingResult:
        """
        Process a single document (parse, chunk, extract metadata).
        
        Args:
            document: Document to process
            **config: Processing configuration
            
        Returns:
            ProcessingResult: Processing result with chunks and metadata
        """
        pass
    
    @abstractmethod
    async def chunk_document(self, document: Document, **config) -> List[DocumentChunk]:
        """
        Split document into chunks for indexing.
        
        Args:
            document: Document to chunk
            **config: Chunking configuration (chunk_size, overlap, etc.)
            
        Returns:
            List[DocumentChunk]: List of document chunks
        """
        pass
    
    @abstractmethod
    async def extract_metadata(self, document: Document) -> Dict[str, Any]:
        """
        Extract metadata from document.
        
        Args:
            document: Document to analyze
            
        Returns:
            Dict[str, Any]: Extracted metadata
        """
        pass


class IVectorStore(ABC):
    """
    Vector storage interface (SRP: responsible only for vector operations).
    
    This interface abstracts vector storage and similarity search operations.
    """
    
    @abstractmethod
    async def add_documents(self, chunks: List[DocumentChunk]) -> bool:
        """
        Add document chunks to vector store.
        
        Args:
            chunks: List of document chunks with embeddings
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    async def search_similar(self, 
                           query_embedding: List[float], 
                           top_k: int = 10,
                           filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filters: Search filters
            
        Returns:
            List[RetrievalResult]: Similar documents with scores
        """
        pass
    
    @abstractmethod
    async def search_by_text(self, 
                           query_text: str, 
                           top_k: int = 10,
                           filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """
        Search using text query (internally converts to embedding).
        
        Args:
            query_text: Text query
            top_k: Number of results to return
            filters: Search filters
            
        Returns:
            List[RetrievalResult]: Search results with scores
        """
        pass
    
    @abstractmethod
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """
        Delete documents from vector store.
        
        Args:
            document_ids: List of document IDs to delete
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    async def get_store_info(self) -> Dict[str, Any]:
        """
        Get vector store information and statistics.
        
        Returns:
            Dict[str, Any]: Store information
        """
        pass


class IIndexManager(ABC):
    """
    Index management interface (SRP: responsible only for index operations).
    
    This interface manages document indexing, updating, and deletion.
    """
    
    @abstractmethod
    async def create_index(self, name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a new index.
        
        Args:
            name: Index name
            config: Index configuration
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    async def index_document(self, document: Document, index_name: Optional[str] = None) -> ProcessingResult:
        """
        Index a single document.
        
        Args:
            document: Document to index
            index_name: Target index name (optional)
            
        Returns:
            ProcessingResult: Indexing result
        """
        pass
    
    @abstractmethod
    async def index_documents_batch(self, 
                                  documents: List[Document], 
                                  index_name: Optional[str] = None) -> AsyncIterator[ProcessingResult]:
        """
        Index multiple documents in batch.
        
        Args:
            documents: Documents to index
            index_name: Target index name (optional)
            
        Yields:
            ProcessingResult: Result for each document
        """
        pass
    
    @abstractmethod
    async def update_document(self, document: Document, index_name: Optional[str] = None) -> ProcessingResult:
        """
        Update an indexed document.
        
        Args:
            document: Updated document
            index_name: Target index name (optional)
            
        Returns:
            ProcessingResult: Update result
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str, index_name: Optional[str] = None) -> bool:
        """
        Delete a document from index.
        
        Args:
            document_id: Document ID to delete
            index_name: Target index name (optional)
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    async def get_index_stats(self, index_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Args:
            index_name: Index name (optional, default index if not specified)
            
        Returns:
            Dict[str, Any]: Index statistics
        """
        pass


class ISearchService(ABC):
    """
    Search service interface (SRP: responsible only for search operations).
    
    This interface provides high-level search capabilities with different strategies.
    """
    
    @abstractmethod
    async def search(self, 
                   query: str, 
                   strategy: SearchStrategy = SearchStrategy.SEMANTIC,
                   top_k: int = 10,
                   filters: Optional[SearchFilter] = None,
                   **kwargs) -> QueryResult:
        """
        Perform search with specified strategy.
        
        Args:
            query: Search query
            strategy: Search strategy to use
            top_k: Number of results to return
            filters: Search filters
            **kwargs: Additional search parameters
            
        Returns:
            QueryResult: Search results
        """
        pass
    
    @abstractmethod
    async def semantic_search(self, 
                            query: str, 
                            top_k: int = 10,
                            filters: Optional[SearchFilter] = None) -> QueryResult:
        """
        Perform semantic search using embeddings.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Search filters
            
        Returns:
            QueryResult: Search results
        """
        pass
    
    @abstractmethod
    async def keyword_search(self, 
                           query: str, 
                           top_k: int = 10,
                           filters: Optional[SearchFilter] = None) -> QueryResult:
        """
        Perform keyword-based search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Search filters
            
        Returns:
            QueryResult: Search results
        """
        pass
    
    @abstractmethod
    async def hybrid_search(self, 
                          query: str, 
                          semantic_weight: float = 0.7,
                          keyword_weight: float = 0.3,
                          top_k: int = 10,
                          filters: Optional[SearchFilter] = None) -> QueryResult:
        """
        Perform hybrid search combining semantic and keyword search.
        
        Args:
            query: Search query
            semantic_weight: Weight for semantic search results
            keyword_weight: Weight for keyword search results
            top_k: Number of results to return
            filters: Search filters
            
        Returns:
            QueryResult: Search results
        """
        pass


class IKnowledgeManager(ABC):
    """
    Knowledge management interface (SRP: responsible only for knowledge operations).
    
    This interface manages the knowledge base, including documents, metadata,
    and relationships.
    """
    
    @abstractmethod
    async def add_document(self, document: Document) -> ProcessingResult:
        """
        Add a document to the knowledge base.
        
        Args:
            document: Document to add
            
        Returns:
            ProcessingResult: Addition result
        """
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Document]:
        """
        Retrieve a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Optional[Document]: Document if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_documents(self, 
                           filters: Optional[SearchFilter] = None,
                           limit: int = 100,
                           offset: int = 0) -> List[Document]:
        """
        List documents with optional filtering.
        
        Args:
            filters: Search filters
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List[Document]: List of documents
        """
        pass
    
    @abstractmethod
    async def update_document(self, document: Document) -> ProcessingResult:
        """
        Update an existing document.
        
        Args:
            document: Updated document
            
        Returns:
            ProcessingResult: Update result
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the knowledge base.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    async def get_document_chunks(self, document_id: str) -> List[DocumentChunk]:
        """
        Get all chunks for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List[DocumentChunk]: Document chunks
        """
        pass
    
    @abstractmethod
    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """
        Get knowledge base statistics.
        
        Returns:
            Dict[str, Any]: Statistics including document count, size, etc.
        """
        pass


class IEmbeddingService(ABC):
    """
    Embedding service interface (SRP: responsible only for embedding generation).
    
    This interface abstracts text embedding generation, allowing for different
    embedding models and providers.
    """
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List[float]: Text embedding vector
        """
        pass
    
    @abstractmethod
    async def embed_texts_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this service.
        
        Returns:
            int: Embedding dimension
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding model.
        
        Returns:
            Dict[str, Any]: Model information
        """
        pass


# Composite interfaces for higher-level operations

class IRAGOrchestrator(ABC):
    """
    RAG orchestrator interface (SRP: responsible for coordinating RAG operations).
    
    This interface coordinates the entire RAG workflow, from document ingestion
    to query answering.
    """
    
    @abstractmethod
    async def ingest_document(self, source: str, **config) -> ProcessingResult:
        """
        Complete document ingestion workflow.
        
        Args:
            source: Document source
            **config: Ingestion configuration
            
        Returns:
            ProcessingResult: Overall ingestion result
        """
        pass
    
    @abstractmethod
    async def query_knowledge(self, 
                            query: str, 
                            strategy: SearchStrategy = SearchStrategy.SEMANTIC,
                            **config) -> QueryResult:
        """
        Complete knowledge query workflow.
        
        Args:
            query: User query
            strategy: Search strategy
            **config: Query configuration
            
        Returns:
            QueryResult: Query result with context
        """
        pass
    
    @abstractmethod
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status and health.
        
        Returns:
            Dict[str, Any]: System status information
        """
        pass


# Exception classes for domain operations

class RAGDomainError(Exception):
    """Base exception for RAG domain operations."""
    pass


class DocumentLoadError(RAGDomainError):
    """Document loading error."""
    pass


class DocumentProcessingError(RAGDomainError):
    """Document processing error."""
    pass


class IndexingError(RAGDomainError):
    """Indexing operation error."""
    pass


class SearchError(RAGDomainError):
    """Search operation error."""
    pass


class EmbeddingError(RAGDomainError):
    """Embedding generation error."""
    pass