"""
Base embedding model interface and factory
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class EmbeddingModelInfo:
    """Information about an embedding model"""
    provider: str
    model_name: str
    dimension: int
    max_tokens: int
    batch_size: int
    cost_per_token: Optional[float] = None

class BaseEmbeddingModel(ABC):
    """Abstract base class for embedding model implementations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get('provider', 'unknown')
        self.model_name = config.get('model_name', 'unknown')
        self.api_key = config.get('api_key')
        self.batch_size = config.get('batch_size', 100)
        
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> EmbeddingModelInfo:
        """
        Get information about the embedding model
        
        Returns:
            EmbeddingModelInfo object with model details
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Check model health and availability
        
        Returns:
            Dictionary with health status information
        """
        pass
    
    def embed_batch(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """
        Embed texts in batches for better performance
        
        Args:
            texts: List of texts to embed
            batch_size: Override default batch size
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        batch_size = batch_size or self.batch_size
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.embed_texts(batch)
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        return self.get_model_info().dimension

class EmbeddingModelFactory:
    """Factory for creating embedding model instances"""
    
    _providers = {}
    
    @classmethod
    def register_provider(cls, provider_name: str, provider_class):
        """Register an embedding model provider"""
        cls._providers[provider_name] = provider_class
    
    @classmethod
    def create(cls, provider: str, model_name: str, config: Dict[str, Any]) -> BaseEmbeddingModel:
        """
        Create an embedding model instance
        
        Args:
            provider: Provider name ('openai', 'deepseek', 'anthropic', 'huggingface')
            model_name: Specific model name
            config: Provider-specific configuration
            
        Returns:
            BaseEmbeddingModel instance
            
        Raises:
            ValueError: If provider is not supported
        """
        if provider not in cls._providers:
            raise ValueError(f"Unsupported embedding provider: {provider}. "
                           f"Available providers: {list(cls._providers.keys())}")
        
        provider_class = cls._providers[provider]
        config_with_model = config.copy()
        config_with_model['provider'] = provider
        config_with_model['model_name'] = model_name
        
        return provider_class(config_with_model)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available providers"""
        return list(cls._providers.keys())
    
    @classmethod
    def get_provider_models(cls, provider: str) -> List[str]:
        """Get available models for a provider"""
        if provider not in cls._providers:
            return []
        
        provider_class = cls._providers[provider]
        if hasattr(provider_class, 'get_available_models'):
            return provider_class.get_available_models()
        return []