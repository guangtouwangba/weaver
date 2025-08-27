"""
Enhanced Chat Service

增强版聊天服务，集成了查询路由引擎，支持智能意图识别和路由分发。
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from .chat_service import ChatService, get_chat_service
from modules.routing import QueryRoutingEngine, RoutingEngineFactory
from modules.routing.config.config_manager import KeywordConfigManager
from modules.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


class EnhancedChatService(ChatService):
    """增强版聊天服务，集成路由引擎"""
    
    def __init__(self, session: AsyncSession = None, ai_client=None):
        super().__init__(session, ai_client)
        
        # 路由引擎相关
        self.routing_engine: Optional[QueryRoutingEngine] = None
        self.config_manager: Optional[KeywordConfigManager] = None
        self.routing_enabled = True
        self.routing_initialized = False
        
        # 路由统计
        self.routing_stats = {
            "total_routed": 0,
            "successful_routes": 0,
            "failed_routes": 0,
            "fallback_routes": 0
        }
        
    async def initialize_routing(
        self, 
        mode: str = "default",
        openai_client: Optional[Any] = None
    ) -> None:
        """
        初始化路由引擎
        
        Args:
            mode: 路由模式 ("default", "llm_first", "keyword_only")
            openai_client: OpenAI客户端
        """
        try:
            if self.routing_initialized:
                return
                
            logger.info(f"开始初始化路由引擎，模式: {mode}")
            
            # 使用当前服务的AI客户端（如果没有提供的话）
            if not openai_client:
                openai_client = self.ai_client
            
            # 创建路由引擎和配置管理器
            self.routing_engine, self.config_manager = await RoutingEngineFactory.create_with_config_manager(
                chat_service=self,
                openai_client=openai_client,
                config_dir="config/routing"
            )
            
            # 根据模式调整默认策略
            if mode == "llm_first" and openai_client:
                self.routing_engine.set_default_strategy("llm_intent")
            elif mode == "keyword_only":
                self.routing_engine.set_default_strategy("configurable_keyword")
            else:
                self.routing_engine.set_default_strategy("configurable_keyword")  # 默认使用关键词策略
            
            self.routing_initialized = True
            logger.info(f"路由引擎初始化完成，策略: {self.routing_engine.default_strategy}")
            
        except Exception as e:
            logger.error(f"路由引擎初始化失败: {e}")
            self.routing_enabled = False
            raise
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """增强版聊天处理，支持智能路由"""
        
        # 如果路由未启用，使用原始聊天服务
        if not self.routing_enabled or not self.routing_engine:
            logger.debug("路由未启用，使用原始聊天服务")
            return await super().chat(request)
        
        try:
            self.routing_stats["total_routed"] += 1
            
            # 准备路由上下文
            context = self._build_routing_context(request)
            
            # 执行路由决策
            routing_result = await self.routing_engine.route(request.message, context)
            
            # 记录路由决策
            logger.info(f"路由决策: handler={routing_result.decision.handler_name}, "
                       f"confidence={routing_result.decision.confidence:.3f}, "
                       f"route_type={routing_result.decision.metadata.get('route_type', 'unknown')}")
            
            # 根据路由结果处理查询
            response = await self._handle_routed_query(request, routing_result, context)
            
            self.routing_stats["successful_routes"] += 1
            return response
            
        except Exception as e:
            self.routing_stats["failed_routes"] += 1
            logger.error(f"路由处理失败，回退到原始聊天服务: {e}")
            
            # 回退到原始聊天服务
            return await self._fallback_to_original_chat(request, str(e))
    
    def _build_routing_context(self, request: ChatRequest) -> Dict[str, Any]:
        """构建路由上下文"""
        return {
            "topic_id": request.topic_id,
            "conversation_id": request.conversation_id,
            "search_type": request.search_type if request.search_type else "semantic",
            "context_window": request.context_window,
            "include_context": request.include_context,
            "user_id": getattr(request, "user_id", None),
            # 可以添加更多上下文信息，如用户偏好、历史行为等
        }
    
    async def _handle_routed_query(
        self,
        request: ChatRequest,
        routing_result: Any,
        context: Dict[str, Any]
    ) -> ChatResponse:
        """处理路由后的查询"""
        
        handler = routing_result.handler
        decision = routing_result.decision
        handler_name = decision.handler_name
        
        try:
            # 调用对应的处理器
            if handler and hasattr(handler, 'handle'):
                handler_response = await handler.handle(
                    request.message,
                    context,
                    decision.metadata
                )
                
                # 根据处理器类型转换响应
                if handler_name == "rag_handler":
                    return await self._convert_rag_response(handler_response, request, decision)
                elif handler_name == "system_handler":
                    return self._convert_system_response(handler_response, request, decision)
                elif handler_name == "tool_handler":
                    return self._convert_tool_response(handler_response, request, decision)
                else:  # chat_handler 或其他
                    return self._convert_chat_response(handler_response, request, decision)
                    
            else:
                # 处理器不可用，回退
                logger.warning(f"处理器不可用: {handler_name}")
                return await self._fallback_to_original_chat(request, "handler_unavailable")
                
        except Exception as e:
            logger.error(f"处理器执行失败 {handler_name}: {e}")
            return await self._fallback_to_original_chat(request, str(e))
    
    async def _convert_rag_response(
        self,
        handler_response: Dict[str, Any],
        request: ChatRequest,
        decision: Any
    ) -> ChatResponse:
        """转换RAG处理器响应"""
        
        # 如果RAG处理器返回了完整的ChatResponse格式
        if "message_id" in handler_response and "conversation_id" in handler_response:
            from modules.schemas.chat import AIMetadata
            
            return ChatResponse(
                message_id=handler_response["message_id"],
                conversation_id=handler_response["conversation_id"],
                content=handler_response["content"],
                retrieved_contexts=handler_response.get("retrieved_contexts", []),
                ai_metadata=AIMetadata(**handler_response.get("ai_metadata", {})) if handler_response.get("ai_metadata") else None,
                timestamp=datetime.now(timezone.utc)
            )
        else:
            # 简单响应格式，生成标准ChatResponse
            return self._create_standard_response(
                content=handler_response.get("content", "处理完成"),
                request=request,
                decision=decision,
                metadata=handler_response
            )
    
    def _convert_system_response(
        self,
        handler_response: Dict[str, Any],
        request: ChatRequest,
        decision: Any
    ) -> ChatResponse:
        """转换系统处理器响应"""
        return self._create_standard_response(
            content=handler_response.get("content", "系统命令执行完成"),
            request=request,
            decision=decision,
            metadata=handler_response
        )
    
    def _convert_tool_response(
        self,
        handler_response: Dict[str, Any],
        request: ChatRequest,
        decision: Any
    ) -> ChatResponse:
        """转换工具处理器响应"""
        return self._create_standard_response(
            content=handler_response.get("content", "工具调用完成"),
            request=request,
            decision=decision,
            metadata=handler_response
        )
    
    def _convert_chat_response(
        self,
        handler_response: Dict[str, Any],
        request: ChatRequest,
        decision: Any
    ) -> ChatResponse:
        """转换聊天处理器响应"""
        
        # 如果聊天处理器使用了AI服务，可能包含完整响应
        if "message_id" in handler_response:
            return self._convert_rag_response(handler_response, request, decision)
        else:
            return self._create_standard_response(
                content=handler_response.get("content", "聊天回复"),
                request=request,
                decision=decision,
                metadata=handler_response
            )
    
    def _create_standard_response(
        self,
        content: str,
        request: ChatRequest,
        decision: Any,
        metadata: Dict[str, Any] = None
    ) -> ChatResponse:
        """创建标准的ChatResponse"""
        import uuid
        from modules.schemas.chat import AIMetadata
        
        return ChatResponse(
            message_id=str(uuid.uuid4()),
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            content=content,
            retrieved_contexts=[],
            ai_metadata=AIMetadata(
                model="routing_engine",
                tokens_used=0,
                generation_time_ms=0,
                search_time_ms=0,
                temperature=0.0,
                max_tokens=0
            ),
            timestamp=datetime.now(timezone.utc)
        )
    
    async def _fallback_to_original_chat(self, request: ChatRequest, reason: str) -> ChatResponse:
        """回退到原始聊天服务"""
        self.routing_stats["fallback_routes"] += 1
        
        logger.info(f"回退到原始聊天服务，原因: {reason}")
        
        try:
            response = await super().chat(request)
            
            # 在响应中标记回退信息
            if hasattr(response, 'ai_metadata') and response.ai_metadata:
                response.ai_metadata.model += f" (fallback: {reason})"
                
            return response
        except Exception as e:
            logger.error(f"原始聊天服务也失败了: {e}")
            # 返回错误响应
            return self._create_error_response(request, str(e))
    
    def _create_error_response(self, request: ChatRequest, error: str) -> ChatResponse:
        """创建错误响应"""
        import uuid
        from modules.schemas.chat import AIMetadata
        
        return ChatResponse(
            message_id=str(uuid.uuid4()),
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            content=f"抱歉，处理您的请求时遇到了问题：{error}",
            retrieved_contexts=[],
            ai_metadata=AIMetadata(
                model="error_handler",
                tokens_used=0,
                generation_time_ms=0,
                search_time_ms=0,
                temperature=0.0,
                max_tokens=0
            ),
            timestamp=datetime.now(timezone.utc)
        )
    
    async def reload_routing_config(self) -> Dict[str, Any]:
        """重新加载路由配置"""
        if not self.config_manager:
            return {"success": False, "error": "配置管理器未初始化"}
        
        try:
            result = await self.config_manager.reload_keyword_config()
            logger.info("路由配置已重新加载")
            return result
        except Exception as e:
            logger.error(f"重新加载路由配置失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        stats = {
            "routing_enabled": self.routing_enabled,
            "routing_initialized": self.routing_initialized,
            **self.routing_stats
        }
        
        if self.routing_engine:
            engine_stats = self.routing_engine.get_stats()
            stats["engine_stats"] = engine_stats
        
        if self.config_manager:
            config_stats = await self.config_manager.get_statistics()
            stats["config_stats"] = config_stats
        
        return stats
    
    async def test_routing(self, query: str) -> Dict[str, Any]:
        """测试路由功能"""
        if not self.routing_engine:
            return {"success": False, "error": "路由引擎未初始化"}
        
        try:
            context = {"test_mode": True}
            routing_result = await self.routing_engine.route(query, context)
            
            return {
                "success": True,
                "query": query,
                "decision": routing_result.decision.to_dict(),
                "handler": routing_result.decision.handler_name,
                "confidence": routing_result.decision.confidence,
                "metadata": routing_result.decision.metadata
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def enable_routing(self) -> None:
        """启用路由功能"""
        self.routing_enabled = True
        logger.info("路由功能已启用")
    
    def disable_routing(self) -> None:
        """禁用路由功能"""
        self.routing_enabled = False
        logger.info("路由功能已禁用")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查（覆盖父类方法）"""
        # 调用父类健康检查
        base_health = {}
        try:
            if hasattr(super(), 'health_check'):
                base_health = await super().health_check()
        except:
            pass
        
        # 添加路由相关健康信息
        routing_health = {
            "routing_enabled": self.routing_enabled,
            "routing_initialized": self.routing_initialized,
            "routing_engine_available": self.routing_engine is not None,
            "config_manager_available": self.config_manager is not None
        }
        
        if self.routing_engine:
            try:
                engine_health = await self.routing_engine.health_check()
                routing_health["engine_health"] = engine_health
            except Exception as e:
                routing_health["engine_health_error"] = str(e)
        
        return {**base_health, **routing_health}


# 便捷函数
async def create_enhanced_chat_service(
    session: AsyncSession = None,
    ai_client=None,
    routing_mode: str = "default"
) -> EnhancedChatService:
    """
    创建增强版聊天服务
    
    Args:
        session: 数据库会话
        ai_client: AI客户端
        routing_mode: 路由模式
        
    Returns:
        EnhancedChatService: 增强版聊天服务实例
    """
    service = EnhancedChatService(session, ai_client)
    await service.initialize()
    await service.initialize_routing(routing_mode, ai_client)
    return service


# 全局缓存的服务实例
_enhanced_chat_service_instance = None

async def get_enhanced_chat_service() -> EnhancedChatService:
    """获取增强版ChatService实例（单例模式，延迟初始化）"""
    global _enhanced_chat_service_instance
    
    if _enhanced_chat_service_instance is None:
        # 创建服务实例
        service = EnhancedChatService()
        
        # 初始化基础服务
        await service.initialize()
        
        # 初始化路由引擎
        await service.initialize_routing()
        
        _enhanced_chat_service_instance = service
    
    return _enhanced_chat_service_instance