"""
Semantic Router Strategy

基于 semantic-router 开源库的路由策略。
使用语义向量空间进行快速决策路由。
"""

import logging
from typing import Dict, List, Any, Optional, Union
import asyncio

try:
    from semantic_router import Route
    from semantic_router.encoders import (
        CohereEncoder, 
        OpenAIEncoder, 
        HuggingFaceEncoder,
        FastEmbedEncoder
    )
    from semantic_router.routers import SemanticRouter
    SEMANTIC_ROUTER_AVAILABLE = True
except ImportError:
    SEMANTIC_ROUTER_AVAILABLE = False
    Route = None
    SemanticRouter = None

from .base import IRoutingStrategy
from ..engine import RouteDecision

logger = logging.getLogger(__name__)


class SemanticRouterStrategy(IRoutingStrategy):
    """基于 semantic-router 的路由策略"""
    
    def __init__(
        self,
        encoder_type: str = "fastembed",
        encoder_config: Dict[str, Any] = None,
        routes_config: List[Dict[str, Any]] = None,
        threshold: float = 0.5,
        top_k: int = 1
    ):
        """
        初始化 semantic router 策略
        
        Args:
            encoder_type: 编码器类型 ("cohere", "openai", "huggingface", "fastembed")
            encoder_config: 编码器配置参数
            routes_config: 路由配置列表
            threshold: 路由决策阈值
            top_k: 返回的最佳匹配数量
        """
        if not SEMANTIC_ROUTER_AVAILABLE:
            raise ImportError(
                "semantic-router is not installed. "
                "Please install it with: pip install semantic-router"
            )
        
        self.encoder_type = encoder_type
        self.encoder_config = encoder_config or {}
        self.routes_config = routes_config or []
        self.threshold = threshold
        self.top_k = top_k
        
        self.encoder = None
        self.router = None
        
        # 默认路由配置
        self._default_routes = [
            {
                "name": "rag_query",
                "handler": "rag_handler",
                "utterances": [
                    "搜索文档中关于",
                    "查找相关信息",
                    "文档里有没有关于",
                    "根据文档回答",
                    "在知识库中查询",
                    "find information about",
                    "search for",
                    "what does the document say about",
                    "according to the documents",
                    "look up information"
                ]
            },
            {
                "name": "casual_chat",
                "handler": "chat_handler",
                "utterances": [
                    "你好",
                    "早上好",
                    "怎么样",
                    "聊天",
                    "随便说说",
                    "hello",
                    "hi there",
                    "how are you",
                    "good morning",
                    "let's chat"
                ]
            },
            {
                "name": "system_command",
                "handler": "system_handler",
                "utterances": [
                    "系统状态",
                    "健康检查",
                    "停止服务",
                    "重启",
                    "清理缓存",
                    "system status",
                    "health check",
                    "stop service",
                    "restart",
                    "clear cache"
                ]
            },
            {
                "name": "summary_request",
                "handler": "summary_handler",
                "utterances": [
                    "总结一下",
                    "给我一个摘要",
                    "概括要点",
                    "总结文档",
                    "主要内容是什么",
                    "summarize this",
                    "give me a summary",
                    "what are the key points",
                    "main takeaways",
                    "overview of the document"
                ]
            }
        ]
    
    async def initialize(self) -> None:
        """初始化编码器和路由器"""
        try:
            # 创建编码器
            self.encoder = await self._create_encoder()
            
            # 创建路由
            routes = self._create_routes()
            
            # 创建路由器
            self.router = SemanticRouter(
                encoder=self.encoder,
                routes=routes,
                threshold=self.threshold,
                top_k=self.top_k
            )
            
            logger.info(f"SemanticRouter 策略初始化成功，编码器: {self.encoder_type}, 路由数量: {len(routes)}")
            
        except Exception as e:
            logger.error(f"SemanticRouter 策略初始化失败: {e}")
            raise
    
    async def _create_encoder(self):
        """创建编码器实例"""
        if self.encoder_type.lower() == "cohere":
            return CohereEncoder(**self.encoder_config)
        elif self.encoder_type.lower() == "openai":
            return OpenAIEncoder(**self.encoder_config)
        elif self.encoder_type.lower() == "huggingface":
            return HuggingFaceEncoder(**self.encoder_config)
        elif self.encoder_type.lower() == "fastembed":
            return FastEmbedEncoder(**self.encoder_config)
        else:
            raise ValueError(f"不支持的编码器类型: {self.encoder_type}")
    
    def _create_routes(self) -> List[Route]:
        """创建路由实例"""
        routes = []
        
        # 使用配置的路由或默认路由
        routes_config = self.routes_config if self.routes_config else self._default_routes
        
        for route_config in routes_config:
            route = Route(
                name=route_config["name"],
                utterances=route_config["utterances"]
            )
            routes.append(route)
        
        return routes
    
    async def decide_route(self, query: str, context: Dict[str, Any]) -> RouteDecision:
        """
        使用 semantic router 进行路由决策
        
        Args:
            query: 用户查询文本
            context: 上下文信息
            
        Returns:
            RouteDecision: 路由决策结果
        """
        if not self.router:
            logger.warning("SemanticRouter 未初始化，回退到默认处理器")
            return RouteDecision(
                handler_name="chat_handler",
                confidence=0.0,
                metadata={"strategy": "semantic_router", "error": "router_not_initialized"}
            )
        
        try:
            # 执行路由决策
            result = await asyncio.to_thread(self._sync_route, query)
            
            if result and hasattr(result, 'name') and result.name:
                # 找到匹配的路由配置
                handler_name = self._get_handler_for_route(result.name)
                confidence = getattr(result, 'score', 0.8)
                
                metadata = {
                    "strategy": "semantic_router",
                    "route_name": result.name,
                    "encoder_type": self.encoder_type,
                    "threshold": self.threshold
                }
                
                if hasattr(result, 'score'):
                    metadata["score"] = result.score
                    
                logger.info(f"SemanticRouter 路由决策: {result.name} -> {handler_name} (置信度: {confidence})")
                
                return RouteDecision(
                    handler_name=handler_name,
                    confidence=confidence,
                    metadata=metadata
                )
            else:
                # 没有找到匹配路由，使用默认处理器
                logger.info("SemanticRouter 未找到匹配路由，使用默认处理器")
                return RouteDecision(
                    handler_name="chat_handler",
                    confidence=0.0,
                    metadata={
                        "strategy": "semantic_router",
                        "result": "no_match",
                        "encoder_type": self.encoder_type
                    }
                )
                
        except Exception as e:
            logger.error(f"SemanticRouter 路由决策失败: {e}")
            return RouteDecision(
                handler_name="chat_handler",
                confidence=0.0,
                metadata={"strategy": "semantic_router", "error": str(e)}
            )
    
    def _sync_route(self, query: str):
        """同步路由决策（用于在线程中执行）"""
        return self.router(query)
    
    def _get_handler_for_route(self, route_name: str) -> str:
        """根据路由名称获取对应的处理器名称"""
        # 从配置的路由中查找
        routes_config = self.routes_config if self.routes_config else self._default_routes
        
        for route_config in routes_config:
            if route_config["name"] == route_name:
                return route_config.get("handler", "chat_handler")
        
        # 默认映射规则
        route_handler_mapping = {
            "rag_query": "rag_handler",
            "casual_chat": "chat_handler",
            "system_command": "system_handler",
            "summary_request": "summary_handler",
            "tool_request": "tool_handler"
        }
        
        return route_handler_mapping.get(route_name, "chat_handler")
    
    @property
    def strategy_name(self) -> str:
        """策略名称"""
        return "semantic_router"
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            if self.encoder and hasattr(self.encoder, 'cleanup'):
                await self.encoder.cleanup()
            
            self.router = None
            self.encoder = None
            
            logger.info("SemanticRouter 策略资源已清理")
        except Exception as e:
            logger.warning(f"SemanticRouter 策略清理时出错: {e}")
    
    def update_routes(self, new_routes_config: List[Dict[str, Any]]) -> None:
        """更新路由配置（需要重新初始化）"""
        self.routes_config = new_routes_config
        logger.info(f"SemanticRouter 路由配置已更新，包含 {len(new_routes_config)} 个路由")
    
    def get_route_info(self) -> Dict[str, Any]:
        """获取路由信息"""
        routes_config = self.routes_config if self.routes_config else self._default_routes
        
        return {
            "strategy_name": self.strategy_name,
            "encoder_type": self.encoder_type,
            "threshold": self.threshold,
            "top_k": self.top_k,
            "routes_count": len(routes_config),
            "routes": [
                {
                    "name": route["name"],
                    "handler": route.get("handler", "chat_handler"),
                    "utterances_count": len(route["utterances"])
                }
                for route in routes_config
            ]
        }