import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import json

# Load .env file if it exists (optional for production deployments)
load_dotenv(override=False)

class Config:
    """Configuration class for the research agent RAG system"""
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Provider Configuration
    DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "openai")
    
    # Model Configuration per Provider
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    
    # Individual Agent Configuration (JSON format in env)
    # Format: {"google_engineer": {"provider": "openai", "model": "gpt-4o"}, ...}
    AGENT_CONFIGS: Dict[str, Dict[str, str]] = {}
    try:
        agent_config_str = os.getenv("AGENT_CONFIGS", "{}")
        AGENT_CONFIGS = json.loads(agent_config_str) if agent_config_str else {}
    except json.JSONDecodeError:
        AGENT_CONFIGS = {}
    
    # Individual Agent Provider/Model Overrides (for simpler env configuration)
    GOOGLE_ENGINEER_PROVIDER: str = os.getenv("GOOGLE_ENGINEER_PROVIDER", "")
    GOOGLE_ENGINEER_MODEL: str = os.getenv("GOOGLE_ENGINEER_MODEL", "")
    MIT_RESEARCHER_PROVIDER: str = os.getenv("MIT_RESEARCHER_PROVIDER", "")
    MIT_RESEARCHER_MODEL: str = os.getenv("MIT_RESEARCHER_MODEL", "")
    INDUSTRY_EXPERT_PROVIDER: str = os.getenv("INDUSTRY_EXPERT_PROVIDER", "")
    INDUSTRY_EXPERT_MODEL: str = os.getenv("INDUSTRY_EXPERT_MODEL", "")
    PAPER_ANALYST_PROVIDER: str = os.getenv("PAPER_ANALYST_PROVIDER", "")
    PAPER_ANALYST_MODEL: str = os.getenv("PAPER_ANALYST_MODEL", "")

    print(os.getenv("POSTGRES_PORT"))
    # ===== DATABASE CONFIGURATION =====
    # PostgreSQL Configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "research_agent")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "research_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "research_password")
    POSTGRES_SSL_MODE: str = os.getenv("POSTGRES_SSL_MODE", "disable")
    POSTGRES_MAX_CONNECTIONS: int = int(os.getenv("POSTGRES_MAX_CONNECTIONS", "20"))
    POSTGRES_CONNECTION_TIMEOUT: int = int(os.getenv("POSTGRES_CONNECTION_TIMEOUT", "30"))
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
    REDIS_CONNECTION_TIMEOUT: int = int(os.getenv("REDIS_CONNECTION_TIMEOUT", "5"))
    REDIS_SOCKET_KEEPALIVE: bool = os.getenv("REDIS_SOCKET_KEEPALIVE", "true").lower() == "true"
    
    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
    CELERY_TASK_SERIALIZER: str = os.getenv("CELERY_TASK_SERIALIZER", "json")
    CELERY_RESULT_SERIALIZER: str = os.getenv("CELERY_RESULT_SERIALIZER", "json")
    CELERY_ACCEPT_CONTENT: str = os.getenv("CELERY_ACCEPT_CONTENT", "json")
    CELERY_TIMEZONE: str = os.getenv("CELERY_TIMEZONE", "UTC")
    CELERY_ENABLE_UTC: bool = os.getenv("CELERY_ENABLE_UTC", "true").lower() == "true"
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = int(os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1"))
    CELERY_TASK_ACKS_LATE: bool = os.getenv("CELERY_TASK_ACKS_LATE", "true").lower() == "true"
    CELERY_RESULT_EXPIRES: int = int(os.getenv("CELERY_RESULT_EXPIRES", "3600"))  # 1 hour
    CELERY_TASK_DEFAULT_RETRY_DELAY: int = int(os.getenv("CELERY_TASK_DEFAULT_RETRY_DELAY", "60"))  # 1 minute
    CELERY_TASK_MAX_RETRIES: int = int(os.getenv("CELERY_TASK_MAX_RETRIES", "3"))
    
    # Vector Database Configuration
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "chroma")  # chroma, pinecone, weaviate, qdrant
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
    VECTOR_DB_COLLECTION: str = os.getenv("VECTOR_DB_COLLECTION", "research-papers")
    
    # Chroma Configuration
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000")) if os.getenv("CHROMA_PORT") else 8000
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "research-papers")
    
    # Pinecone Configuration
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "research-papers")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp-free")
    PINECONE_DIMENSION: int = int(os.getenv("PINECONE_DIMENSION", "384"))
    
    # Weaviate Configuration
    WEAVIATE_HOST: str = os.getenv("WEAVIATE_HOST", "localhost")
    WEAVIATE_PORT: int = int(os.getenv("WEAVIATE_PORT", "8080"))
    WEAVIATE_SCHEME: str = os.getenv("WEAVIATE_SCHEME", "http")
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", f"{WEAVIATE_SCHEME}://{WEAVIATE_HOST}:{WEAVIATE_PORT}")
    WEAVIATE_API_KEY: str = os.getenv("WEAVIATE_API_KEY", "")
    WEAVIATE_CLASS_NAME: str = os.getenv("WEAVIATE_CLASS_NAME", "ResearchPaper")
    
    # Qdrant Configuration
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "research-papers")
    QDRANT_VECTOR_SIZE: int = int(os.getenv("QDRANT_VECTOR_SIZE", "384"))
    
    # Embedding Model Configuration
    EMBEDDING_MODEL_TYPE: str = os.getenv("EMBEDDING_MODEL_TYPE", "openai")  # openai, anthropic, huggingface, deepseek
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    ANTHROPIC_EMBEDDING_MODEL: str = os.getenv("ANTHROPIC_EMBEDDING_MODEL", "claude-3-haiku-20240307")
    HUGGINGFACE_EMBEDDING_MODEL: str = os.getenv("HUGGINGFACE_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    DEEPSEEK_EMBEDDING_MODEL: str = os.getenv("DEEPSEEK_EMBEDDING_MODEL", "deepseek-embedding")
    
    # Processing Configuration
    MAX_PAPERS_PER_QUERY: int = int(os.getenv("MAX_PAPERS_PER_QUERY", "50"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # Search Configuration
    MIN_SIMILARITY_THRESHOLD: float = float(os.getenv("MIN_SIMILARITY_THRESHOLD", "0.5"))
    ENABLE_ARXIV_FALLBACK: bool = os.getenv("ENABLE_ARXIV_FALLBACK", "true").lower() == "true"
    ARXIV_FALLBACK_MAX_PAPERS: int = int(os.getenv("ARXIV_FALLBACK_MAX_PAPERS", "10"))
    
    # Query Expansion Configuration
    ENABLE_QUERY_EXPANSION: bool = os.getenv("ENABLE_QUERY_EXPANSION", "true").lower() == "true"
    MAX_QUERY_EXPANSIONS: int = int(os.getenv("MAX_QUERY_EXPANSIONS", "3"))
    
    # Agent Discussion Configuration
    ENABLE_AGENT_DISCUSSIONS: bool = os.getenv("ENABLE_AGENT_DISCUSSIONS", "true").lower() == "true"
    DEFAULT_SELECTED_AGENTS: str = os.getenv("DEFAULT_SELECTED_AGENTS", "Google Engineer,MIT Researcher,Industry Expert,Paper Analyst")
    
    # Research Parameters
    DEFAULT_MAX_PAPERS: int = int(os.getenv("DEFAULT_MAX_PAPERS", "20"))
    DEFAULT_INCLUDE_RECENT: bool = os.getenv("DEFAULT_INCLUDE_RECENT", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/research_agent.log")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    
    # CORS Configuration
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    
    # Legacy Streamlit Configuration (deprecated)
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    STREAMLIT_HOST: str = os.getenv("STREAMLIT_HOST", "localhost")
    
    @classmethod
    def get_api_key_for_provider(cls, provider: str) -> str:
        """Get API key for a specific provider"""
        if provider == "openai":
            return cls.OPENAI_API_KEY
        elif provider == "deepseek":
            return cls.DEEPSEEK_API_KEY
        elif provider == "anthropic":
            return cls.ANTHROPIC_API_KEY
        else:
            return cls.OPENAI_API_KEY  # Default fallback
    
    @classmethod
    def get_model_for_provider(cls, provider: str) -> str:
        """Get default model for a specific provider"""
        if provider == "openai":
            return cls.OPENAI_MODEL
        elif provider == "deepseek":
            return cls.DEEPSEEK_MODEL
        elif provider == "anthropic":
            return cls.ANTHROPIC_MODEL
        else:
            return cls.OPENAI_MODEL  # Default fallback
    
    @classmethod
    def get_agent_config(cls, agent_name: str) -> Dict[str, str]:
        """Get configuration for a specific agent"""
        # First check individual env vars
        agent_env_vars = {
            "google_engineer": (cls.GOOGLE_ENGINEER_PROVIDER, cls.GOOGLE_ENGINEER_MODEL),
            "mit_researcher": (cls.MIT_RESEARCHER_PROVIDER, cls.MIT_RESEARCHER_MODEL),
            "industry_expert": (cls.INDUSTRY_EXPERT_PROVIDER, cls.INDUSTRY_EXPERT_MODEL),
            "paper_analyst": (cls.PAPER_ANALYST_PROVIDER, cls.PAPER_ANALYST_MODEL)
        }
        
        if agent_name in agent_env_vars:
            provider, model = agent_env_vars[agent_name]
            if provider or model:
                return {
                    "provider": provider or cls.DEFAULT_PROVIDER,
                    "model": model or cls.get_model_for_provider(provider or cls.DEFAULT_PROVIDER)
                }
        
        # Then check AGENT_CONFIGS JSON
        if agent_name in cls.AGENT_CONFIGS:
            config = cls.AGENT_CONFIGS[agent_name].copy()
            # Ensure all required fields are present
            if "provider" not in config:
                config["provider"] = cls.DEFAULT_PROVIDER
            if "model" not in config:
                config["model"] = cls.get_model_for_provider(config["provider"])
            return config
        
        # Default configuration
        return {
            "provider": cls.DEFAULT_PROVIDER,
            "model": cls.get_model_for_provider(cls.DEFAULT_PROVIDER)
        }
    
    @classmethod
    def get_all_agent_configs(cls) -> Dict[str, Dict[str, str]]:
        """Get configurations for all agents"""
        agents = ["google_engineer", "mit_researcher", "industry_expert", "paper_analyst"]
        return {agent: cls.get_agent_config(agent) for agent in agents}
    
    @classmethod
    def get_default_selected_agents(cls) -> list:
        """Get list of default selected agents"""
        return [agent.strip() for agent in cls.DEFAULT_SELECTED_AGENTS.split(",")]
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present"""
        # Check that at least one API key is provided
        if not any([cls.OPENAI_API_KEY, cls.DEEPSEEK_API_KEY, cls.ANTHROPIC_API_KEY]):
            raise ValueError("At least one API key must be provided (OPENAI_API_KEY, DEEPSEEK_API_KEY, or ANTHROPIC_API_KEY)")
        
        # Validate default provider
        valid_providers = ["openai", "deepseek", "anthropic"]
        if cls.DEFAULT_PROVIDER not in valid_providers:
            raise ValueError(f"DEFAULT_PROVIDER must be one of: {valid_providers}")
        
        # Check that API key exists for default provider
        default_key = cls.get_api_key_for_provider(cls.DEFAULT_PROVIDER)
        if not default_key:
            raise ValueError(f"API key for default provider '{cls.DEFAULT_PROVIDER}' is not set")
        
        # Validate agent configurations
        for agent_name, config in cls.get_all_agent_configs().items():
            provider = config.get("provider")
            if provider not in valid_providers:
                raise ValueError(f"Invalid provider '{provider}' for agent '{agent_name}'")
            
            api_key = cls.get_api_key_for_provider(provider)
            if not api_key:
                raise ValueError(f"API key for provider '{provider}' (used by {agent_name}) is not set")
        
        return True
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary for debugging"""
        return {
            "api_keys": {
                "openai": bool(cls.OPENAI_API_KEY),
                "deepseek": bool(cls.DEEPSEEK_API_KEY),
                "anthropic": bool(cls.ANTHROPIC_API_KEY)
            },
            "default_provider": cls.DEFAULT_PROVIDER,
            "models": {
                "openai": cls.OPENAI_MODEL,
                "deepseek": cls.DEEPSEEK_MODEL,
                "anthropic": cls.ANTHROPIC_MODEL
            },
            "agent_configs": cls.get_all_agent_configs(),
            "search": {
                "min_similarity_threshold": cls.MIN_SIMILARITY_THRESHOLD,
                "enable_arxiv_fallback": cls.ENABLE_ARXIV_FALLBACK,
                "enable_query_expansion": cls.ENABLE_QUERY_EXPANSION
            },
            "research": {
                "default_max_papers": cls.DEFAULT_MAX_PAPERS,
                "default_include_recent": cls.DEFAULT_INCLUDE_RECENT
            },
            "database": {
                "postgres": {
                    "host": cls.POSTGRES_HOST,
                    "port": cls.POSTGRES_PORT,
                    "database": cls.POSTGRES_DB,
                    "has_password": bool(cls.POSTGRES_PASSWORD)
                },
                "redis": {
                    "host": cls.REDIS_HOST,
                    "port": cls.REDIS_PORT,
                    "has_password": bool(cls.REDIS_PASSWORD)
                },
                "celery": {
                    "broker_url": cls.CELERY_BROKER_URL,
                    "result_backend": cls.CELERY_RESULT_BACKEND,
                    "task_serializer": cls.CELERY_TASK_SERIALIZER,
                    "result_expires": cls.CELERY_RESULT_EXPIRES,
                    "max_retries": cls.CELERY_TASK_MAX_RETRIES
                },
                "vector_db": {
                    "type": cls.VECTOR_DB_TYPE,
                    "path": cls.VECTOR_DB_PATH,
                    "collection": cls.VECTOR_DB_COLLECTION
                }
            },
            "server": {
                "host": cls.HOST,
                "port": cls.PORT,
                "workers": cls.WORKERS,
                "cors_origins": cls.CORS_ORIGINS
            }
        }
        
    @classmethod
    def get_postgres_url(cls) -> str:
        """Get PostgreSQL connection URL"""
        password_part = f":{cls.POSTGRES_PASSWORD}" if cls.POSTGRES_PASSWORD else ""
        ssl_part = f"?sslmode={cls.POSTGRES_SSL_MODE}" if cls.POSTGRES_SSL_MODE != "disable" else ""
        return f"postgresql://{cls.POSTGRES_USER}{password_part}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}{ssl_part}"
    
    @classmethod
    def get_redis_url(cls) -> str:
        """Get Redis connection URL"""
        password_part = f":{cls.REDIS_PASSWORD}@" if cls.REDIS_PASSWORD else ""
        return f"redis://{password_part}{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
    
    @classmethod
    def get_celery_broker_url(cls) -> str:
        """Get Celery broker URL"""
        return cls.CELERY_BROKER_URL
    
    @classmethod
    def get_celery_result_backend(cls) -> str:
        """Get Celery result backend URL"""
        return cls.CELERY_RESULT_BACKEND