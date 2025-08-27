"""
Chat Handler

普通聊天处理器，处理闲聊、情感交流等对话。
"""

import logging
from typing import Dict, Any, Optional, List

from .base import BaseQueryHandler

logger = logging.getLogger(__name__)


class ChatHandler(BaseQueryHandler):
    """普通聊天处理器"""
    
    def __init__(self, chat_service: Optional[Any] = None):
        super().__init__("chat_handler")
        self.chat_service = chat_service
        
        # 预设回复模板
        self.greeting_responses = {
            "你好": ["你好！很高兴和你聊天。", "你好！有什么可以帮助你的吗？", "嗨！今天过得怎么样？"],
            "早上好": ["早上好！新的一天开始了！", "早上好！希望你今天有个好心情！"],
            "下午好": ["下午好！下午过得如何？", "下午好！需要什么帮助吗？"],
            "晚上好": ["晚上好！晚上有什么计划吗？", "晚上好！今天过得怎么样？"],
            "再见": ["再见！期待下次聊天！", "再见！保重！", "拜拜！有需要随时找我！"],
            "谢谢": ["不客气！很高兴能帮到你。", "不用谢！这是我应该做的。", "很乐意为你服务！"],
        }
        
        self.emotional_responses = {
            "开心": ["那太好了！能分享一下是什么让你这么开心吗？", "很高兴听到你心情不错！"],
            "高兴": ["真为你感到高兴！", "看到你开心我也很开心！"],
            "难过": ["听起来你心情不太好，需要聊聊吗？", "有什么事情让你难过了吗？我可以听你说说。"],
            "伤心": ["我能理解你的感受，有什么可以帮助你的吗？", "伤心是正常的情感，慢慢就会好起来的。"],
            "生气": ["听起来你很生气，深呼吸一下，告诉我发生了什么？", "生气的时候先冷静一下，也许我能帮你分析分析。"],
            "无聊": ["无聊的时候可以做很多事情呀！比如听音乐、看书、运动...", "要不我们聊点有趣的话题？"],
        }
        
    def set_chat_service(self, chat_service: Any) -> None:
        """设置聊天服务"""
        self.chat_service = chat_service
        logger.info("ChatHandler 聊天服务已设置")
        
    async def _handle_query(
        self,
        query: str,
        context: Dict[str, Any],
        route_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理聊天查询"""
        
        # 首先尝试模板回复
        template_response = self._try_template_response(query, route_metadata)
        if template_response:
            return template_response
        
        # 如果有聊天服务，使用AI生成回复
        if self.chat_service:
            return await self._generate_ai_response(query, context, route_metadata)
        
        # 否则使用简单回复
        return self._generate_simple_response(query, context, route_metadata)
    
    def _try_template_response(self, query: str, route_metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """尝试使用模板回复"""
        query_lower = query.lower().strip()
        
        # 检查匹配的模式
        matched_patterns = route_metadata.get("matched_patterns", {}).get("matches", [])
        
        # 问候语匹配
        for keyword in self.greeting_responses:
            if keyword in query_lower or keyword in matched_patterns:
                import random
                response = random.choice(self.greeting_responses[keyword])
                return {
                    "content": response,
                    "template_match": keyword,
                    "response_type": "greeting"
                }
        
        # 情感关键词匹配
        for emotion in self.emotional_responses:
            if emotion in query_lower or emotion in matched_patterns:
                import random
                response = random.choice(self.emotional_responses[emotion])
                return {
                    "content": response,
                    "template_match": emotion,
                    "response_type": "emotional"
                }
        
        return None
    
    async def _generate_ai_response(
        self,
        query: str,
        context: Dict[str, Any],
        route_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用AI生成回复"""
        try:
            # 构建聊天请求，不包含检索
            chat_request = self._build_chat_request(query, context, include_context=False)
            
            if hasattr(self.chat_service, 'chat'):
                response = await self.chat_service.chat(chat_request)
                
                return {
                    "content": response.content,
                    "message_id": response.message_id,
                    "conversation_id": response.conversation_id,
                    "ai_metadata": response.ai_metadata.model_dump() if response.ai_metadata else {},
                    "response_type": "ai_generated",
                    "retrieval_used": False
                }
            else:
                return self._generate_simple_response(query, context, route_metadata)
                
        except Exception as e:
            logger.error(f"AI回复生成失败: {e}")
            return self._generate_simple_response(query, context, route_metadata)
    
    def _generate_simple_response(
        self,
        query: str,
        context: Dict[str, Any],
        route_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成简单回复"""
        
        # 分析查询类型
        if any(word in query for word in ["？", "?", "吗", "呢", "什么", "如何", "怎么"]):
            responses = [
                "这是个很好的问题！不过我可能需要更多信息才能更好地回答你。",
                "我理解你的疑问，但这个问题可能需要更专业的知识来回答。",
                "有意思的问题！你能告诉我更多相关的背景信息吗？"
            ]
        elif any(word in query for word in ["好", "是的", "对", "嗯", "ok", "OK"]):
            responses = [
                "很好！还有什么其他的事情吗？",
                "明白了，还需要什么帮助吗？",
                "好的！继续说吧。"
            ]
        elif any(word in query for word in ["不", "没有", "不对", "不是"]):
            responses = [
                "我明白了，那你觉得应该是什么样的呢？",
                "好的，能告诉我正确的情况是怎样的吗？",
                "了解，那让我重新理解一下..."
            ]
        else:
            responses = [
                "我听到你说的了，虽然我可能不能给出完美的回答，但我很乐意和你聊天。",
                "有趣的话题！虽然我的知识有限，但我们可以继续交流。",
                "谢谢你的分享！还有什么想聊的吗？"
            ]
        
        import random
        response = random.choice(responses)
        
        return {
            "content": response,
            "response_type": "simple_generated",
            "fallback_reason": "no_ai_service"
        }
    
    def _build_chat_request(
        self,
        query: str,
        context: Dict[str, Any],
        include_context: bool = False
    ) -> Any:
        """构建聊天请求"""
        try:
            from modules.schemas.chat import ChatRequest, SearchType
            
            return ChatRequest(
                message=query,
                topic_id=context.get("topic_id"),
                conversation_id=context.get("conversation_id"),
                search_type=SearchType.SEMANTIC,
                max_results=3,  # 闲聊时检索较少
                score_threshold=0.8,  # 提高阈值
                include_context=include_context,
                context_window=context.get("context_window", 3),
                temperature=0.8  # 提高创造性
            )
        except ImportError:
            return {
                "message": query,
                "topic_id": context.get("topic_id"),
                "conversation_id": context.get("conversation_id"),
                "include_context": include_context,
                "max_results": 3,
                "score_threshold": 0.8,
                "context_window": context.get("context_window", 3),
                "temperature": 0.8
            }
    
    def add_greeting_response(self, keyword: str, responses: List[str]) -> None:
        """添加问候语回复"""
        self.greeting_responses[keyword] = responses
        logger.info(f"已添加问候语回复: {keyword}")
        
    def add_emotional_response(self, emotion: str, responses: List[str]) -> None:
        """添加情感回复"""
        self.emotional_responses[emotion] = responses
        logger.info(f"已添加情感回复: {emotion}")
        
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        base_health = await super().health_check()
        
        base_health.update({
            "chat_service_available": self.chat_service is not None,
            "template_responses": {
                "greeting_patterns": len(self.greeting_responses),
                "emotional_patterns": len(self.emotional_responses)
            }
        })
        
        return base_health