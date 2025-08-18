"""Configuration for DDD + RAG architecture."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import os
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "rag_db"
    username: str = "rag_user"
    password: str = "rag_password"
    pool_size: int = 10
    
    @property
    def connection_url(self) -> str:
        """Get database connection URL."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class VectorStoreConfig:
    """Vector store configuration."""
    provider: str = "chroma"  # chroma, pinecone, weaviate, etc.
    host: str = "localhost"
    port: int = 8000
    collection_name: str = "knowledge_base"
    embedding_dimension: int = 1536
    
    # Provider-specific settings
    api_key: Optional[str] = None
    environment: Optional[str] = None
    index_name: Optional[str] = None


@dataclass
class EmbeddingConfig:
    """Embedding model configuration."""
    provider: str = "openai"  # openai, huggingface, local, etc.
    model_name: str = "text-embedding-ada-002"
    api_key: Optional[str] = None
    max_tokens: int = 8191
    batch_size: int = 100


@dataclass
class DocumentProcessingConfig:
    """Document processing configuration."""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_file_size_mb: int = 100
    supported_file_types: List[str] = None
    
    def __post_init__(self):
        if self.supported_file_types is None:
            self.supported_file_types = [
                "text/plain",
                "text/markdown", 
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ]


@dataclass
class SearchConfig:
    """Search configuration."""
    default_top_k: int = 10
    max_top_k: int = 100
    similarity_threshold: float = 0.7
    enable_hybrid_search: bool = True
    enable_reranking: bool = True
    reranking_model: Optional[str] = None


@dataclass
class RAGConfig:
    """RAG system configuration."""
    database: DatabaseConfig = None
    vector_store: VectorStoreConfig = None
    embedding: EmbeddingConfig = None
    document_processing: DocumentProcessingConfig = None
    search: SearchConfig = None
    
    # System settings
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # File storage
    storage_path: str = "./storage"
    temp_path: str = "./temp"
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig()
        if self.vector_store is None:
            self.vector_store = VectorStoreConfig()
        if self.embedding is None:
            self.embedding = EmbeddingConfig()
        if self.document_processing is None:
            self.document_processing = DocumentProcessingConfig()
        if self.search is None:
            self.search = SearchConfig()
    
    @classmethod
    def from_env(cls) -> 'RAGConfig':
        """Create configuration from environment variables."""
        return cls(
            database=DatabaseConfig(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '5432')),
                database=os.getenv('DB_NAME', 'rag_db'),
                username=os.getenv('DB_USER', 'rag_user'),
                password=os.getenv('DB_PASSWORD', 'rag_password'),
                pool_size=int(os.getenv('DB_POOL_SIZE', '10'))
            ),
            vector_store=VectorStoreConfig(
                provider=os.getenv('VECTOR_STORE_PROVIDER', 'chroma'),
                host=os.getenv('VECTOR_STORE_HOST', 'localhost'),
                port=int(os.getenv('VECTOR_STORE_PORT', '8000')),
                collection_name=os.getenv('VECTOR_COLLECTION_NAME', 'knowledge_base'),
                embedding_dimension=int(os.getenv('EMBEDDING_DIMENSION', '1536')),
                api_key=os.getenv('VECTOR_STORE_API_KEY'),
                environment=os.getenv('VECTOR_STORE_ENV'),
                index_name=os.getenv('VECTOR_STORE_INDEX')
            ),
            embedding=EmbeddingConfig(
                provider=os.getenv('EMBEDDING_PROVIDER', 'openai'),
                model_name=os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002'),
                api_key=os.getenv('OPENAI_API_KEY'),
                max_tokens=int(os.getenv('EMBEDDING_MAX_TOKENS', '8191')),
                batch_size=int(os.getenv('EMBEDDING_BATCH_SIZE', '100'))
            ),
            document_processing=DocumentProcessingConfig(
                chunk_size=int(os.getenv('CHUNK_SIZE', '1000')),
                chunk_overlap=int(os.getenv('CHUNK_OVERLAP', '200')),
                min_chunk_size=int(os.getenv('MIN_CHUNK_SIZE', '100')),
                max_file_size_mb=int(os.getenv('MAX_FILE_SIZE_MB', '100'))
            ),
            search=SearchConfig(
                default_top_k=int(os.getenv('DEFAULT_TOP_K', '10')),
                max_top_k=int(os.getenv('MAX_TOP_K', '100')),
                similarity_threshold=float(os.getenv('SIMILARITY_THRESHOLD', '0.7')),
                enable_hybrid_search=os.getenv('ENABLE_HYBRID_SEARCH', 'true').lower() == 'true',
                enable_reranking=os.getenv('ENABLE_RERANKING', 'true').lower() == 'true'
            ),
            environment=os.getenv('ENVIRONMENT', 'development'),
            debug=os.getenv('DEBUG', 'true').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            storage_path=os.getenv('STORAGE_PATH', './storage'),
            temp_path=os.getenv('TEMP_PATH', './temp')
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return any errors."""
        errors = []
        warnings = []
        
        # Validate required fields based on providers (but only warn in development)
        if self.embedding.provider == "openai" and not self.embedding.api_key:
            if self.environment == "production":
                errors.append("OpenAI API key is required when using OpenAI embeddings in production")
            else:
                warnings.append("OpenAI API key not set - some features may not work")
        
        if self.vector_store.provider == "pinecone" and not self.vector_store.api_key:
            if self.environment == "production":
                errors.append("Pinecone API key is required when using Pinecone in production")
            else:
                warnings.append("Pinecone API key not set - using fallback vector store")
        
        # Validate paths
        try:
            Path(self.storage_path).mkdir(parents=True, exist_ok=True)
            Path(self.temp_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create storage directories: {e}")
        
        # Validate numeric ranges
        if self.document_processing.chunk_size <= 0:
            errors.append("Chunk size must be positive")
        
        if self.document_processing.chunk_overlap >= self.document_processing.chunk_size:
            errors.append("Chunk overlap must be less than chunk size")
        
        if not 0.0 <= self.search.similarity_threshold <= 1.0:
            errors.append("Similarity threshold must be between 0.0 and 1.0")
        
        # Log warnings if any
        if warnings:
            import logging
            logger = logging.getLogger(__name__)
            for warning in warnings:
                logger.warning(warning)
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "pool_size": self.database.pool_size
            },
            "vector_store": {
                "provider": self.vector_store.provider,
                "host": self.vector_store.host,
                "port": self.vector_store.port,
                "collection_name": self.vector_store.collection_name,
                "embedding_dimension": self.vector_store.embedding_dimension
            },
            "embedding": {
                "provider": self.embedding.provider,
                "model_name": self.embedding.model_name,
                "max_tokens": self.embedding.max_tokens,
                "batch_size": self.embedding.batch_size
            },
            "document_processing": {
                "chunk_size": self.document_processing.chunk_size,
                "chunk_overlap": self.document_processing.chunk_overlap,
                "min_chunk_size": self.document_processing.min_chunk_size,
                "max_file_size_mb": self.document_processing.max_file_size_mb,
                "supported_file_types": self.document_processing.supported_file_types
            },
            "search": {
                "default_top_k": self.search.default_top_k,
                "max_top_k": self.search.max_top_k,
                "similarity_threshold": self.search.similarity_threshold,
                "enable_hybrid_search": self.search.enable_hybrid_search,
                "enable_reranking": self.search.enable_reranking
            },
            "environment": self.environment,
            "debug": self.debug,
            "log_level": self.log_level,
            "storage_path": self.storage_path,
            "temp_path": self.temp_path
        }


# Global configuration instance
_config: Optional[RAGConfig] = None


def get_config() -> RAGConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = RAGConfig.from_env()
    return _config


def set_config(config: RAGConfig) -> None:
    """Set global configuration instance."""
    global _config
    _config = config
