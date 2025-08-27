"""
Routing Engine Factory

路由引擎工厂，提供不同配置的路由引擎创建。
"""

import logging
from typing import Dict, Any, Optional, List

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

try:
    from .strategies.semantic_router_strategy import SemanticRouterStrategy
    SEMANTIC_ROUTER_AVAILABLE = True
except ImportError:
    SEMANTIC_ROUTER_AVAILABLE = False
    SemanticRouterStrategy = None

from .engine import QueryRoutingEngine, RoutingRule
from .strategies.configurable_keyword_strategy import ConfigurableKeywordStrategy
from .strategies.llm_intent_strategy import LLMIntentStrategy
from .handlers.rag_handler import RAGQueryHandler
from .handlers.chat_handler import ChatHandler
from .handlers.system_handler import SystemHandler
from .handlers.tool_handler import ToolHandler
from .handlers.summary_handler import SummaryQueryHandler
from .config.keyword_config import KeywordConfigLoader
from .config.config_manager import KeywordConfigManager

logger = logging.getLogger(__name__)


class RoutingEngineFactory:
    """路由引擎工厂类"""
    
    @staticmethod
    async def create_default_engine(
        chat_service: Optional[Any] = None,
        openai_client: Optional[Any] = None,
        config_dir: str = "config/routing",
        semantic_config: Optional[Dict[str, Any]] = None
    ) -> QueryRoutingEngine:
        """
        创建默认配置的路由引擎
        
        Args:
            chat_service: 聊天服务实例
            openai_client: OpenAI客户端
            config_dir: 配置文件目录
            
        Returns:
            QueryRoutingEngine: 配置好的路由引擎
        """
        logger.info("开始创建默认路由引擎")
        
        # 创建路由引擎
        engine = QueryRoutingEngine()
        
        # 创建配置加载器
        config_loader = KeywordConfigLoader(config_dir)
        
        # 创建并注册策略
        await RoutingEngineFactory._register_strategies(engine, config_loader, openai_client, semantic_config)
        
        # 创建并注册处理器
        await RoutingEngineFactory._register_handlers(engine, chat_service)
        
        # 添加默认路由规则
        await RoutingEngineFactory._add_default_rules(engine)
        
        # 配置引擎设置
        engine.set_default_strategy("configurable_keyword")  # 默认使用关键词策略
        engine.set_fallback_handler("chat_handler")
        engine.enable_rules = True
        engine.enable_monitoring = True
        
        logger.info("默认路由引擎创建完成")
        return engine
    
    @staticmethod
    async def create_llm_first_engine(
        chat_service: Optional[Any] = None,
        openai_client: Optional[Any] = None,
        config_dir: str = "config/routing",
        semantic_config: Optional[Dict[str, Any]] = None
    ) -> QueryRoutingEngine:
        """
        创建LLM优先的路由引擎
        
        Args:
            chat_service: 聊天服务实例
            openai_client: OpenAI客户端
            config_dir: 配置文件目录
            
        Returns:
            QueryRoutingEngine: LLM优先的路由引擎
        """
        logger.info("开始创建LLM优先路由引擎")
        
        if not openai_client and not OPENAI_AVAILABLE:
            logger.warning("OpenAI不可用，回退到默认引擎")
            return await RoutingEngineFactory.create_default_engine(chat_service, config_dir=config_dir, semantic_config=semantic_config)
        
        # 创建路由引擎
        engine = QueryRoutingEngine()
        
        # 创建配置加载器
        config_loader = KeywordConfigLoader(config_dir)
        
        # 创建并注册策略
        await RoutingEngineFactory._register_strategies(engine, config_loader, openai_client, semantic_config)
        
        # 创建并注册处理器
        await RoutingEngineFactory._register_handlers(engine, chat_service)
        
        # 添加默认路由规则
        await RoutingEngineFactory._add_default_rules(engine)
        
        # 配置引擎设置（LLM优先）
        engine.set_default_strategy("llm_intent")  # 使用LLM策略
        engine.set_fallback_handler("chat_handler")
        engine.enable_rules = True
        engine.enable_monitoring = True
        
        logger.info("LLM优先路由引擎创建完成")
        return engine
    
    @staticmethod
    async def create_keyword_only_engine(
        chat_service: Optional[Any] = None,
        config_dir: str = "config/routing"
    ) -> QueryRoutingEngine:
        """
        创建仅使用关键词的路由引擎（适合资源受限环境）
        
        Args:
            chat_service: 聊天服务实例
            config_dir: 配置文件目录
            
        Returns:
            QueryRoutingEngine: 关键词专用路由引擎
        """
        logger.info("开始创建关键词专用路由引擎")
        
        # 创建路由引擎
        engine = QueryRoutingEngine()
        
        # 创建配置加载器
        config_loader = KeywordConfigLoader(config_dir)
        
        # 只注册关键词策略
        configurable_strategy = ConfigurableKeywordStrategy(config_loader)
        await configurable_strategy.initialize()
        engine.register_strategy("configurable_keyword", configurable_strategy)
        
        # 创建并注册处理器
        await RoutingEngineFactory._register_handlers(engine, chat_service)
        
        # 添加默认路由规则
        await RoutingEngineFactory._add_default_rules(engine)
        
        # 配置引擎设置
        engine.set_default_strategy("configurable_keyword")
        engine.set_fallback_handler("chat_handler")
        engine.enable_rules = True
        engine.enable_monitoring = True
        
        logger.info("关键词专用路由引擎创建完成")
        return engine
    
    @staticmethod
    async def _register_strategies(
        engine: QueryRoutingEngine,
        config_loader: KeywordConfigLoader,
        openai_client: Optional[Any] = None,
        semantic_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """注册所有路由策略"""
        
        # 1. 配置化关键词策略（总是可用）
        configurable_strategy = ConfigurableKeywordStrategy(config_loader)
        await configurable_strategy.initialize()
        engine.register_strategy("configurable_keyword", configurable_strategy)
        
        # 2. LLM意图识别策略（如果可用）
        if openai_client or OPENAI_AVAILABLE:
            if not openai_client and OPENAI_AVAILABLE:
                # 使用默认配置创建客户端（注意：需要API密钥环境变量）
                try:
                    openai_client = openai.AsyncOpenAI()
                except Exception as e:
                    logger.warning(f"创建OpenAI客户端失败: {e}")
                    openai_client = None
            
            if openai_client:
                llm_strategy = LLMIntentStrategy(openai_client)
                await llm_strategy.initialize()
                engine.register_strategy("llm_intent", llm_strategy)
                logger.info("LLM意图识别策略已注册")
            else:
                logger.warning("OpenAI客户端不可用，跳过LLM策略注册")
        else:
            logger.info("OpenAI不可用，跳过LLM策略注册")
        
        # 3. Semantic Router策略（如果可用并启用）
        if SEMANTIC_ROUTER_AVAILABLE and semantic_config and semantic_config.get("enabled", False):
            try:
                # 加载语义路由配置
                routes_config = await RoutingEngineFactory._load_semantic_routes_config(
                    semantic_config.get("routes_config_file", "config/routing/semantic_routes.yaml")
                )
                
                # 创建编码器配置
                encoder_config = RoutingEngineFactory._build_encoder_config(semantic_config)
                
                semantic_strategy = SemanticRouterStrategy(
                    encoder_type=semantic_config.get("encoder_type", "fastembed"),
                    encoder_config=encoder_config,
                    routes_config=routes_config,
                    threshold=semantic_config.get("threshold", 0.5),
                    top_k=semantic_config.get("top_k", 1)
                )
                await semantic_strategy.initialize()
                engine.register_strategy("semantic_router", semantic_strategy)
                logger.info(f"Semantic Router策略已注册，编码器: {semantic_config.get('encoder_type', 'fastembed')}")
            except Exception as e:
                logger.error(f"Semantic Router策略注册失败: {e}")
        elif not SEMANTIC_ROUTER_AVAILABLE:
            logger.info("semantic-router库不可用，跳过Semantic Router策略注册")
        elif not semantic_config or not semantic_config.get("enabled", False):
            logger.info("Semantic Router策略未启用，跳过注册")
    
    @staticmethod
    async def _register_handlers(
        engine: QueryRoutingEngine,
        chat_service: Optional[Any] = None
    ) -> None:
        """注册所有查询处理器"""
        
        # 1. RAG查询处理器
        rag_handler = RAGQueryHandler(chat_service)
        await rag_handler.initialize()
        engine.register_handler("rag_handler", rag_handler)
        
        # 2. 普通聊天处理器
        chat_handler = ChatHandler(chat_service)
        await chat_handler.initialize()
        engine.register_handler("chat_handler", chat_handler)
        
        # 3. 系统命令处理器
        system_handler = SystemHandler(chat_service, engine)
        await system_handler.initialize()
        engine.register_handler("system_handler", system_handler)
        
        # 4. 工具调用处理器
        tool_handler = ToolHandler()
        await tool_handler.initialize()
        engine.register_handler("tool_handler", tool_handler)
        
        # 5. 摘要查询处理器 (新增)
        summary_handler = SummaryQueryHandler(chat_service)
        await summary_handler.initialize()
        engine.register_handler("summary_handler", summary_handler)
        
        logger.info("所有查询处理器已注册")
    
    @staticmethod
    async def _add_default_rules(engine: QueryRoutingEngine) -> None:
        """添加默认路由规则"""
        
        # 高优先级规则：管理员命令
        def is_admin_command(query: str, context: Dict[str, Any]) -> bool:
            return (query.startswith("/admin") and 
                   context.get("user_role") == "admin")
        
        admin_rule = RoutingRule(
            name="admin_command",
            condition=is_admin_command,
            handler_name="system_handler",
            priority=100,
            description="管理员专用命令"
        )
        engine.add_rule(admin_rule)
        
        # 中等优先级规则：健康检查
        def is_health_check(query: str, context: Dict[str, Any]) -> bool:
            return query.lower().strip() in ["health", "status", "ping", "健康检查", "状态"]
        
        health_rule = RoutingRule(
            name="health_check",
            condition=is_health_check,
            handler_name="system_handler",
            priority=90,
            description="系统健康检查"
        )
        engine.add_rule(health_rule)
        
        # 中等优先级规则：紧急停止
        def is_emergency_stop(query: str, context: Dict[str, Any]) -> bool:
            emergency_keywords = ["停止", "stop", "halt", "紧急停止", "emergency"]
            return any(keyword in query.lower() for keyword in emergency_keywords)
        
        emergency_rule = RoutingRule(
            name="emergency_stop",
            condition=is_emergency_stop,
            handler_name="system_handler",
            priority=80,
            description="紧急停止命令"
        )
        engine.add_rule(emergency_rule)
        
        logger.info("默认路由规则已添加")
    
    @staticmethod
    async def create_custom_engine(
        strategies: Dict[str, Any],
        handlers: Dict[str, Any],
        rules: list = None,
        config: Dict[str, Any] = None
    ) -> QueryRoutingEngine:
        """
        创建自定义配置的路由引擎
        
        Args:
            strategies: 策略配置字典
            handlers: 处理器配置字典
            rules: 自定义规则列表
            config: 引擎配置
            
        Returns:
            QueryRoutingEngine: 自定义路由引擎
        """
        logger.info("开始创建自定义路由引擎")
        
        # 创建路由引擎
        engine = QueryRoutingEngine()
        
        # 注册策略
        for name, strategy in strategies.items():
            if hasattr(strategy, 'initialize'):
                await strategy.initialize()
            engine.register_strategy(name, strategy)
        
        # 注册处理器
        for name, handler in handlers.items():
            if hasattr(handler, 'initialize'):
                await handler.initialize()
            engine.register_handler(name, handler)
        
        # 添加自定义规则
        if rules:
            for rule in rules:
                engine.add_rule(rule)
        
        # 应用配置
        if config:
            if "default_strategy" in config:
                engine.set_default_strategy(config["default_strategy"])
            if "fallback_handler" in config:
                engine.set_fallback_handler(config["fallback_handler"])
            if "enable_rules" in config:
                engine.enable_rules = config["enable_rules"]
            if "enable_monitoring" in config:
                engine.enable_monitoring = config["enable_monitoring"]
        
        logger.info("自定义路由引擎创建完成")
        return engine
    
    @staticmethod
    async def create_with_config_manager(
        chat_service: Optional[Any] = None,
        openai_client: Optional[Any] = None,
        config_dir: str = "config/routing",
        semantic_config: Optional[Dict[str, Any]] = None
    ) -> tuple[QueryRoutingEngine, KeywordConfigManager]:
        """
        创建带配置管理器的路由引擎
        
        Returns:
            tuple: (路由引擎, 配置管理器)
        """
        # 创建路由引擎
        engine = await RoutingEngineFactory.create_default_engine(
            chat_service, openai_client, config_dir, semantic_config
        )
        
        # 创建配置管理器
        config_manager = KeywordConfigManager(engine)
        await config_manager.initialize()
        
        logger.info("带配置管理器的路由引擎已创建")
        return engine, config_manager
    
    @staticmethod
    async def _load_semantic_routes_config(config_file_path: str) -> List[Dict[str, Any]]:
        """加载语义路由配置文件"""
        import os
        import yaml
        
        if not os.path.exists(config_file_path):
            logger.warning(f"语义路由配置文件不存在: {config_file_path}，使用默认配置")
            return []
        
        try:
            with open(config_file_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                routes = config.get("routes", [])
                logger.info(f"从配置文件加载了 {len(routes)} 个语义路由")
                return routes
        except Exception as e:
            logger.error(f"加载语义路由配置文件失败: {e}")
            return []
    
    @staticmethod
    def _build_encoder_config(semantic_config: Dict[str, Any]) -> Dict[str, Any]:
        """构建编码器配置"""
        encoder_type = semantic_config.get("encoder_type", "fastembed")
        encoder_config = {}
        
        if encoder_type == "openai":
            if semantic_config.get("openai_api_key"):
                encoder_config["api_key"] = semantic_config["openai_api_key"]
            if semantic_config.get("encoder_model"):
                encoder_config["model"] = semantic_config["encoder_model"]
        
        elif encoder_type == "cohere":
            if semantic_config.get("cohere_api_key"):
                encoder_config["api_key"] = semantic_config["cohere_api_key"]
            if semantic_config.get("encoder_model"):
                encoder_config["model"] = semantic_config["encoder_model"]
        
        elif encoder_type == "huggingface":
            encoder_config["model"] = semantic_config.get("huggingface_model", "sentence-transformers/all-MiniLM-L6-v2")
        
        elif encoder_type == "fastembed":
            encoder_config["model"] = semantic_config.get("fastembed_model", "BAAI/bge-small-en-v1.5")
        
        return encoder_config
    
    @staticmethod
    async def create_semantic_router_engine(
        chat_service: Optional[Any] = None,
        semantic_config: Optional[Dict[str, Any]] = None,
        config_dir: str = "config/routing"
    ) -> QueryRoutingEngine:
        """
        创建专用的语义路由引擎
        
        Args:
            chat_service: 聊天服务实例
            semantic_config: 语义路由配置
            config_dir: 配置文件目录
            
        Returns:
            QueryRoutingEngine: 语义路由专用引擎
        """
        if not SEMANTIC_ROUTER_AVAILABLE:
            logger.warning("semantic-router不可用，回退到默认引擎")
            return await RoutingEngineFactory.create_default_engine(chat_service, config_dir=config_dir)
        
        logger.info("开始创建语义路由专用引擎")
        
        # 创建路由引擎
        engine = QueryRoutingEngine()
        
        # 创建配置加载器
        config_loader = KeywordConfigLoader(config_dir)
        
        # 只注册语义路由策略
        if semantic_config and semantic_config.get("enabled", True):
            await RoutingEngineFactory._register_strategies(
                engine, 
                config_loader, 
                semantic_config=semantic_config
            )
        
        # 创建并注册处理器
        await RoutingEngineFactory._register_handlers(engine, chat_service)
        
        # 添加默认路由规则
        await RoutingEngineFactory._add_default_rules(engine)
        
        # 配置引擎设置
        engine.set_default_strategy("semantic_router")
        engine.set_fallback_handler("chat_handler")
        engine.enable_rules = True
        engine.enable_monitoring = True
        
        logger.info("语义路由专用引擎创建完成")
        return engine


# 便捷函数
async def create_routing_engine(
    mode: str = "default",
    chat_service: Optional[Any] = None,
    openai_client: Optional[Any] = None,
    config_dir: str = "config/routing",
    semantic_config: Optional[Dict[str, Any]] = None
) -> QueryRoutingEngine:
    """
    便捷的路由引擎创建函数
    
    Args:
        mode: 创建模式 ("default", "llm_first", "keyword_only", "semantic_router")
        chat_service: 聊天服务实例
        openai_client: OpenAI客户端
        config_dir: 配置文件目录
        semantic_config: 语义路由配置
        
    Returns:
        QueryRoutingEngine: 路由引擎实例
    """
    if mode == "llm_first":
        return await RoutingEngineFactory.create_llm_first_engine(
            chat_service, openai_client, config_dir, semantic_config
        )
    elif mode == "keyword_only":
        return await RoutingEngineFactory.create_keyword_only_engine(
            chat_service, config_dir
        )
    elif mode == "semantic_router":
        return await RoutingEngineFactory.create_semantic_router_engine(
            chat_service, semantic_config, config_dir
        )
    else:  # default
        return await RoutingEngineFactory.create_default_engine(
            chat_service, openai_client, config_dir, semantic_config
        )