"""
Advanced Embedding System

Multi-model embedding management with support for different content types,
languages, and specialized domains.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import logging
import hashlib
import json
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class EmbeddingModelType(str, Enum):
    """Embedding model types"""
    TEXT_CHINESE = "text_zh"
    TEXT_ENGLISH = "text_en"
    TEXT_MULTILINGUAL = "text_multilingual"
    CODE = "code"
    MATH = "math"
    MULTIMODAL = "multimodal"

class ContentType(str, Enum):
    """Content type detection"""
    TEXT = "text"
    CODE = "code"
    MATH = "math"
    TABLE = "table"
    LIST = "list"
    MIXED = "mixed"

@dataclass
class EmbeddingResult:
    """Embedding result with metadata"""
    text: str
    embedding: List[float]
    model_used: str
    content_type: ContentType
    language: Optional[str] = None
    confidence: float = 1.0
    processing_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class EmbeddingConfig:
    """Embedding configuration"""
    model_name: str
    model_type: EmbeddingModelType
    dimension: int
    max_length: int = 512
    batch_size: int = 32
    normalize: bool = True
    device: str = "cuda"

class IEmbeddingModel(ABC):
    """Abstract embedding model interface"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the model"""
        pass
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        pass
    
    @abstractmethod
    def get_max_length(self) -> int:
        """Get maximum input length"""
        pass

class BGEEmbedding(IEmbeddingModel):
    """BGE embedding model implementation"""
    
    def __init__(self, model_name: str = "BAAI/bge-large-zh-v1.5",
                 device: str = "cuda", normalize: bool = True):
        self.model_name = model_name
        self.device = device
        self.normalize = normalize
        self.model = None
        self.tokenizer = None
        self._initialized = False
        self._dimension = None
        self._max_length = 512
    
    async def initialize(self) -> None:
        """Initialize BGE model"""
        try:
            from sentence_transformers import SentenceTransformer
            
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self._dimension = self.model.get_sentence_embedding_dimension()
            self._max_length = self.model.max_seq_length
            self._initialized = True
            
            logger.info(f"BGE model {self.model_name} initialized successfully")
            logger.info(f"Dimension: {self._dimension}, Max length: {self._max_length}")
            
        except ImportError:
            raise ImportError("sentence-transformers package is required for BGEEmbedding")
        except Exception as e:
            logger.error(f"Failed to initialize BGE model: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Truncate text if too long
            if len(text) > self._max_length:
                text = text[:self._max_length]
            
            embedding = self.model.encode([text], normalize_embeddings=self.normalize)[0]
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Truncate texts if too long
            truncated_texts = []
            for text in texts:
                if len(text) > self._max_length:
                    truncated_texts.append(text[:self._max_length])
                else:
                    truncated_texts.append(text)
            
            embeddings = self.model.encode(
                truncated_texts, 
                normalize_embeddings=self.normalize,
                batch_size=32
            )
            return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension or 1024
    
    def get_max_length(self) -> int:
        """Get maximum input length"""
        return self._max_length

class OpenAIEmbedding(IEmbeddingModel):
    """OpenAI embedding model implementation"""
    
    def __init__(self, model_name: str = "text-embedding-ada-002",
                 api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key
        self.client = None
        self._initialized = False
        self._dimension = 1536  # ada-002 dimension
        self._max_length = 8191  # ada-002 max tokens
    
    async def initialize(self) -> None:
        """Initialize OpenAI client"""
        try:
            import openai
            
            if self.api_key:
                openai.api_key = self.api_key
            
            self.client = openai.OpenAI(api_key=self.api_key)
            self._initialized = True
            
            logger.info(f"OpenAI embedding model {self.model_name} initialized")
            
        except ImportError:
            raise ImportError("openai package is required for OpenAIEmbedding")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        if not self._initialized:
            await self.initialize()
        
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=[text]
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Failed to generate OpenAI embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        if not self._initialized:
            await self.initialize()
        
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            return [item.embedding for item in response.data]
            
        except Exception as e:
            logger.error(f"Failed to generate OpenAI batch embeddings: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension
    
    def get_max_length(self) -> int:
        """Get maximum input length"""
        return self._max_length

class ContentAnalyzer:
    """Content type and language analyzer"""
    
    def __init__(self):
        self.code_patterns = [
            r'def\s+\w+\s*\(',  # Python function
            r'function\s+\w+\s*\(',  # JavaScript function
            r'class\s+\w+\s*{',  # Class definition
            r'import\s+[\w\.,\s]+',  # Import statements
            r'#include\s*<.*>',  # C/C++ includes
            r'package\s+\w+',  # Java/Go package
        ]
        
        self.math_patterns = [
            r'\$.*\$',  # LaTeX math
            r'\\[a-zA-Z]+{',  # LaTeX commands
            r'[∑∏∫∂∇∞±×÷≤≥≠≈∈∉⊂⊃∪∩]',  # Math symbols
            r'\^\d+',  # Superscripts
            r'_\{[^}]+\}',  # Subscripts
        ]
        
        self.chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        self.english_pattern = re.compile(r'[a-zA-Z]+')
    
    def analyze_content_type(self, text: str) -> ContentType:
        """Analyze content type"""
        # Check for code patterns
        for pattern in self.code_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return ContentType.CODE
        
        # Check for math patterns
        for pattern in self.math_patterns:
            if re.search(pattern, text):
                return ContentType.MATH
        
        # Check for table structure
        if '|' in text and text.count('|') > 4:
            lines = text.split('\n')
            if sum(1 for line in lines if '|' in line) > len(lines) * 0.5:
                return ContentType.TABLE
        
        # Check for list structure
        list_markers = [r'^\s*[-*+]\s', r'^\s*\d+\.\s', r'^\s*[a-zA-Z]\.\s']
        if any(re.search(pattern, text, re.MULTILINE) for pattern in list_markers):
            return ContentType.LIST
        
        return ContentType.TEXT
    
    def detect_language(self, text: str) -> str:
        """Detect primary language"""
        chinese_chars = len(self.chinese_pattern.findall(text))
        english_chars = len(self.english_pattern.findall(text))
        
        if chinese_chars > english_chars:
            return "zh"
        elif english_chars > chinese_chars:
            return "en"
        else:
            return "mixed"
    
    def calculate_complexity(self, text: str) -> float:
        """Calculate text complexity score"""
        # Simple complexity based on sentence length, vocabulary diversity
        sentences = text.split('.')
        avg_sentence_length = np.mean([len(s.split()) for s in sentences if s.strip()])
        
        words = text.split()
        unique_words = set(words)
        vocabulary_diversity = len(unique_words) / len(words) if words else 0
        
        complexity = (avg_sentence_length / 20.0 + vocabulary_diversity) / 2
        return min(complexity, 1.0)

class MultiModelEmbedding:
    """Multi-model embedding manager"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.models = {}
        self.content_analyzer = ContentAnalyzer()
        self._initialized = False
        
        # Default model configurations
        self.model_configs = {
            EmbeddingModelType.TEXT_CHINESE: EmbeddingConfig(
                model_name="BAAI/bge-large-zh-v1.5",
                model_type=EmbeddingModelType.TEXT_CHINESE,
                dimension=1024
            ),
            EmbeddingModelType.TEXT_ENGLISH: EmbeddingConfig(
                model_name="BAAI/bge-large-en-v1.5",
                model_type=EmbeddingModelType.TEXT_ENGLISH,
                dimension=1024
            ),
            EmbeddingModelType.TEXT_MULTILINGUAL: EmbeddingConfig(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                model_type=EmbeddingModelType.TEXT_MULTILINGUAL,
                dimension=384
            )
        }
    
    async def initialize(self) -> None:
        """Initialize all embedding models"""
        try:
            # Initialize Chinese text model
            self.models[EmbeddingModelType.TEXT_CHINESE] = BGEEmbedding(
                self.model_configs[EmbeddingModelType.TEXT_CHINESE].model_name,
                device=self.config.get("device", "cuda")
            )
            
            # Initialize English text model
            self.models[EmbeddingModelType.TEXT_ENGLISH] = BGEEmbedding(
                self.model_configs[EmbeddingModelType.TEXT_ENGLISH].model_name,
                device=self.config.get("device", "cuda")
            )
            
            # Initialize multilingual model as fallback
            self.models[EmbeddingModelType.TEXT_MULTILINGUAL] = BGEEmbedding(
                self.model_configs[EmbeddingModelType.TEXT_MULTILINGUAL].model_name,
                device=self.config.get("device", "cuda")
            )
            
            # Initialize models
            for model in self.models.values():
                await model.initialize()
            
            self._initialized = True
            logger.info("Multi-model embedding system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding models: {e}")
            raise
    
    def select_model(self, text: str) -> Tuple[IEmbeddingModel, EmbeddingModelType]:
        """Select the best model for given text"""
        content_type = self.content_analyzer.analyze_content_type(text)
        language = self.content_analyzer.detect_language(text)
        
        # Model selection logic
        if content_type == ContentType.CODE:
            # For code, prefer English model
            return self.models[EmbeddingModelType.TEXT_ENGLISH], EmbeddingModelType.TEXT_ENGLISH
        elif content_type == ContentType.MATH:
            # For math, prefer English model
            return self.models[EmbeddingModelType.TEXT_ENGLISH], EmbeddingModelType.TEXT_ENGLISH
        elif language == "zh":
            # Chinese text
            return self.models[EmbeddingModelType.TEXT_CHINESE], EmbeddingModelType.TEXT_CHINESE
        elif language == "en":
            # English text
            return self.models[EmbeddingModelType.TEXT_ENGLISH], EmbeddingModelType.TEXT_ENGLISH
        else:
            # Mixed or unknown language, use multilingual
            return self.models[EmbeddingModelType.TEXT_MULTILINGUAL], EmbeddingModelType.TEXT_MULTILINGUAL
    
    async def embed_text(self, text: str) -> EmbeddingResult:
        """Generate embedding for single text with optimal model"""
        if not self._initialized:
            await self.initialize()
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Analyze content
            content_type = self.content_analyzer.analyze_content_type(text)
            language = self.content_analyzer.detect_language(text)
            
            # Select model
            model, model_type = self.select_model(text)
            
            # Generate embedding
            embedding = await model.embed_text(text)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return EmbeddingResult(
                text=text,
                embedding=embedding,
                model_used=model_type.value,
                content_type=content_type,
                language=language,
                confidence=1.0,
                processing_time=processing_time,
                metadata={
                    "text_length": len(text),
                    "embedding_dimension": len(embedding),
                    "complexity": self.content_analyzer.calculate_complexity(text)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for batch of texts"""
        if not self._initialized:
            await self.initialize()
        
        # Group texts by optimal model
        model_groups = {}
        text_indices = {}
        
        for i, text in enumerate(texts):
            model, model_type = self.select_model(text)
            if model_type not in model_groups:
                model_groups[model_type] = []
                text_indices[model_type] = []
            
            model_groups[model_type].append(text)
            text_indices[model_type].append(i)
        
        # Process each group
        results = [None] * len(texts)
        
        for model_type, grouped_texts in model_groups.items():
            model = self.models[model_type]
            embeddings = await model.embed_batch(grouped_texts)
            
            for j, (text, embedding) in enumerate(zip(grouped_texts, embeddings)):
                original_index = text_indices[model_type][j]
                
                content_type = self.content_analyzer.analyze_content_type(text)
                language = self.content_analyzer.detect_language(text)
                
                results[original_index] = EmbeddingResult(
                    text=text,
                    embedding=embedding,
                    model_used=model_type.value,
                    content_type=content_type,
                    language=language,
                    confidence=1.0,
                    processing_time=0.0,  # Not measured for batch
                    metadata={
                        "text_length": len(text),
                        "embedding_dimension": len(embedding),
                        "complexity": self.content_analyzer.calculate_complexity(text)
                    }
                )
        
        return results
    
    def get_model_info(self, model_type: EmbeddingModelType) -> Dict[str, Any]:
        """Get model information"""
        if model_type in self.models:
            model = self.models[model_type]
            return {
                "model_type": model_type.value,
                "dimension": model.get_dimension(),
                "max_length": model.get_max_length(),
                "initialized": hasattr(model, '_initialized') and model._initialized
            }
        return {}
    
    def get_all_models_info(self) -> Dict[str, Any]:
        """Get information about all models"""
        return {
            model_type.value: self.get_model_info(model_type)
            for model_type in self.models.keys()
        }

class EmbeddingManager:
    """High-level embedding management with caching and optimization"""
    
    def __init__(self, cache_config: Optional[Dict[str, Any]] = None):
        self.multi_model = MultiModelEmbedding()
        self.cache_config = cache_config or {}
        self.cache = None
        self._setup_cache()
    
    def _setup_cache(self):
        """Setup embedding cache"""
        if self.cache_config.get("enabled", True):
            try:
                import redis
                self.cache = redis.Redis(
                    host=self.cache_config.get("host", "localhost"),
                    port=self.cache_config.get("port", 6379),
                    db=self.cache_config.get("db", 1),
                    decode_responses=False
                )
                logger.info("Embedding cache initialized")
            except ImportError:
                logger.warning("Redis not available, caching disabled")
            except Exception as e:
                logger.warning(f"Failed to initialize embedding cache: {e}")
    
    def _generate_cache_key(self, text: str, model_type: str) -> str:
        """Generate cache key for text and model"""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"embedding:{model_type}:{text_hash}"
    
    async def get_or_create_embedding(self, text: str, 
                                    force_model: Optional[EmbeddingModelType] = None) -> EmbeddingResult:
        """Get embedding from cache or create new one"""
        
        # Determine model type
        if force_model:
            model_type = force_model
        else:
            _, model_type = self.multi_model.select_model(text)
        
        # Check cache first
        if self.cache:
            cache_key = self._generate_cache_key(text, model_type.value)
            try:
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    cached_data = json.loads(cached_result.decode('utf-8'))
                    return EmbeddingResult(**cached_data)
            except Exception as e:
                logger.warning(f"Failed to retrieve from cache: {e}")
        
        # Generate new embedding
        result = await self.multi_model.embed_text(text)
        
        # Cache the result
        if self.cache:
            try:
                cache_key = self._generate_cache_key(text, result.model_used)
                cache_data = {
                    "text": result.text,
                    "embedding": result.embedding,
                    "model_used": result.model_used,
                    "content_type": result.content_type.value,
                    "language": result.language,
                    "confidence": result.confidence,
                    "processing_time": result.processing_time,
                    "metadata": result.metadata
                }
                
                self.cache.setex(
                    cache_key,
                    self.cache_config.get("ttl", 86400),  # 24 hours default
                    json.dumps(cache_data)
                )
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")
        
        return result
    
    async def initialize(self) -> None:
        """Initialize embedding manager"""
        await self.multi_model.initialize()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Test embedding generation
            test_text = "This is a test sentence for health check."
            result = await self.get_or_create_embedding(test_text)
            
            cache_status = "enabled" if self.cache else "disabled"
            if self.cache:
                try:
                    self.cache.ping()
                    cache_status = "healthy"
                except:
                    cache_status = "unhealthy"
            
            return {
                "status": "healthy",
                "models": self.multi_model.get_all_models_info(),
                "cache_status": cache_status,
                "test_embedding_dimension": len(result.embedding),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }