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
        FastEmbedEncoder,
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
        top_k: int = 1,
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

        # 移除硬编码的默认路由 - 强制使用配置文件中的语义路由
        # 这样确保真正使用语义向量而不是关键词匹配
        self._default_routes = []

    async def initialize(self) -> None:
        """初始化编码器和路由器"""
        try:
            # 创建编码器
            self.encoder = await self._create_encoder()

            # 创建路由
            routes = self._create_routes()

            # 创建路由器（启用异步索引）
            self.router = SemanticRouter(
                encoder=self.encoder,
                routes=routes,
                top_k=self.top_k,
                init_async_index=True,
            )

            # 等待索引构建完成
            logger.info("正在构建SemanticRouter索引...")
            if hasattr(self.router, "async_sync"):
                # 添加缺失的sync_mode参数，使用默认的embedding模式
                await self.router.async_sync(sync_mode="embedding")
            elif hasattr(self.router, "sync"):
                # 如果没有异步方法，使用同步方法（在线程中执行）
                await asyncio.to_thread(self.router.sync)

            # 验证索引是否准备就绪
            if hasattr(self.router, "async_is_synced"):
                is_ready = await self.router.async_is_synced()
            elif hasattr(self.router, "is_synced"):
                is_ready = await asyncio.to_thread(self.router.is_synced)
            else:
                is_ready = True  # 假设已准备就绪

            if is_ready:
                logger.info(
                    f"SemanticRouter 策略初始化成功，编码器: {self.encoder_type}, 路由数量: {len(routes)}, 索引状态: 已准备"
                )
            else:
                logger.warning("SemanticRouter 索引未完全准备就绪，但将继续初始化")
                logger.info(
                    f"SemanticRouter 策略初始化完成，编码器: {self.encoder_type}, 路由数量: {len(routes)}, 索引状态: 未完全准备"
                )

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
        """创建路由实例 - 必须基于配置文件中的语义示例"""
        routes = []

        # 强制使用配置文件中的路由，确保使用语义示例而不是关键词
        if not self.routes_config:
            raise ValueError(
                "SemanticRouter 必须提供路由配置文件。"
                "请确保配置文件包含完整的语义示例utterances，而不是关键词片段。"
            )

        routes_config = self.routes_config

        for route_config in routes_config:
            # 验证路由配置包含必要字段
            if "name" not in route_config or "utterances" not in route_config:
                raise ValueError(f"路由配置缺少必要字段: {route_config}")

            # 验证utterances是完整句子而不是关键词片段
            utterances = route_config["utterances"]
            if not utterances:
                raise ValueError(f"路由 {route_config['name']} 的utterances不能为空")

            # 简单检查：好的语义示例通常包含多个词且长度合理
            for utterance in utterances[:3]:  # 检查前几个示例
                if len(utterance.split()) < 3:
                    logger.warning(
                        f"路由 {route_config['name']} 的utterance '{utterance}' 可能过短，"
                        f"请使用完整的语义示例句子而不是关键词片段"
                    )

            route = Route(name=route_config["name"], utterances=utterances)
            routes.append(route)

        logger.info(f"创建了 {len(routes)} 个语义路由，总共包含语义示例数量:")
        for route, config in zip(routes, routes_config):
            logger.info(f"  - {route.name}: {len(config['utterances'])} 个示例")

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
                metadata={
                    "strategy": "semantic_router",
                    "error": "router_not_initialized",
                },
            )

        # 检查索引是否准备就绪
        try:
            if hasattr(self.router, "async_is_synced"):
                is_ready = await self.router.async_is_synced()
            elif hasattr(self.router, "is_synced"):
                is_ready = await asyncio.to_thread(self.router.is_synced)
            else:
                is_ready = True  # 假设已准备就绪

            if not is_ready:
                logger.warning("SemanticRouter 索引未准备就绪，尝试重新同步...")
                try:
                    if hasattr(self.router, "async_sync"):
                        await self.router.async_sync(sync_mode="embedding")
                    elif hasattr(self.router, "sync"):
                        await asyncio.to_thread(self.router.sync)
                except Exception as sync_e:
                    logger.error(f"SemanticRouter 索引同步失败: {sync_e}")
                    return RouteDecision(
                        handler_name="chat_handler",
                        confidence=0.0,
                        metadata={
                            "strategy": "semantic_router",
                            "error": "index_not_ready",
                            "sync_error": str(sync_e),
                        },
                    )
        except Exception as check_e:
            logger.warning(f"检查SemanticRouter索引状态失败: {check_e}")

        try:
            # 执行路由决策
            result = await asyncio.to_thread(self._sync_route, query)

            if result and hasattr(result, "name") and result.name:
                # 找到匹配的路由配置
                handler_name = self._get_handler_for_route(result.name)
                confidence = getattr(result, "score", 0.8)

                # 应用阈值检查
                if confidence < self.threshold:
                    logger.info(
                        f"SemanticRouter 路由置信度 {confidence:.3f} 低于阈值 {self.threshold}，使用默认处理器"
                    )
                    return RouteDecision(
                        handler_name="chat_handler",
                        confidence=0.0,
                        metadata={
                            "strategy": "semantic_router",
                            "result": "below_threshold",
                            "route_name": result.name,
                            "score": confidence,
                            "threshold": self.threshold,
                            "encoder_type": self.encoder_type,
                        },
                    )

                metadata = {
                    "strategy": "semantic_router",
                    "route_name": result.name,
                    "encoder_type": self.encoder_type,
                    "threshold": self.threshold,
                }

                if hasattr(result, "score"):
                    metadata["score"] = result.score

                logger.info(
                    f"SemanticRouter 路由决策: {result.name} -> {handler_name} (置信度: {confidence:.3f})"
                )

                return RouteDecision(
                    handler_name=handler_name, confidence=confidence, metadata=metadata
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
                        "encoder_type": self.encoder_type,
                    },
                )

        except Exception as e:
            logger.error(f"SemanticRouter 路由决策失败: {e}")
            return RouteDecision(
                handler_name="chat_handler",
                confidence=0.0,
                metadata={"strategy": "semantic_router", "error": str(e)},
            )

    def _sync_route(self, query: str):
        """同步路由决策（用于在线程中执行）"""
        return self.router(query)

    def _get_handler_for_route(self, route_name: str) -> str:
        """根据路由名称获取对应的处理器名称"""
        # 从配置的路由中查找
        routes_config = (
            self.routes_config if self.routes_config else self._default_routes
        )

        for route_config in routes_config:
            if route_config["name"] == route_name:
                return route_config.get("handler", "chat_handler")

        # 默认映射规则
        route_handler_mapping = {
            "rag_query": "rag_handler",
            "casual_chat": "chat_handler",
            "system_command": "system_handler",
            "summary_request": "summary_handler",
            "tool_request": "tool_handler",
        }

        return route_handler_mapping.get(route_name, "chat_handler")

    @property
    def strategy_name(self) -> str:
        """策略名称"""
        return "semantic_router"

    async def cleanup(self) -> None:
        """清理资源"""
        try:
            if self.encoder and hasattr(self.encoder, "cleanup"):
                await self.encoder.cleanup()

            self.router = None
            self.encoder = None

            logger.info("SemanticRouter 策略资源已清理")
        except Exception as e:
            logger.warning(f"SemanticRouter 策略清理时出错: {e}")

    def update_routes(self, new_routes_config: List[Dict[str, Any]]) -> None:
        """更新路由配置（需要重新初始化）"""
        self.routes_config = new_routes_config
        logger.info(
            f"SemanticRouter 路由配置已更新，包含 {len(new_routes_config)} 个路由"
        )

    def get_route_info(self) -> Dict[str, Any]:
        """获取路由信息"""
        routes_config = (
            self.routes_config if self.routes_config else self._default_routes
        )

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
                    "utterances_count": len(route["utterances"]),
                }
                for route in routes_config
            ],
        }
