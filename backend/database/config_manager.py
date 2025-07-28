"""
Multi-provider configuration management for vector databases and embedding models
"""
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from database.database import get_session
from database.models import VectorDBConfig, EmbeddingConfig
from database.vector_db import VectorDBFactory
from database.embeddings import EmbeddingModelFactory

logger = logging.getLogger(__name__)

@dataclass
class ProviderConfig:
    """Configuration for a provider"""
    name: str
    provider: str
    config: Dict[str, Any]
    is_default: bool = False

class ConfigManager:
    """Manages configuration for vector databases and embedding models"""
    
    def __init__(self):
        # Cache for loaded configurations
        self._vector_db_configs = {}
        self._embedding_configs = {}
        self._default_vector_db = None
        self._default_embedding = None
    
    def load_vector_db_configs(self) -> Dict[str, ProviderConfig]:
        """Load vector database configurations from database"""
        try:
            with get_session() as session:
                configs = session.query(VectorDBConfig).all()
                
                self._vector_db_configs = {}
                for config in configs:
                    provider_config = ProviderConfig(
                        name=config.name,
                        provider=config.provider,
                        config=config.config,
                        is_default=config.is_default
                    )
                    self._vector_db_configs[config.name] = provider_config
                    
                    if config.is_default:
                        self._default_vector_db = config.name
                
                logger.info(f"Loaded {len(self._vector_db_configs)} vector DB configurations")
                return self._vector_db_configs.copy()
                
        except Exception as e:
            logger.error(f"Error loading vector DB configurations: {e}")
            return self._get_default_vector_db_configs()
    
    def load_embedding_configs(self) -> Dict[str, ProviderConfig]:
        """Load embedding model configurations from database"""
        try:
            with get_session() as session:
                configs = session.query(EmbeddingConfig).all()
                
                self._embedding_configs = {}
                for config in configs:
                    provider_config = ProviderConfig(
                        name=config.name,
                        provider=config.provider,
                        config={
                            'model_name': config.model_name,
                            **config.config
                        },
                        is_default=config.is_default
                    )
                    self._embedding_configs[config.name] = provider_config
                    
                    if config.is_default:
                        self._default_embedding = config.name
                
                logger.info(f"Loaded {len(self._embedding_configs)} embedding configurations")
                return self._embedding_configs.copy()
                
        except Exception as e:
            logger.error(f"Error loading embedding configurations: {e}")
            return self._get_default_embedding_configs()
    
    def _get_default_vector_db_configs(self) -> Dict[str, ProviderConfig]:
        """Get default vector database configurations from environment"""
        configs = {}
        
        # ChromaDB default configuration
        chroma_config = ProviderConfig(
            name="default_chroma",
            provider="chroma",
            config={
                "db_path": os.getenv("VECTOR_DB_PATH", "./data/vector_db"),
                "collection_name": os.getenv("VECTOR_DB_COLLECTION", "research_papers"),
                "host": os.getenv("CHROMA_HOST"),
                "port": int(os.getenv("CHROMA_PORT", 8000)) if os.getenv("CHROMA_PORT") else None
            },
            is_default=True
        )
        configs["default_chroma"] = chroma_config
        
        # Pinecone configuration if API key is available
        if os.getenv("PINECONE_API_KEY"):
            pinecone_config = ProviderConfig(
                name="default_pinecone",
                provider="pinecone",
                config={
                    "api_key": os.getenv("PINECONE_API_KEY"),
                    "index_name": os.getenv("PINECONE_INDEX_NAME", "research-papers"),
                    "environment": os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp"),
                    "dimension": int(os.getenv("PINECONE_DIMENSION", 384))
                },
                is_default=False
            )
            configs["default_pinecone"] = pinecone_config
        
        # Weaviate configuration if URL is available
        if os.getenv("WEAVIATE_URL"):
            weaviate_config = ProviderConfig(
                name="default_weaviate",
                provider="weaviate",
                config={
                    "url": os.getenv("WEAVIATE_URL"),
                    "api_key": os.getenv("WEAVIATE_API_KEY"),
                    "class_name": os.getenv("WEAVIATE_CLASS_NAME", "ResearchPaper")
                },
                is_default=False
            )
            configs["default_weaviate"] = weaviate_config
        
        # Qdrant configuration if host is available
        if os.getenv("QDRANT_HOST"):
            qdrant_config = ProviderConfig(
                name="default_qdrant",
                provider="qdrant",
                config={
                    "host": os.getenv("QDRANT_HOST", "localhost"),
                    "port": int(os.getenv("QDRANT_PORT", 6333)),
                    "api_key": os.getenv("QDRANT_API_KEY"),
                    "collection_name": os.getenv("QDRANT_COLLECTION", "research-papers"),
                    "vector_size": int(os.getenv("QDRANT_VECTOR_SIZE", 384))
                },
                is_default=False
            )
            configs["default_qdrant"] = qdrant_config
        
        self._vector_db_configs = configs
        self._default_vector_db = "default_chroma"
        return configs
    
    def _get_default_embedding_configs(self) -> Dict[str, ProviderConfig]:
        """Get default embedding model configurations from environment"""
        configs = {}
        
        # OpenAI configuration if API key is available
        if os.getenv("OPENAI_API_KEY"):
            openai_config = ProviderConfig(
                name="default_openai",
                provider="openai",
                config={
                    "model_name": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "batch_size": int(os.getenv("OPENAI_BATCH_SIZE", 100))
                },
                is_default=True
            )
            configs["default_openai"] = openai_config
        
        # DeepSeek configuration if API key is available
        if os.getenv("DEEPSEEK_API_KEY"):
            deepseek_config = ProviderConfig(
                name="default_deepseek",
                provider="deepseek",
                config={
                    "model_name": os.getenv("DEEPSEEK_EMBEDDING_MODEL", "deepseek-embedding"),
                    "api_key": os.getenv("DEEPSEEK_API_KEY"),
                    "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                    "batch_size": int(os.getenv("DEEPSEEK_BATCH_SIZE", 100))
                },
                is_default=not os.getenv("OPENAI_API_KEY")  # Default if no OpenAI
            )
            configs["default_deepseek"] = deepseek_config
        
        # HuggingFace default configuration (always available)
        huggingface_config = ProviderConfig(
            name="default_huggingface",
            provider="huggingface",
            config={
                "model_name": os.getenv("HUGGINGFACE_MODEL", "all-MiniLM-L6-v2"),
                "batch_size": int(os.getenv("HUGGINGFACE_BATCH_SIZE", 32))
            },
            is_default=not (os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY"))
        )
        configs["default_huggingface"] = huggingface_config
        
        # Anthropic configuration if API key is available
        if os.getenv("ANTHROPIC_API_KEY"):
            anthropic_config = ProviderConfig(
                name="default_anthropic",
                provider="anthropic",
                config={
                    "model_name": os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
                    "api_key": os.getenv("ANTHROPIC_API_KEY"),
                    "batch_size": int(os.getenv("ANTHROPIC_BATCH_SIZE", 50))
                },
                is_default=False
            )
            configs["default_anthropic"] = anthropic_config
        
        self._embedding_configs = configs
        # Set default embedding
        for name, config in configs.items():
            if config.is_default:
                self._default_embedding = name
                break
        else:
            # If no default found, use the first available
            if configs:
                first_name = list(configs.keys())[0]
                configs[first_name].is_default = True
                self._default_embedding = first_name
        
        return configs
    
    def get_vector_db_instance(self, config_name: Optional[str] = None):
        """Get a vector database instance"""
        if not self._vector_db_configs:
            self.load_vector_db_configs()
        
        # Use default if no config specified
        if config_name is None:
            config_name = self._default_vector_db
        
        if config_name not in self._vector_db_configs:
            raise ValueError(f"Vector DB configuration '{config_name}' not found")
        
        config = self._vector_db_configs[config_name]
        return VectorDBFactory.create(config.provider, config.config)
    
    def get_embedding_model_instance(self, config_name: Optional[str] = None):
        """Get an embedding model instance"""
        if not self._embedding_configs:
            self.load_embedding_configs()
        
        # Use default if no config specified
        if config_name is None:
            config_name = self._default_embedding
        
        if config_name not in self._embedding_configs:
            raise ValueError(f"Embedding configuration '{config_name}' not found")
        
        config = self._embedding_configs[config_name]
        model_name = config.config.pop('model_name', 'default')
        return EmbeddingModelFactory.create(config.provider, model_name, config.config)
    
    def save_vector_db_config(self, name: str, provider: str, config: Dict[str, Any], 
                             is_default: bool = False) -> bool:
        """Save vector database configuration to database"""
        try:
            with get_session() as session:
                # Check if config exists
                existing_config = session.query(VectorDBConfig).filter_by(name=name).first()
                
                if existing_config:
                    # Update existing
                    existing_config.provider = provider
                    existing_config.config = config
                    existing_config.is_default = is_default
                else:
                    # Create new
                    new_config = VectorDBConfig(
                        name=name,
                        provider=provider,
                        config=config,
                        is_default=is_default
                    )
                    session.add(new_config)
                
                # If this is set as default, unset others
                if is_default:
                    session.query(VectorDBConfig).filter(VectorDBConfig.name != name).update(
                        {"is_default": False}
                    )
                
                session.commit()
                logger.info(f"Saved vector DB configuration: {name}")
                
                # Reload configurations
                self.load_vector_db_configs()
                return True
                
        except Exception as e:
            logger.error(f"Error saving vector DB configuration: {e}")
            return False
    
    def save_embedding_config(self, name: str, provider: str, model_name: str, 
                             config: Dict[str, Any], is_default: bool = False) -> bool:
        """Save embedding model configuration to database"""
        try:
            with get_session() as session:
                # Check if config exists
                existing_config = session.query(EmbeddingConfig).filter_by(name=name).first()
                
                if existing_config:
                    # Update existing
                    existing_config.provider = provider
                    existing_config.model_name = model_name
                    existing_config.config = config
                    existing_config.is_default = is_default
                else:
                    # Create new
                    new_config = EmbeddingConfig(
                        name=name,
                        provider=provider,
                        model_name=model_name,
                        config=config,
                        is_default=is_default
                    )
                    session.add(new_config)
                
                # If this is set as default, unset others
                if is_default:
                    session.query(EmbeddingConfig).filter(EmbeddingConfig.name != name).update(
                        {"is_default": False}
                    )
                
                session.commit()
                logger.info(f"Saved embedding configuration: {name}")
                
                # Reload configurations
                self.load_embedding_configs()
                return True
                
        except Exception as e:
            logger.error(f"Error saving embedding configuration: {e}")
            return False
    
    def get_available_providers(self) -> Dict[str, List[str]]:
        """Get available providers for vector databases and embeddings"""
        return {
            'vector_db': VectorDBFactory.get_available_providers(),
            'embedding': EmbeddingModelFactory.get_available_providers()
        }
    
    def test_configuration(self, config_type: str, config_name: str) -> Dict[str, Any]:
        """Test a configuration"""
        try:
            if config_type == 'vector_db':
                instance = self.get_vector_db_instance(config_name)
                return instance.health_check()
            elif config_type == 'embedding':
                instance = self.get_embedding_model_instance(config_name)
                return instance.health_check()
            else:
                return {'status': 'error', 'message': f'Unknown config type: {config_type}'}
                
        except Exception as e:
            return {
                'status': 'error', 
                'message': str(e),
                'config_type': config_type,
                'config_name': config_name
            }

# Global configuration manager instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager