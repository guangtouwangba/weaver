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
    
    # Vector Database
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
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
            }
        }