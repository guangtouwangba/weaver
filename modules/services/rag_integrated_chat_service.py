"""
RAG集成聊天服务

集成新的模块化RAG架构的聊天服务，提供更强大的检索增强生成能力。
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from .chat_service import ChatService
from modules.schemas.chat import ChatRequest, ChatResponse, RetrievedContext, AIMetadata
from modules.routing import QueryRoutingEngine, RoutingEngineFactory
from modules.routing.config.config_manager import KeywordConfigManager
from modules.rag.factory import RAGPipelineFactory, create_rag_pipeline_from_config, get_default_config
from modules.rag.base import IRAGPipeline, RAGStrategy, RetrievedDocument
from modules.vector_store.weaviate_service import WeaviateVectorStore
from modules.embedding.openai_service import OpenAIEmbeddingService
from config.settings import get_config

logger = logging.getLogger(__name__)


class RAGIntegratedChatService(ChatService):
    """集成新RAG架构的聊天服务"""
    
    def __init__(self, session: AsyncSession = None, ai_client=None):
        super().__init__(session, ai_client)
        
        # 新RAG组件
        self.rag_pipeline: Optional[IRAGPipeline] = None
        self.rag_config: Dict[str, Any] = {}
        self.rag_enabled = True
        self.rag_initialized = False
        
        # 路由引擎相关（从EnhancedChatService迁移）
        self.routing_engine: Optional[QueryRoutingEngine] = None
        self.config_manager: Optional[KeywordConfigManager] = None
        self.routing_enabled = True
        self.routing_initialized = False
        
        # RAG统计
        self.rag_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_processing_time": 0.0,
            "avg_confidence": 0.0
        }
        
        # 路由统计（从EnhancedChatService迁移）
        self.routing_stats = {
            "total_routed": 0,
            "successful_routes": 0,
            "failed_routes": 0,
            "fallback_routes": 0
        }
        
        logger.info("RAGIntegratedChatService 初始化")
    
    async def initialize_rag(
        self, 
        pipeline_type: str = "adaptive",
        custom_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        初始化新的RAG管道
        
        Args:
            pipeline_type: RAG管道类型 ("simple", "hybrid", "adaptive", "multi_hop")
            custom_config: 自定义配置
        """
        try:
            if self.rag_initialized:
                return
                
            logger.info(f"开始初始化RAG管道，类型: {pipeline_type}")
            
            # 确保基础服务已初始化
            await self.initialize()
            
            # 获取配置
            if custom_config:
                self.rag_config = custom_config
            else:
                self.rag_config = get_default_config(pipeline_type)
            
            # 创建RAG管道
            self.rag_pipeline = await create_rag_pipeline_from_config(
                pipeline_type=pipeline_type,
                vector_store=self._vector_store,
                embedding_service=self._embedding_service,
                db_session=self.session,
                config=self.rag_config
            )
            
            # 初始化管道
            await self.rag_pipeline.initialize()
            
            self.rag_initialized = True
            logger.info(f"RAG管道初始化完成: {pipeline_type}")
            
            # 健康检查
            health = await self.rag_pipeline.health_check()
            logger.info(f"RAG管道健康状态: {health.get('initialized', False)}")
            
        except Exception as e:
            logger.error(f"RAG管道初始化失败: {e}")
            self.rag_enabled = False
            raise
    
    async def initialize_routing(
        self, 
        mode: str = "default",
        openai_client: Optional[Any] = None
    ) -> None:
        """
        初始化路由引擎（从EnhancedChatService迁移）
        
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
            
            # 构建语义路由配置
            semantic_config = self._build_semantic_config()
            
            # 创建路由引擎和配置管理器
            self.routing_engine, self.config_manager = await RoutingEngineFactory.create_with_config_manager(
                chat_service=self,
                openai_client=openai_client,
                config_dir="config/routing",
                semantic_config=semantic_config
            )
            
            # 智能策略优先级：LLM首选 > 语义路由 > 关键词匹配
            strategy_set = False
            
            # 1. 首选：LLM意图识别策略（如果可用）
            if openai_client and "llm_intent" in self.routing_engine.strategies:
                self.routing_engine.set_default_strategy("llm_intent")
                logger.info("🧠 启用LLM意图识别策略作为默认策略（首选）")
                strategy_set = True
                
            # 2. 次选：语义路由策略（如果LLM不可用但语义路由可用）
            elif not strategy_set and semantic_config and semantic_config.get("enabled", False):
                if "semantic_router" in self.routing_engine.strategies:
                    self.routing_engine.set_default_strategy("semantic_router")
                    logger.info("🎯 启用语义路由策略作为默认策略（次选）")
                    strategy_set = True
                else:
                    logger.warning("语义路由策略注册失败")
                    
            # 3. 回退：关键词策略（最后选择）
            if not strategy_set:
                self.routing_engine.set_default_strategy("configurable_keyword")
                logger.info("🔤 启用关键词策略作为默认策略（回退选择）")
            
            # 特殊模式覆盖
            if mode == "keyword_only":
                self.routing_engine.set_default_strategy("configurable_keyword")
                logger.info("🔧 强制使用关键词策略（keyword_only模式）")
            elif mode == "llm_first" and openai_client:
                self.routing_engine.set_default_strategy("llm_intent") 
                logger.info("🔧 强制使用LLM策略（llm_first模式）")
            
            # 确保策略设置成功
            if not hasattr(self.routing_engine, 'default_strategy') or not self.routing_engine.default_strategy:
                self.routing_engine.set_default_strategy("configurable_keyword")
                logger.warning("⚠️ 回退到关键词策略作为最终默认选择")
            
            self.routing_initialized = True
            logger.info(f"🚀 路由引擎初始化完成，策略: {self.routing_engine.default_strategy}")
            
        except Exception as e:
            logger.error(f"路由引擎初始化失败: {e}")
            self.routing_enabled = False
            raise
    
    def _build_semantic_config(self) -> Dict[str, Any]:
        """构建语义路由配置（从EnhancedChatService迁移）"""
        try:
            from config.settings import get_config
            config = get_config()
            
            # 检查是否启用语义路由
            semantic_enabled = getattr(config, 'semantic_router_enabled', True)
            
            if not semantic_enabled:
                logger.info("语义路由在配置中被禁用")
                return {"enabled": False}
            
            # 构建语义路由配置
            semantic_config = {
                "enabled": True,
                "model": getattr(config, 'semantic_router_model', 'text-embedding-3-small'),
                "threshold": getattr(config, 'semantic_router_threshold', 0.75),
                "routes_file": "config/routing/semantic_routes.yaml"
            }
            
            logger.info(f"语义路由配置: {semantic_config}")
            return semantic_config
            
        except Exception as e:
            logger.warning(f"构建语义路由配置失败: {e}")
            return {"enabled": False}
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        处理聊天请求 - 使用新的RAG架构
        """
        start_time = time.time()
        
        try:
            # 确保服务已初始化
            await self._ensure_initialized()
            
            # 如果启用了路由，先进行路由处理
            if self.routing_enabled and self.routing_initialized:
                try:
                    routed_response = await self._handle_routing(request)
                    if routed_response:
                        return routed_response
                except Exception as e:
                    logger.warning(f"路由处理失败，回退到RAG处理: {e}")
            
            # 使用新的RAG管道处理
            if self.rag_enabled and self.rag_initialized:
                return await self._handle_rag_chat(request)
            else:
                # 回退到原有的聊天处理
                logger.warning("RAG未启用，使用传统聊天处理")
                return await super().chat(request)
                
        except Exception as e:
            logger.error(f"聊天处理失败: {e}")
            # 返回错误响应
            return ChatResponse(
                message_id=str(uuid.uuid4()),
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                content=f"抱歉，处理您的请求时出现了错误: {str(e)}",
                confidence=0.0,
                retrieved_contexts=[],
                ai_metadata=AIMetadata(
                    model="error",
                    tokens_used=0,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            )
    
    async def _handle_rag_chat(self, request: ChatRequest) -> ChatResponse:
        """使用新RAG架构处理聊天请求"""
        start_time = time.time()
        
        try:
            # 准备用户上下文
            user_context = {
                "top_k": request.max_results,
                "score_threshold": request.score_threshold,
                "rerank_top_k": min(request.max_results, 10),  # 重排序数量
                "topic_id": request.topic_id,
                "search_type": request.search_type.value if request.search_type else "semantic"
            }
            
            # 准备对话历史
            conversation_history = []
            if request.context_window > 0 and request.conversation_id:
                # 获取对话历史（这里可以从数据库获取）
                conversation_history = await self._get_conversation_history(
                    request.conversation_id, 
                    request.context_window * 2
                )
            
            # 调用RAG管道
            rag_response = await self.rag_pipeline.process(
                query=request.message,
                user_context=user_context,
                conversation_history=conversation_history
            )
            
            # 转换检索到的文档
            retrieved_contexts = []
            for doc in rag_response.retrieved_documents:
                context = RetrievedContext(
                    content=doc.content,
                    source=doc.source,
                    score=doc.score,
                    metadata=doc.metadata,
                    chunk_id=doc.id,
                    document_id=doc.metadata.get("document_id", ""),
                    title=doc.metadata.get("title", "")
                )
                retrieved_contexts.append(context)
            
            # 更新统计信息
            self._update_rag_stats(rag_response)
            
            # 构建响应
            processing_time = (time.time() - start_time) * 1000
            
            response = ChatResponse(
                message_id=str(uuid.uuid4()),
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                content=rag_response.answer,
                confidence=rag_response.confidence,
                retrieved_contexts=retrieved_contexts,
                ai_metadata=AIMetadata(
                    model=self.rag_config.get("generator", {}).get("model", "unknown"),
                    tokens_used=rag_response.metadata.get("tokens_used", 0),
                    processing_time_ms=processing_time,
                    rag_metadata={
                        "strategy": rag_response.metadata.get("strategy", "unknown"),
                        "documents_retrieved": len(retrieved_contexts),
                        "processing_components": list(rag_response.metadata.get("components_used", [])),
                        "rag_processing_time": rag_response.processing_time_ms
                    }
                )
            )
            
            # 保存对话记录（如果需要）
            if request.save_conversation:
                await self._save_conversation_message(request, response)
            
            logger.info(f"RAG聊天处理完成: 耗时{processing_time:.1f}ms, "
                       f"置信度{rag_response.confidence:.3f}, "
                       f"检索文档{len(retrieved_contexts)}个")
            
            return response
            
        except Exception as e:
            logger.error(f"RAG聊天处理失败: {e}")
            raise
    
    async def _handle_routing(self, request: ChatRequest) -> Optional[ChatResponse]:
        """处理路由逻辑"""
        try:
            # 使用路由引擎处理查询
            route_result = await self.routing_engine.route_query(
                query=request.message,
                context={
                    "conversation_id": request.conversation_id,
                    "topic_id": request.topic_id,
                    "user_context": request.dict()
                }
            )
            
            # 更新路由统计
            self.routing_stats["total_routed"] += 1
            
            if route_result and route_result.get("content"):
                self.routing_stats["successful_routes"] += 1
                
                # 构建路由响应
                return ChatResponse(
                    message_id=str(uuid.uuid4()),
                    conversation_id=request.conversation_id or str(uuid.uuid4()),
                    content=route_result["content"],
                    confidence=route_result.get("confidence", 0.8),
                    retrieved_contexts=self._convert_routing_contexts(
                        route_result.get("retrieved_contexts", [])
                    ),
                    ai_metadata=AIMetadata(
                        model="routing_engine",
                        tokens_used=0,
                        processing_time_ms=route_result.get("processing_time_ms", 0),
                        routing_metadata={
                            "route_type": route_result.get("route_type", "unknown"),
                            "strategy_used": route_result.get("strategy_used", "unknown"),
                            "confidence": route_result.get("confidence", 0.0)
                        }
                    )
                )
            else:
                self.routing_stats["fallback_routes"] += 1
                return None
                
        except Exception as e:
            self.routing_stats["failed_routes"] += 1
            logger.warning(f"路由处理失败: {e}")
            return None
    
    def _convert_routing_contexts(self, routing_contexts: List[Dict]) -> List[RetrievedContext]:
        """转换路由上下文为标准格式"""
        contexts = []
        for ctx in routing_contexts:
            if isinstance(ctx, dict):
                context = RetrievedContext(
                    content=ctx.get("content", ""),
                    source=ctx.get("source", "routing"),
                    score=ctx.get("score", 0.0),
                    metadata=ctx.get("metadata", {}),
                    chunk_id=ctx.get("id", ""),
                    document_id=ctx.get("document_id", ""),
                    title=ctx.get("title", "")
                )
                contexts.append(context)
        return contexts
    
    async def _ensure_initialized(self) -> None:
        """确保所有服务都已初始化"""
        if not self._initialized:
            await self.initialize()
        
        if not self.rag_initialized and self.rag_enabled:
            await self.initialize_rag()
        
        if not self.routing_initialized and self.routing_enabled:
            await self.initialize_routing()
    
    def _update_rag_stats(self, rag_response) -> None:
        """更新RAG统计信息"""
        self.rag_stats["total_queries"] += 1
        
        if rag_response.answer:
            self.rag_stats["successful_queries"] += 1
        else:
            self.rag_stats["failed_queries"] += 1
        
        # 更新平均处理时间
        total_time = (self.rag_stats["avg_processing_time"] * 
                     (self.rag_stats["total_queries"] - 1) + 
                     rag_response.processing_time_ms)
        self.rag_stats["avg_processing_time"] = total_time / self.rag_stats["total_queries"]
        
        # 更新平均置信度
        total_confidence = (self.rag_stats["avg_confidence"] * 
                           (self.rag_stats["successful_queries"] - 1) + 
                           rag_response.confidence)
        if self.rag_stats["successful_queries"] > 0:
            self.rag_stats["avg_confidence"] = total_confidence / self.rag_stats["successful_queries"]
    
    async def _get_conversation_history(
        self, 
        conversation_id: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """获取对话历史"""
        try:
            # 这里应该从数据库获取对话历史
            # 暂时返回空列表，可以根据实际需求实现
            return []
        except Exception as e:
            logger.warning(f"获取对话历史失败: {e}")
            return []
    
    async def _save_conversation_message(
        self, 
        request: ChatRequest, 
        response: ChatResponse
    ) -> None:
        """保存对话消息"""
        try:
            # 这里应该保存对话到数据库
            # 可以根据实际需求实现
            pass
        except Exception as e:
            logger.warning(f"保存对话失败: {e}")
    
    async def get_rag_stats(self) -> Dict[str, Any]:
        """获取RAG统计信息"""
        stats = self.rag_stats.copy()
        
        if self.rag_pipeline:
            try:
                pipeline_metrics = await self.rag_pipeline.get_metrics()
                stats["pipeline_metrics"] = {
                    "total_processing_time_ms": pipeline_metrics.total_processing_time_ms,
                    "query_processing_time_ms": pipeline_metrics.query_processing_time_ms,
                    "retrieval_time_ms": pipeline_metrics.retrieval_time_ms,
                    "reranking_time_ms": pipeline_metrics.reranking_time_ms,
                    "generation_time_ms": pipeline_metrics.generation_time_ms
                }
            except Exception as e:
                logger.warning(f"获取管道指标失败: {e}")
        
        return stats
    
    async def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        return self.routing_stats.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = {
            "service": "rag_integrated_chat_service",
            "initialized": self._initialized,
            "rag_enabled": self.rag_enabled,
            "rag_initialized": self.rag_initialized,
            "routing_enabled": self.routing_enabled,
            "routing_initialized": self.routing_initialized
        }
        
        # RAG管道健康检查
        if self.rag_pipeline:
            try:
                rag_health = await self.rag_pipeline.health_check()
                health["rag_pipeline"] = rag_health
            except Exception as e:
                health["rag_pipeline"] = {"status": "unhealthy", "error": str(e)}
        
        # 基础服务健康检查
        try:
            base_health = await super().health_check() if hasattr(super(), 'health_check') else {}
            health["base_service"] = base_health
        except Exception as e:
            health["base_service"] = {"status": "unhealthy", "error": str(e)}
        
        return health
    
    async def switch_rag_pipeline(
        self, 
        pipeline_type: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """动态切换RAG管道"""
        try:
            logger.info(f"切换RAG管道到: {pipeline_type}")
            
            # 清理现有管道
            if self.rag_pipeline:
                await self.rag_pipeline.cleanup()
            
            # 重置状态
            self.rag_initialized = False
            
            # 初始化新管道
            await self.initialize_rag(pipeline_type, config)
            
            logger.info(f"RAG管道切换完成: {pipeline_type}")
            
        except Exception as e:
            logger.error(f"切换RAG管道失败: {e}")
            self.rag_enabled = False
            raise
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            if self.rag_pipeline:
                await self.rag_pipeline.cleanup()
            
            # 调用父类清理方法
            if hasattr(super(), 'cleanup'):
                await super().cleanup()
                
            logger.info("RAGIntegratedChatService 资源清理完成")
            
        except Exception as e:
            logger.warning(f"资源清理失败: {e}")


# 工厂函数
async def create_rag_integrated_chat_service(
    session: AsyncSession = None,
    ai_client = None,
    pipeline_type: str = "adaptive",
    rag_config: Optional[Dict[str, Any]] = None,
    enable_routing: bool = True
) -> RAGIntegratedChatService:
    """创建RAG集成聊天服务"""
    
    service = RAGIntegratedChatService(session, ai_client)
    
    # 初始化RAG
    await service.initialize_rag(pipeline_type, rag_config)
    
    # 初始化路由（如果启用）
    if enable_routing:
        await service.initialize_routing()
    
    return service
