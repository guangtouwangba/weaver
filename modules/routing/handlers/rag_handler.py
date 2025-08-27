"""
RAG Query Handler

RAG知识查询处理器，专门处理需要检索知识库的查询。
"""

import logging
from typing import Dict, Any, Optional

from .base import BaseQueryHandler

logger = logging.getLogger(__name__)


class RAGQueryHandler(BaseQueryHandler):
    """RAG查询处理器"""
    
    def __init__(self, chat_service: Optional[Any] = None):
        super().__init__("rag_handler")
        self.chat_service = chat_service
        
        # RAG特定配置
        self.default_max_results = 8
        self.default_score_threshold = 0.7
        self.high_confidence_threshold = 0.9
        
    def set_chat_service(self, chat_service: Any) -> None:
        """设置聊天服务"""
        self.chat_service = chat_service
        logger.info("RAGQueryHandler 聊天服务已设置")
        
    async def _handle_query(
        self,
        query: str,
        context: Dict[str, Any],
        route_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理RAG查询"""
        
        if not self.chat_service:
            return {
                "content": "抱歉，知识库服务暂时不可用。",
                "error": "chat_service_not_available"
            }
        
        try:
            # 根据路由置信度调整检索参数
            confidence = route_metadata.get("confidence", 0.5)
            max_results = self._get_max_results(confidence)
            score_threshold = self._get_score_threshold(confidence)
            
            logger.info(f"RAG查询参数: max_results={max_results}, score_threshold={score_threshold}, confidence={confidence}")
            
            # 构建聊天请求
            chat_request = self._build_chat_request(query, context, max_results, score_threshold)
            
            # 调用现有的聊天服务
            if hasattr(self.chat_service, 'chat'):
                response = await self.chat_service.chat(chat_request)
                
                return {
                    "content": response.content,
                    "retrieved_contexts": [ctx.model_dump() for ctx in response.retrieved_contexts],
                    "ai_metadata": response.ai_metadata.model_dump() if response.ai_metadata else {},
                    "message_id": response.message_id,
                    "conversation_id": response.conversation_id,
                    "rag_optimized": True,
                    "optimization_params": {
                        "max_results": max_results,
                        "score_threshold": score_threshold,
                        "confidence_based": True
                    }
                }
            else:
                return {
                    "content": "聊天服务接口不兼容。",
                    "error": "incompatible_chat_service"
                }
                
        except Exception as e:
            logger.error(f"RAG查询处理失败: {e}")
            return {
                "content": f"抱歉，检索知识库时遇到问题：{str(e)}",
                "error": str(e)
            }
    
    def _get_max_results(self, confidence: float) -> int:
        """根据置信度确定最大检索结果数"""
        if confidence >= self.high_confidence_threshold:
            return self.default_max_results + 2  # 高置信度，检索更多结果
        elif confidence >= 0.7:
            return self.default_max_results
        else:
            return max(self.default_max_results - 2, 3)  # 低置信度，检索较少结果
    
    def _get_score_threshold(self, confidence: float) -> float:
        """根据置信度确定相似度阈值"""
        if confidence >= self.high_confidence_threshold:
            return self.default_score_threshold - 0.1  # 高置信度，放宽阈值
        elif confidence >= 0.7:
            return self.default_score_threshold
        else:
            return self.default_score_threshold + 0.1  # 低置信度，提高阈值
    
    def _build_chat_request(
        self,
        query: str,
        context: Dict[str, Any],
        max_results: int,
        score_threshold: float
    ) -> Any:
        """构建聊天请求对象"""
        # 导入ChatRequest类
        try:
            from modules.schemas.chat import ChatRequest, SearchType
            
            return ChatRequest(
                message=query,
                topic_id=context.get("topic_id"),
                conversation_id=context.get("conversation_id"),
                search_type=SearchType.SEMANTIC,
                max_results=max_results,
                score_threshold=score_threshold,
                include_context=True,
                context_window=context.get("context_window", 5)
            )
        except ImportError:
            # 如果无法导入，创建字典格式
            return {
                "message": query,
                "topic_id": context.get("topic_id"),
                "conversation_id": context.get("conversation_id"),
                "search_type": "semantic",
                "max_results": max_results,
                "score_threshold": score_threshold,
                "include_context": True,
                "context_window": context.get("context_window", 5)
            }
    
    def update_rag_config(
        self,
        default_max_results: int = None,
        default_score_threshold: float = None,
        high_confidence_threshold: float = None
    ) -> None:
        """更新RAG配置"""
        if default_max_results is not None:
            self.default_max_results = max(1, min(20, default_max_results))
        if default_score_threshold is not None:
            self.default_score_threshold = max(0.0, min(1.0, default_score_threshold))
        if high_confidence_threshold is not None:
            self.high_confidence_threshold = max(0.0, min(1.0, high_confidence_threshold))
            
        logger.info(f"RAG配置已更新: max_results={self.default_max_results}, "
                   f"score_threshold={self.default_score_threshold}, "
                   f"high_confidence_threshold={self.high_confidence_threshold}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        base_health = await super().health_check()
        
        base_health.update({
            "chat_service_available": self.chat_service is not None,
            "rag_config": {
                "default_max_results": self.default_max_results,
                "default_score_threshold": self.default_score_threshold,
                "high_confidence_threshold": self.high_confidence_threshold
            }
        })
        
        return base_health