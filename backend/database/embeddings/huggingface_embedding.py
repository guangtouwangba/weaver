"""
HuggingFace embedding model implementation
"""
import logging
from typing import List, Dict, Any
import time
import os

try:
    from sentence_transformers import SentenceTransformer
    import torch
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False

from .base import BaseEmbeddingModel, EmbeddingModelInfo, EmbeddingModelFactory

logger = logging.getLogger(__name__)

class HuggingFaceEmbedding(BaseEmbeddingModel):
    """HuggingFace sentence-transformers embedding model implementation"""
    
    MODEL_INFO = {
        'all-MiniLM-L6-v2': {
            'dimension': 384,
            'max_tokens': 512,
            'cost_per_token': 0.0  # Free
        },
        'all-mpnet-base-v2': {
            'dimension': 768,
            'max_tokens': 512,
            'cost_per_token': 0.0  # Free
        },
        'all-MiniLM-L12-v2': {
            'dimension': 384,
            'max_tokens': 512,
            'cost_per_token': 0.0  # Free
        },
        'paraphrase-multilingual-MiniLM-L12-v2': {
            'dimension': 384,
            'max_tokens': 512,
            'cost_per_token': 0.0  # Free
        },
        'sentence-transformers/all-roberta-large-v1': {
            'dimension': 1024,
            'max_tokens': 512,
            'cost_per_token': 0.0  # Free
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        if not HUGGINGFACE_AVAILABLE:
            raise ImportError("HuggingFace sentence-transformers is not installed. "
                            "Install with: pip install sentence-transformers")
        
        super().__init__(config)
        
        # Configure environment to avoid PyTorch issues
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        # Validate model
        if self.model_name not in self.MODEL_INFO:
            logger.warning(f"Unknown HuggingFace model: {self.model_name}. Using all-MiniLM-L6-v2")
            self.model_name = 'all-MiniLM-L6-v2'
        
        # Initialize model
        try:
            # Set default device to CPU to avoid meta tensor issues
            if 'torch' in globals():
                torch.set_default_device('cpu')
            
            self.model = SentenceTransformer(self.model_name)
            
            logger.info(f"Successfully initialized HuggingFace model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace model {self.model_name}: {e}")
            # Fallback to CPU
            try:
                if 'torch' in globals():
                    torch.set_default_device('cpu')
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Fallback initialization succeeded for {self.model_name}")
            except Exception as e2:
                logger.error(f"All HuggingFace model initialization attempts failed: {e2}")
                raise RuntimeError(f"Cannot initialize HuggingFace model: {e2}") from e2
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            
            # Convert to list of lists
            if isinstance(embeddings, list):
                embeddings_list = [emb.tolist() if hasattr(emb, 'tolist') else emb for emb in embeddings]
            else:
                embeddings_list = embeddings.tolist()
            
            logger.debug(f"Generated {len(embeddings_list)} embeddings using HuggingFace {self.model_name}")
            return embeddings_list
            
        except Exception as e:
            logger.error(f"Error generating HuggingFace embeddings: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            embedding = self.model.encode([text], convert_to_tensor=False)
            
            # Convert to list
            if isinstance(embedding, list):
                result = embedding[0].tolist() if hasattr(embedding[0], 'tolist') else embedding[0]
            else:
                result = embedding.tolist()[0]
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating single HuggingFace embedding: {e}")
            raise
    
    def get_model_info(self) -> EmbeddingModelInfo:
        """Get model information"""
        model_config = self.MODEL_INFO.get(self.model_name, self.MODEL_INFO['all-MiniLM-L6-v2'])
        
        return EmbeddingModelInfo(
            provider='huggingface',
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
                'provider': 'huggingface',
                'model_name': self.model_name,
                'embedding_dimension': len(test_embedding),
                'device': str(self.model.device) if hasattr(self.model, 'device') else 'unknown',
                'connection': 'active',
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'huggingface',
                'model_name': self.model_name,
                'error': str(e),
                'connection': 'failed',
                'timestamp': time.time()
            }
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available HuggingFace embedding models"""
        return list(cls.MODEL_INFO.keys())

# Register HuggingFace provider if available
if HUGGINGFACE_AVAILABLE:
    EmbeddingModelFactory.register_provider('huggingface', HuggingFaceEmbedding)
else:
    logger.warning("HuggingFace sentence-transformers not available. "
                  "Install with: pip install sentence-transformers")