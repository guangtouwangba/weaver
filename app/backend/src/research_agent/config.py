"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


# Find .env file - check multiple locations
def find_env_file() -> str:
    """Find .env file in current dir or parent dirs."""

    candidates = []

    # Current working directory
    cwd = Path.cwd()
    candidates.append(cwd / ".env")

    # Project root (2 levels up from app/backend when running from there)
    candidates.append((cwd / ".." / ".." / ".env").resolve())

    # Based on this file's location
    # __file__ is in app/backend/src/research_agent/config.py
    this_file = Path(__file__).resolve()
    # Go up: config.py -> research_agent -> src -> backend -> app -> project_root
    project_root = this_file.parent.parent.parent.parent.parent
    candidates.append(project_root / ".env")
    candidates.append(project_root / "app" / "backend" / ".env")

    # Check each candidate
    for candidate in candidates:
        if candidate.exists():
            return str(candidate.resolve())

    # Fallback - return first candidate path for error message
    return str(candidates[0])


_env_file_path = find_env_file()
_env_file_exists = Path(_env_file_path).exists()
if _env_file_exists:
    print(f"[Config] Loading .env from: {_env_file_path}")
else:
    # This is normal in production - Zeabur/Docker uses environment variables directly
    print("[Config] No .env file found (using environment variables instead)")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=_env_file_path,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
    )

    # Database
    database_url: str = (
        "postgresql+asyncpg://research_rag:research_rag_dev@localhost:5432/research_rag"
    )

    # Database Client Type
    # "postgres" - Direct PostgreSQL connection (default for local development)
    # "supabase" - Supabase SDK (for production/cloud)
    # "sqlalchemy" - SQLAlchemy wrapper (for backward compatibility)
    database_client_type: str = "postgres"

    @property
    def async_database_url(self) -> str:
        """Ensure database URL uses asyncpg driver and compatible SSL params."""
        url = self.database_url
        # Convert postgresql:// to postgresql+asyncpg://
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        # Convert postgres:// to postgresql+asyncpg://
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)

        # Remove parameters that asyncpg doesn't understand
        # - sslmode: asyncpg handles SSL via connect_args
        # - pgbouncer: Prisma-specific parameter
        # - connect_timeout: handled differently in asyncpg
        import re

        url = re.sub(r"[?&]sslmode=[^&]*", "", url)
        url = re.sub(r"[?&]pgbouncer=[^&]*", "", url)
        url = re.sub(r"[?&]connect_timeout=[^&]*", "", url)
        # Clean up any trailing ? or &&
        url = url.rstrip("?").replace("&&", "&").rstrip("&")

        return url

    # OpenRouter API (for both LLM and Embeddings)
    # See: https://openrouter.ai/openai/text-embedding-3-small/api
    openrouter_api_key: str = ""
    llm_model: str = "openai/gpt-4o-mini"
    embedding_model: str = "openai/text-embedding-3-small"

    # Optional: OpenAI API key (fallback, not required if using OpenRouter)
    openai_api_key: str = ""

    # Google Gemini API (for Vision OCR)
    google_api_key: str = ""

    # OCR Provider Configuration
    # auto: Unstructured first, auto-switch to Gemini for scanned PDFs
    # unstructured: Lightweight parser (default, no PyTorch)
    # docling: Heavy parser with PyTorch (optional install)
    # gemini: Google Gemini Vision OCR
    ocr_mode: str = "auto"  # auto | unstructured | docling | gemini
    gemini_ocr_concurrency: int = (
        3  # Number of parallel Gemini API calls for OCR (reduced to avoid DB connection exhaustion)
    )
    gemini_request_timeout: int = 60  # Timeout for each Gemini API request (seconds)
    gemini_connection_timeout: int = 10  # Timeout for initial connection check (seconds)

    # Smart OCR Detection Thresholds (for auto mode)
    ocr_min_chars_per_page: int = 100  # Minimum characters per page to consider as text PDF
    ocr_max_garbage_ratio: float = 0.3  # Maximum ratio of garbage characters before triggering OCR

    # Storage
    upload_dir: str = "./data/uploads"

    # Supabase Storage
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    storage_bucket: str = "documents"

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

    # Logging - Loki
    loki_url: str = ""
    loki_enabled: bool = False

    # Observability - Langfuse
    # See: https://langfuse.com/docs/integrations/langchain
    langfuse_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"  # Or self-hosted URL

    # Supabase Auth
    supabase_jwt_secret: str = ""  # JWT secret for verifying Supabase Auth tokens
    auth_bypass_enabled: bool = False  # Set True for local dev without auth

    # Evaluation - Ragas
    evaluation_enabled: bool = False
    evaluation_sample_rate: float = 0.1  # Evaluate 10% of queries by default

    # Retrieval Configuration
    retrieval_top_k: int = 5  # Number of top similar documents to retrieve for RAG
    retrieval_min_similarity: float = 0.0  # Minimum similarity threshold (0.0 = no filter)

    # Query Rewrite Configuration
    # use_llm_rewrite: If True, use LLM for query rewriting (more accurate, ~1-2s latency)
    #                  If False (default), use rule-based expansion (faster, no extra LLM call)
    use_llm_rewrite: bool = False  # Disabled by default for faster response time

    # Intent Classification Configuration
    intent_classification_enabled: bool = True  # Enable intent-based adaptive RAG strategies
    intent_cache_enabled: bool = True  # Cache intent classification results

    # Long Context RAG Configuration
    rag_mode: str = "traditional"  # traditional | long_context | auto
    long_context_safety_ratio: float = 0.55  # Use 55% of model context window (conservative)
    long_context_min_tokens: int = 10000  # Minimum tokens to use long context mode
    enable_citation_grounding: bool = True  # Enable citation anchors
    citation_format: str = "both"  # inline | structured | both

    # Mega-Prompt Configuration (for long_context mode)
    mega_prompt_citation_mode: str = "xml_quote"  # xml_quote | text_markers | json_mode
    # xml_quote: XML tags with quote attribute for precise localization (default, recommended)
    # text_markers: Simple [doc_01] text markers (document-level only)
    # json_mode: Structured JSON output (more stable, less streaming-friendly)
    citation_match_threshold: int = 85  # Fuzzy match threshold (0-100) for Quote-to-Coordinate

    # Redis Configuration (for ARQ task queue)
    redis_url: str = ""  # redis://localhost:6379 or rediss://...@upstash.io:6379

    # URL Extraction Configuration
    url_extraction_timeout: int = 60  # Timeout for URL extraction tasks (seconds)
    url_content_max_length: int = 50000  # Maximum content length (characters)
    disable_ssrf_check: bool = False  # Disable SSRF protection (only for development/testing)
    youtube_cookies_path: str = ""  # Path to Netscape formatted cookies file for YouTube auth
    youtube_cookies_content: str = ""  # Raw content of cookies.txt (useful for cloud envs)

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

        # Default/Known origins
        defaults = [
            "https://research-agent-rag-web-dev.zeabur.app",
            "https://research-agent-rag-frontend-dev.zeabur.app",
            "https://weaver.zeabur.app",  # Production frontend
            "http://localhost:3000",
            "http://localhost:3001",
        ]

        # Deduplicate and return
        return list(set(origins + defaults))

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
