"""
OpenAI embedding model implementation
"""
import logging
from typing import List, Dict, Any
import time

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import BaseEmbeddingModel, EmbeddingModelInfo, EmbeddingModelFactory

logger = logging.getLogger(__name__)

class OpenAIEmbedding(BaseEmbeddingModel):
    """OpenAI embedding model implementation"""
    
    MODEL_INFO = {
        'text-embedding-3-small': {
            'dimension': 1536,
            'max_tokens': 8191,
            'cost_per_token': 0.00002 / 1000  # $0.02 per 1M tokens
        },
        'text-embedding-3-large': {
            'dimension': 3072,
            'max_tokens': 8191,
            'cost_per_token': 0.00013 / 1000  # $0.13 per 1M tokens
        },
        'text-embedding-ada-002': {
            'dimension': 1536,
            'max_tokens': 8191,
            'cost_per_token': 0.0001 / 1000  # $0.10 per 1M tokens
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI is not installed. Install with: pip install openai")
        
        super().__init__(config)
        
        # Initialize OpenAI client
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Validate model
        if self.model_name not in self.MODEL_INFO:
            logger.warning(f"Unknown OpenAI model: {self.model_name}. Using text-embedding-3-small")
            self.model_name = 'text-embedding-3-small'
        
        logger.info(f"Initialized OpenAI embedding model: {self.model_name}")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            
            embeddings = [data.embedding for data in response.data]
            logger.debug(f"Generated {len(embeddings)} embeddings using OpenAI {self.model_name}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating OpenAI embeddings: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = self.embed_texts([text])
        return embeddings[0] if embeddings else []
    
    def get_model_info(self) -> EmbeddingModelInfo:
        """Get model information"""
        model_config = self.MODEL_INFO.get(self.model_name, self.MODEL_INFO['text-embedding-3-small'])
        
        return EmbeddingModelInfo(
            provider='openai',
            model_name=self.model_name,
            dimension=model_config['dimension'],
            max_tokens=model_config['max_tokens'],
            batch_size=self.batch_size,
            cost_per_token=model_config.get('cost_per_token')
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Check model health"""
        try:
            # Test with a simple embedding
            test_embedding = self.embed_text("test")
            
            return {
                'status': 'healthy',
                'provider': 'openai',
                'model_name': self.model_name,
                'embedding_dimension': len(test_embedding),
                'connection': 'active',
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'openai',
                'model_name': self.model_name,
                'error': str(e),
                'connection': 'failed',
                'timestamp': time.time()
            }
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available OpenAI embedding models"""
        return list(cls.MODEL_INFO.keys())

# Register OpenAI provider if available
if OPENAI_AVAILABLE:
    EmbeddingModelFactory.register_provider('openai', OpenAIEmbedding)
else:
    logger.warning("OpenAI client not available. Install with: pip install openai")