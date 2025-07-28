"""
DeepSeek embedding model implementation
"""
import logging
from typing import List, Dict, Any
import time
import requests
import json

from .base import BaseEmbeddingModel, EmbeddingModelInfo, EmbeddingModelFactory

logger = logging.getLogger(__name__)

class DeepSeekEmbedding(BaseEmbeddingModel):
    """DeepSeek embedding model implementation"""
    
    MODEL_INFO = {
        'deepseek-embedding': {
            'dimension': 1536,
            'max_tokens': 8192,
            'cost_per_token': 0.00002 / 1000  # Estimated cost
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Initialize DeepSeek configuration
        if not self.api_key:
            raise ValueError("DeepSeek API key is required")
        
        self.base_url = config.get('base_url', 'https://api.deepseek.com/v1')
        self.timeout = config.get('timeout', 30)
        
        # Validate model
        if self.model_name not in self.MODEL_INFO:
            logger.warning(f"Unknown DeepSeek model: {self.model_name}. Using deepseek-embedding")
            self.model_name = 'deepseek-embedding'
        
        logger.info(f"Initialized DeepSeek embedding model: {self.model_name}")
    
    def _make_request(self, texts: List[str]) -> Dict[str, Any]:
        """Make API request to DeepSeek"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model_name,
            'input': texts
        }
        
        response = requests.post(
            f"{self.base_url}/embeddings",
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"DeepSeek API error: {response.status_code} - {response.text}")
        
        return response.json()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        try:
            response_data = self._make_request(texts)
            
            # Extract embeddings from response
            embeddings = []
            for item in response_data.get('data', []):
                embeddings.append(item.get('embedding', []))
            
            logger.debug(f"Generated {len(embeddings)} embeddings using DeepSeek {self.model_name}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating DeepSeek embeddings: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = self.embed_texts([text])
        return embeddings[0] if embeddings else []
    
    def get_model_info(self) -> EmbeddingModelInfo:
        """Get model information"""
        model_config = self.MODEL_INFO.get(self.model_name, self.MODEL_INFO['deepseek-embedding'])
        
        return EmbeddingModelInfo(
            provider='deepseek',
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
                'provider': 'deepseek',
                'model_name': self.model_name,
                'embedding_dimension': len(test_embedding),
                'connection': 'active',
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'deepseek',
                'model_name': self.model_name,
                'error': str(e),
                'connection': 'failed',
                'timestamp': time.time()
            }
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available DeepSeek embedding models"""
        return list(cls.MODEL_INFO.keys())

# Register DeepSeek provider
EmbeddingModelFactory.register_provider('deepseek', DeepSeekEmbedding)