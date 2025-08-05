#!/usr/bin/env python3
"""
Text embeddings for RAG module
Handles text vectorization using sentence transformers
"""

import logging
import numpy as np
from typing import List, Optional, Dict, Any
import os

try:
    from sentence_transformers import SentenceTransformer
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generates text embeddings for RAG retrieval"""
    
    def __init__(self, provider: str = "sentence-transformers", model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        self.provider = provider
        self.model_name = model_name
        self.device = device
        self.model = None
        self.client = None
        self.embedding_dimension = None
        
        # Validate provider and dependencies
        if provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("openai library is required for OpenAI embeddings. Install with: pip install openai")
        elif provider == "sentence-transformers":
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError("sentence-transformers is required. Install with: pip install sentence-transformers")
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
        
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model based on provider"""
        try:
            logger.info(f"Loading {self.provider} embedding model: {self.model_name}")
            
            if self.provider == "openai":
                self._load_openai_model()
            elif self.provider == "sentence-transformers":
                self._load_sentence_transformer_model()
            
            logger.info(f"Loaded {self.provider} model, embedding dimension: {self.embedding_dimension}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _load_openai_model(self):
        """Load OpenAI embedding model"""
        # Get API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Please set it in your .env file or environment variables. "
                "Example: OPENAI_API_KEY=sk-your-api-key-here"
            )
        
        # Validate API key format
        if not api_key.startswith('sk-'):
            logger.warning("API key format may be incorrect. OpenAI API keys typically start with 'sk-'")
        
        # Initialize OpenAI client
        try:
            self.client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {e}")
        
        # Set embedding dimension based on model
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        
        if self.model_name not in model_dimensions:
            logger.warning(f"Unknown OpenAI embedding model: {self.model_name}. Using default dimension 1536.")
            self.embedding_dimension = 1536
        else:
            self.embedding_dimension = model_dimensions[self.model_name]
        
        # Test the connection with detailed error handling
        try:
            test_response = self.client.embeddings.create(
                model=self.model_name,
                input=["test connection"],
                encoding_format="float"
            )
            logger.info(f"OpenAI embedding model '{self.model_name}' connection test successful")
            
            # Verify the response format
            if not test_response.data or not hasattr(test_response.data[0], 'embedding'):
                raise ValueError("Unexpected response format from OpenAI API")
                
        except openai.AuthenticationError as e:
            raise ValueError(
                f"OpenAI API authentication failed: {e}. "
                "Please check your API key is correct and active."
            )
        except openai.PermissionDeniedError as e:
            raise ValueError(
                f"OpenAI API permission denied: {e}. "
                "Please check your API key has embedding permissions."
            )
        except openai.RateLimitError as e:
            raise ValueError(
                f"OpenAI API rate limit exceeded: {e}. "
                "Please check your API quota and billing."
            )
        except openai.BadRequestError as e:
            if "model" in str(e).lower():
                raise ValueError(
                    f"OpenAI embedding model '{self.model_name}' not found or not accessible. "
                    f"Available models: {list(model_dimensions.keys())}"
                )
            else:
                raise ValueError(f"OpenAI API bad request: {e}")
        except Exception as e:
            raise ValueError(
                f"Failed to connect to OpenAI embedding API: {e}. "
                "Please check your internet connection and API key."
            )
    
    def _load_sentence_transformer_model(self):
        """Load sentence transformer model"""
        # Set device
        if self.device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA not available, falling back to CPU")
            self.device = "cpu"
        
        # Load model
        self.model = SentenceTransformer(self.model_name, device=self.device)
        
        # Get embedding dimension
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
    
    def encode_texts(self, texts: List[str], batch_size: int = 32, show_progress: bool = True) -> np.ndarray:
        """
        Encode list of texts into embeddings
        
        Args:
            texts: List of text strings to encode
            batch_size: Batch size for encoding
            show_progress: Whether to show progress bar
            
        Returns:
            NumPy array of embeddings
        """
        if not texts:
            return np.array([])
        
        try:
            logger.info(f"Encoding {len(texts)} texts with {self.provider} provider")
            
            if self.provider == "openai":
                embeddings = self._encode_texts_openai(texts, batch_size, show_progress)
            elif self.provider == "sentence-transformers":
                embeddings = self._encode_texts_sentence_transformers(texts, batch_size, show_progress)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            logger.info(f"Generated embeddings shape: {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to encode texts: {e}")
            raise
    
    def _encode_texts_openai(self, texts: List[str], batch_size: int, show_progress: bool) -> np.ndarray:
        """Encode texts using OpenAI API"""
        embeddings = []
        
        # Process in batches to respect API limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Retry logic for API calls
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.client.embeddings.create(
                        model=self.model_name,
                        input=batch,
                        encoding_format="float"
                    )
                    
                    batch_embeddings = [data.embedding for data in response.data]
                    embeddings.extend(batch_embeddings)
                    
                    if show_progress and len(texts) > batch_size:
                        logger.info(f"Processed batch {i//batch_size + 1}/{(len(texts) - 1)//batch_size + 1}")
                    
                    break  # Success, exit retry loop
                    
                except openai.RateLimitError as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        import time
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        raise
                        
                except openai.BadRequestError as e:
                    logger.error(f"Bad request for batch {i//batch_size + 1}: {e}")
                    raise
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"API error, retrying in {wait_time}s: {e}")
                        import time
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Failed to encode batch {i//batch_size + 1} after {max_retries} attempts: {e}")
                        raise
        
        # Convert to numpy array and normalize
        embeddings_array = np.array(embeddings)
        
        # L2 normalization for better similarity computation
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        embeddings_array = embeddings_array / norms
        
        return embeddings_array
    
    def _encode_texts_sentence_transformers(self, texts: List[str], batch_size: int, show_progress: bool) -> np.ndarray:
        """Encode texts using sentence transformers"""
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2 normalization for better similarity computation
        )
        
        return embeddings
    
    def encode_single_text(self, text: str) -> np.ndarray:
        """
        Encode a single text into embedding
        
        Args:
            text: Text string to encode
            
        Returns:
            NumPy array embedding
        """
        try:
            if self.provider == "openai":
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=[text],
                    encoding_format="float"
                )
                embedding = np.array(response.data[0].embedding)
                
                # L2 normalization
                norm = np.linalg.norm(embedding)
                embedding = embedding / norm
                
                return embedding
                
            elif self.provider == "sentence-transformers":
                embedding = self.model.encode(
                    [text],
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
                return embedding[0]  # Return single embedding
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
        except Exception as e:
            logger.error(f"Failed to encode single text: {e}")
            raise
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score (0-1)
        """
        try:
            # Since embeddings are normalized, dot product = cosine similarity
            similarity = np.dot(embedding1, embedding2)
            
            # Ensure similarity is in [0, 1] range
            similarity = max(0.0, min(1.0, similarity))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0
    
    def compute_similarities(self, query_embedding: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
        """
        Compute similarities between query embedding and multiple embeddings
        
        Args:
            query_embedding: Query embedding vector
            embeddings: Array of embeddings to compare against
            
        Returns:
            Array of similarity scores
        """
        try:
            if embeddings.ndim == 1:
                embeddings = embeddings.reshape(1, -1)
            
            # Compute dot product (cosine similarity for normalized vectors)
            similarities = np.dot(embeddings, query_embedding)
            
            # Ensure similarities are in [0, 1] range
            similarities = np.clip(similarities, 0.0, 1.0)
            
            return similarities
            
        except Exception as e:
            logger.error(f"Failed to compute similarities: {e}")
            return np.array([])
    
    def get_top_k_similar(self, query_embedding: np.ndarray, embeddings: np.ndarray, 
                         k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Get top-k most similar embeddings to query
        
        Args:
            query_embedding: Query embedding vector
            embeddings: Array of embeddings to search
            k: Number of top results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of dictionaries with indices and similarity scores
        """
        try:
            similarities = self.compute_similarities(query_embedding, embeddings)
            
            # Filter by threshold
            valid_indices = np.where(similarities >= threshold)[0]
            
            if len(valid_indices) == 0:
                return []
            
            # Get top-k indices
            valid_similarities = similarities[valid_indices]
            top_k_indices = np.argsort(valid_similarities)[::-1][:k]
            
            # Format results
            results = []
            for i in top_k_indices:
                original_index = valid_indices[i]
                results.append({
                    'index': int(original_index),
                    'similarity': float(valid_similarities[i])
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get top-k similar: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding model
        
        Returns:
            Dictionary with model information
        """
        info = {
            'provider': self.provider,
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dimension,
        }
        
        if self.provider == "sentence-transformers":
            info.update({
                'device': self.device,
                'max_sequence_length': getattr(self.model, 'max_seq_length', None)
            })
        elif self.provider == "openai":
            # OpenAI specific info
            max_tokens = {
                "text-embedding-3-small": 8191,
                "text-embedding-3-large": 8191,
                "text-embedding-ada-002": 8191
            }
            info.update({
                'max_tokens': max_tokens.get(self.model_name, 8191),
                'api_based': True
            })
        
        return info
    
    def preprocess_text(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Preprocess text before embedding
        
        Args:
            text: Input text
            max_length: Maximum text length (characters)
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
        
        # Basic cleaning
        text = text.strip()
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Truncate if too long
        if max_length and len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + "..."
            logger.debug(f"Truncated text to {len(text)} characters")
        
        return text
    
    def batch_encode_with_metadata(self, text_metadata_pairs: List[Dict[str, Any]], 
                                 batch_size: int = 32) -> List[Dict[str, Any]]:
        """
        Encode texts with metadata preservation
        
        Args:
            text_metadata_pairs: List of dicts with 'text' and other metadata
            batch_size: Batch size for encoding
            
        Returns:
            List of dicts with embeddings and metadata
        """
        if not text_metadata_pairs:
            return []
        
        try:
            # Extract texts
            texts = [item.get('text', '') for item in text_metadata_pairs]
            
            # Preprocess texts
            processed_texts = [self.preprocess_text(text) for text in texts]
            
            # Generate embeddings
            embeddings = self.encode_texts(processed_texts, batch_size=batch_size)
            
            # Combine with metadata
            results = []
            for i, (item, embedding) in enumerate(zip(text_metadata_pairs, embeddings)):
                result = item.copy()
                result['embedding'] = embedding
                result['processed_text'] = processed_texts[i]
                results.append(result)
            
            logger.info(f"Encoded {len(results)} texts with metadata")
            return results
            
        except Exception as e:
            logger.error(f"Failed to batch encode with metadata: {e}")
            return []
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate number of tokens in text (rough approximation)
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters for English text
        return len(text) // 4