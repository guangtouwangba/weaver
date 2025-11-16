"""Application lifecycle management for RAG system."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
import logging
import os

from fastapi import FastAPI

from shared_config.settings import AppSettings

logger = logging.getLogger(__name__)


class ApplicationState:
    """
    Centralized application state management.
    
    Manages the lifecycle of all RAG system components:
    - LLM and Embeddings
    - Vector Store
    - Redis Cache (optional)
    - Reranker (optional)
    - LangSmith Tracing (optional)
    - Prometheus Metrics (optional)
    """

    def __init__(self):
        """Initialize empty state."""
        self.settings: AppSettings | None = None
        self.vector_store: Any = None
        self.llm: Any = None
        self.embeddings: Any = None
        self.redis_client: Any = None
        self.reranker: Any = None
        self.prometheus_registry: Any = None
        self.is_initialized: bool = False

    async def initialize(self) -> None:
        """
        Initialize all application modules in the correct order.
        
        Order matters:
        1. Configuration
        2. LLM and Embeddings
        3. Vector Store
        4. Optional: Redis, Reranker, LangSmith, Prometheus
        """
        if self.is_initialized:
            logger.warning("⚠️  Application already initialized, skipping...")
            return

        logger.info("=" * 80)
        logger.info("🚀 开始初始化 RAG 系统模块...")
        logger.info("=" * 80)

        try:
            # 1. Load configuration
            await self._init_config()

            # 2. Initialize LLM and Embeddings
            await self._init_llm_and_embeddings()

            # 3. Initialize Vector Store
            await self._init_vector_store()

            # 4. Initialize optional modules
            if self.settings.cache.enabled:
                await self._init_redis()

            if self.settings.reranker.enabled:
                await self._init_reranker()

            if self.settings.observability.langsmith_enabled:
                self._init_langsmith()

            if self.settings.observability.prometheus_enabled:
                self._init_prometheus()

            self.is_initialized = True
            logger.info("=" * 80)
            logger.info("✅ RAG 系统所有模块初始化完成！")
            logger.info("=" * 80)
            self._log_system_status()

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}", exc_info=True)
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """
        Cleanup all modules in reverse order.
        
        Ensures graceful shutdown of all resources.
        """
        if not self.is_initialized:
            logger.info("⏭️  No cleanup needed, system not initialized")
            return

        logger.info("=" * 80)
        logger.info("🧹 开始清理 RAG 系统模块...")
        logger.info("=" * 80)

        # Cleanup in reverse order
        cleanup_tasks = [
            ("Prometheus", self._cleanup_prometheus),
            ("LangSmith", self._cleanup_langsmith),
            ("Reranker", self._cleanup_reranker),
            ("Redis", self._cleanup_redis),
            ("Vector Store", self._cleanup_vector_store),
            ("LLM & Embeddings", self._cleanup_llm_and_embeddings),
        ]

        for name, cleanup_func in cleanup_tasks:
            try:
                await cleanup_func()
            except Exception as e:
                logger.error(f"清理 {name} 时出错: {e}")

        self.is_initialized = False
        logger.info("=" * 80)
        logger.info("✅ RAG 系统所有模块清理完成！")
        logger.info("=" * 80)

    # ========================================
    # Initialization Methods
    # ========================================

    async def _init_config(self) -> None:
        """Load application configuration."""
        logger.info("📋 加载配置...")
        self.settings = AppSettings()  # type: ignore[arg-type]
        logger.info(f"   ├─ 环境: {self.settings.app_env}")
        logger.info(f"   ├─ LLM Provider: {self.settings.llm.provider}")
        logger.info(f"   └─ Embedding Provider: {self.settings.embedding.provider}")

    async def _init_llm_and_embeddings(self) -> None:
        """Initialize LLM and embedding models."""
        logger.info("🤖 初始化 LLM 和 Embeddings...")

        try:
            from rag_core.chains.llm import build_llm
            from rag_core.chains.embeddings import build_embedding_function

            self.llm = build_llm(self.settings)
            self.embeddings = build_embedding_function(self.settings)

            logger.info(f"   ├─ LLM: {self.settings.llm.model}")
            logger.info(f"   └─ Embeddings: {self.settings.embedding.model}")
        except Exception as e:
            logger.error(f"   ❌ LLM/Embeddings 初始化失败: {e}")
            raise

    async def _init_vector_store(self) -> None:
        """Initialize vector store."""
        logger.info("🗄️  初始化向量存储...")

        try:
            from rag_core.chains.vectorstore import load_vector_store

            self.vector_store = load_vector_store()

            if self.vector_store:
                logger.info(f"   ✅ 向量存储加载成功 (路径: {self.settings.vector_store_path})")
            else:
                logger.warning("   ⚠️  向量存储为空，可能需要先导入文档")
        except Exception as e:
            logger.warning(f"   ⚠️  向量存储加载失败: {e}")
            # Vector store can be empty initially, not critical

    async def _init_redis(self) -> None:
        """Initialize Redis cache."""
        logger.info("🔴 初始化 Redis 缓存...")

        try:
            import redis.asyncio as redis

            self.redis_client = await redis.from_url(
                self.settings.cache.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=self.settings.cache.redis_max_connections,
            )

            # Test connection
            await self.redis_client.ping()
            logger.info(f"   ✅ Redis 连接成功 ({self.settings.cache.redis_url})")

        except ImportError:
            logger.error("   ❌ redis 库未安装，请运行: pip install redis")
            self.redis_client = None
        except Exception as e:
            logger.error(f"   ❌ Redis 连接失败: {e}")
            self.redis_client = None
            if self.settings.cache.enabled:
                raise  # Fail if cache is explicitly enabled but unavailable

    async def _init_reranker(self) -> None:
        """Initialize document reranker."""
        logger.info("🎯 初始化重排序器...")

        try:
            from rag_core.rerankers.factory import RerankerFactory

            self.reranker = await RerankerFactory.create_from_settings(self.settings)

            if self.reranker:
                config = self.reranker.get_config()
                logger.info(f"   ✅ 重排序器加载成功")
                logger.info(f"      ├─ 类型: {config['type']}")
                logger.info(f"      ├─ 模型: {config['model_name']}")
                logger.info(f"      ├─ Top-N: {config['top_n']}")
                logger.info(f"      └─ 设备: {config['device']}")
            else:
                logger.info("   ℹ️  重排序器未启用")

        except ImportError as e:
            logger.error(f"   ❌ 重排序器依赖未安装: {e}")
            logger.error("   💡 请安装: pip install sentence-transformers")
            self.reranker = None
            if self.settings.reranker.enabled:
                raise  # Fail if reranker is explicitly enabled but unavailable
        except Exception as e:
            logger.error(f"   ❌ 重排序器初始化失败: {e}")
            self.reranker = None
            if self.settings.reranker.enabled:
                raise

    def _init_langsmith(self) -> None:
        """Initialize LangSmith tracing."""
        logger.info("🔍 初始化 LangSmith 追踪...")

        try:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = self.settings.observability.langsmith_project

            if self.settings.observability.langsmith_api_key:
                api_key = self.settings.observability.langsmith_api_key.get_secret_value()
                os.environ["LANGCHAIN_API_KEY"] = api_key

            logger.info(f"   ✅ LangSmith 已启用 (项目: {self.settings.observability.langsmith_project})")

        except Exception as e:
            logger.error(f"   ❌ LangSmith 初始化失败: {e}")

    def _init_prometheus(self) -> None:
        """Initialize Prometheus metrics."""
        logger.info("📊 初始化 Prometheus 监控...")

        try:
            from prometheus_client import CollectorRegistry

            self.prometheus_registry = CollectorRegistry()
            logger.info(f"   ✅ Prometheus 已启用 (端口: {self.settings.observability.prometheus_port})")
            logger.info("   ℹ️  指标端点: /metrics")

        except ImportError:
            logger.error("   ❌ prometheus-client 库未安装，请运行: pip install prometheus-client")
            self.prometheus_registry = None
        except Exception as e:
            logger.error(f"   ❌ Prometheus 初始化失败: {e}")
            self.prometheus_registry = None

    # ========================================
    # Cleanup Methods
    # ========================================

    async def _cleanup_llm_and_embeddings(self) -> None:
        """Cleanup LLM and embeddings."""
        if self.llm or self.embeddings:
            logger.info("   🤖 清理 LLM 和 Embeddings...")
            # Most LLMs don't need explicit cleanup
            self.llm = None
            self.embeddings = None

    async def _cleanup_vector_store(self) -> None:
        """Cleanup vector store."""
        if self.vector_store:
            logger.info("   🗄️  清理向量存储...")
            # FAISS doesn't need explicit cleanup
            self.vector_store = None

    async def _cleanup_redis(self) -> None:
        """Cleanup Redis connection."""
        if self.redis_client:
            logger.info("   🔴 关闭 Redis 连接...")
            try:
                await self.redis_client.aclose()
            except Exception as e:
                logger.error(f"   ❌ Redis 关闭失败: {e}")
            finally:
                self.redis_client = None

    async def _cleanup_reranker(self) -> None:
        """Cleanup reranker."""
        if self.reranker:
            logger.info("   🎯 清理重排序器...")
            # Add cleanup logic when reranker is implemented
            self.reranker = None

    async def _cleanup_langsmith(self) -> None:
        """Cleanup LangSmith."""
        # LangSmith doesn't need explicit cleanup
        pass

    async def _cleanup_prometheus(self) -> None:
        """Cleanup Prometheus."""
        if self.prometheus_registry:
            logger.info("   📊 清理 Prometheus...")
            self.prometheus_registry = None

    # ========================================
    # Utility Methods
    # ========================================

    def _log_system_status(self) -> None:
        """Log the status of all system components."""
        logger.info("")
        logger.info("📊 系统组件状态:")
        logger.info(f"   ├─ LLM: {'✅ 已加载' if self.llm else '❌ 未加载'}")
        logger.info(f"   ├─ Embeddings: {'✅ 已加载' if self.embeddings else '❌ 未加载'}")
        logger.info(f"   ├─ 向量存储: {'✅ 已加载' if self.vector_store else '⚠️  空'}")
        logger.info(f"   ├─ Redis 缓存: {'✅ 已连接' if self.redis_client else '❌ 未启用'}")
        logger.info(f"   ├─ 重排序器: {'✅ 已加载' if self.reranker else '❌ 未启用'}")
        logger.info(f"   ├─ LangSmith: {'✅ 已启用' if self.settings.observability.langsmith_enabled else '❌ 未启用'}")
        logger.info(f"   └─ Prometheus: {'✅ 已启用' if self.settings.observability.prometheus_enabled else '❌ 未启用'}")
        logger.info("")

    def get_status(self) -> dict[str, Any]:
        """
        Get the status of all components.
        
        Returns:
            Dictionary with component status information.
        """
        return {
            "initialized": self.is_initialized,
            "components": {
                "llm": {"status": "loaded" if self.llm else "not_loaded"},
                "embeddings": {"status": "loaded" if self.embeddings else "not_loaded"},
                "vector_store": {"status": "loaded" if self.vector_store else "empty"},
                "redis": {
                    "status": "connected" if self.redis_client else "disconnected",
                    "enabled": self.settings.cache.enabled if self.settings else False,
                },
                "reranker": {
                    "status": "loaded" if self.reranker else "not_loaded",
                    "enabled": self.settings.reranker.enabled if self.settings else False,
                },
                "langsmith": {
                    "status": "enabled" if self.settings and self.settings.observability.langsmith_enabled else "disabled",
                },
                "prometheus": {
                    "status": "enabled" if self.prometheus_registry else "disabled",
                },
            },
        }


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.
    
    Manages the startup and shutdown of the RAG system.
    
    Usage:
        app = FastAPI(lifespan=lifespan)
    """
    # Startup
    app.state.rag = ApplicationState()
    await app.state.rag.initialize()

    yield

    # Shutdown
    await app.state.rag.cleanup()

