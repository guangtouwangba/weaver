"""
Summary Query Handler

摘要查询处理器，专门处理需要高级概念和摘要信息的查询。
"""

import logging
from typing import Dict, Any, Optional

from .base import BaseQueryHandler

logger = logging.getLogger(__name__)


class SummaryQueryHandler(BaseQueryHandler):
    """摘要查询处理器"""
    
    def __init__(self, chat_service: Optional[Any] = None):
        super().__init__("summary_handler")
        self.chat_service = chat_service
        
        # 摘要特定配置
        self.default_max_results = 5  # 摘要查询通常需要更少的结果
        self.default_score_threshold = 0.75  # 摘要查询需要更高的相关性
        self.high_confidence_threshold = 0.85
        
    def set_chat_service(self, chat_service: Any) -> None:
        """设置聊天服务"""
        self.chat_service = chat_service
        logger.info("SummaryQueryHandler 聊天服务已设置")
        
    async def _handle_query(
        self,
        query: str,
        context: Dict[str, Any],
        route_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理摘要查询"""
        
        if not self.chat_service:
            return {
                "content": "抱歉，摘要服务暂时不可用。",
                "error": "summary_service_not_available"
            }
        
        try:
            # 根据路由置信度调整检索参数
            confidence = route_metadata.get("confidence", 0.5)
            max_results = self._get_max_results(confidence)
            score_threshold = self._get_score_threshold(confidence)
            
            logger.info(f"摘要查询参数: max_results={max_results}, score_threshold={score_threshold}, confidence={confidence}")
            
            # 构建摘要查询请求
            summary_request = self._build_summary_request(query, context, max_results, score_threshold)
            
            # 调用摘要搜索功能
            if hasattr(self.chat_service, 'chat_with_summary'):
                response = await self.chat_service.chat_with_summary(summary_request)
                
                # 包装响应
                return {
                    "content": response.content,
                    "metadata": {
                        "handler": "summary",
                        "search_type": "summary",
                        "confidence": confidence,
                        "results_count": getattr(response, 'context_count', 0),
                        "processing_time": getattr(response, 'processing_time', 0)
                    },
                    "context": getattr(response, 'retrieved_context', [])
                }
            else:
                # 回退到普通RAG，但使用摘要优化的参数
                logger.warning("摘要搜索功能不可用，回退到普通RAG")
                return await self._fallback_to_rag(query, context, route_metadata)
                
        except Exception as e:
            logger.error(f"摘要查询处理失败: {e}")
            return {
                "content": f"抱歉，处理您的摘要查询时出现错误: {str(e)}",
                "error": "summary_query_failed",
                "metadata": {
                    "handler": "summary",
                    "error_type": type(e).__name__
                }
            }
    
    def _get_max_results(self, confidence: float) -> int:
        """根据置信度调整最大结果数量"""
        if confidence >= self.high_confidence_threshold:
            return max(3, self.default_max_results - 2)  # 高置信度查询，更少结果
        elif confidence >= 0.6:
            return self.default_max_results
        else:
            return min(8, self.default_max_results + 3)  # 低置信度，更多结果
    
    def _get_score_threshold(self, confidence: float) -> float:
        """根据置信度调整分数阈值"""
        if confidence >= self.high_confidence_threshold:
            return self.default_score_threshold
        elif confidence >= 0.6:
            return max(0.6, self.default_score_threshold - 0.1)
        else:
            return max(0.5, self.default_score_threshold - 0.2)
    
    def _build_summary_request(
        self,
        query: str,
        context: Dict[str, Any],
        max_results: int,
        score_threshold: float
    ) -> Dict[str, Any]:
        """构建摘要查询请求"""
        
        request = {
            "query": query,
            "search_type": "summary",
            "max_results": max_results,
            "score_threshold": score_threshold,
            "context": context
        }
        
        # 添加摘要特定的提示优化
        enhanced_query = f"""请基于相关文档的摘要信息回答以下问题。
        重点关注高级概念、主要观点和总体趋势，而不是具体的细节。
        
        用户问题: {query}"""
        
        request["enhanced_query"] = enhanced_query
        request["response_style"] = "summary"  # 指导AI生成摘要风格的回答
        
        # 提取topic_id等上下文信息
        if "topic_id" in context:
            request["topic_id"] = context["topic_id"]
        
        return request
    
    async def _fallback_to_rag(
        self,
        query: str,
        context: Dict[str, Any],
        route_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """回退到普通RAG查询"""
        try:
            # 使用高级摘要提示来优化普通RAG
            enhanced_query = f"""请从高层次角度总结和回答以下问题，
            重点关注主要概念和趋势，避免过多具体细节：
            
            {query}"""
            
            # 构建RAG请求
            chat_request = {
                "query": enhanced_query,
                "search_type": "vector",
                "max_results": self.default_max_results,
                "score_threshold": self.default_score_threshold,
                "context": context
            }
            
            if hasattr(self.chat_service, 'chat'):
                response = await self.chat_service.chat(chat_request)
                
                return {
                    "content": response.content,
                    "metadata": {
                        "handler": "summary_fallback",
                        "search_type": "vector",
                        "fallback": True
                    },
                    "context": getattr(response, 'retrieved_context', [])
                }
            else:
                return {
                    "content": "抱歉，无法处理您的摘要查询。",
                    "error": "no_available_service"
                }
                
        except Exception as e:
            logger.error(f"摘要查询回退失败: {e}")
            return {
                "content": "抱歉，处理查询时出现错误。",
                "error": "fallback_failed"
            }
    
    def get_supported_query_types(self) -> list:
        """获取支持的查询类型"""
        return [
            "summary",
            "overview", 
            "概述",
            "总结",
            "主要内容",
            "核心观点",
            "整体情况",
            "大致内容"
        ]
    
    def can_handle_query(self, query: str, context: Dict[str, Any]) -> float:
        """判断是否能处理查询并返回置信度"""
        query_lower = query.lower()
        
        # 摘要关键词检测
        summary_keywords = [
            "总结", "概述", "摘要", "概括", "整体", "全面", "主要", "核心",
            "summary", "overview", "main points", "key insights", "overall",
            "主要内容", "核心观点", "总体情况", "大致内容"
        ]
        
        confidence = 0.0
        for keyword in summary_keywords:
            if keyword in query_lower:
                confidence += 0.3
        
        # 长度检测 - 摘要查询通常较短且概念性
        if len(query) < 50:
            confidence += 0.1
        
        # 避免具体细节的查询
        detail_keywords = ["具体", "详细", "怎么", "如何", "什么时候", "where", "when", "how"]
        has_details = any(keyword in query_lower for keyword in detail_keywords)
        if not has_details:
            confidence += 0.2
        
        return min(1.0, confidence)