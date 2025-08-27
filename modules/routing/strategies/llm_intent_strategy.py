"""
LLM Intent Recognition Strategy

基于大语言模型的意图识别路由策略。
"""

import json
import logging
from typing import Dict, List, Any, Optional

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

from .base import IRoutingStrategy
from ..engine import RouteDecision

logger = logging.getLogger(__name__)


class LLMIntentStrategy(IRoutingStrategy):
    """基于LLM的意图识别路由策略"""
    
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.1,
        max_tokens: int = 200
    ):
        self.llm_client = llm_client
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 意图到处理器的映射
        self.intent_handler_mapping = {
            "RAG_QUERY": "rag_handler",
            "CASUAL_CHAT": "chat_handler",
            "SYSTEM_COMMAND": "system_handler", 
            "TOOL_REQUEST": "tool_handler",
            "GREETING": "chat_handler",
            "UNCLEAR": "chat_handler"
        }
        
        # 意图描述，用于生成更好的提示词
        self.intent_descriptions = {
            "RAG_QUERY": "用户想要查询具体知识、信息或需要解释某个概念",
            "CASUAL_CHAT": "用户进行日常闲聊、情感表达或一般性对话",
            "SYSTEM_COMMAND": "用户想要执行系统操作，如清除历史、设置配置等",
            "TOOL_REQUEST": "用户需要使用工具，如计算、翻译、查天气等",
            "GREETING": "用户的问候语或告别语",
            "UNCLEAR": "无法明确判断用户意图"
        }
        
        if not OPENAI_AVAILABLE and not llm_client:
            logger.warning("OpenAI库未安装且未提供LLM客户端，LLM意图识别将无法工作")
        
    async def initialize(self) -> None:
        """初始化策略"""
        if not self.llm_client and OPENAI_AVAILABLE:
            logger.warning("LLM客户端未设置，请确保在使用前设置LLM客户端")
        
        logger.info("LLMIntentStrategy 初始化完成")
        
    def set_llm_client(self, client: Any) -> None:
        """设置LLM客户端"""
        self.llm_client = client
        logger.info("LLM客户端已设置")
        
    async def decide_route(self, query: str, context: Dict[str, Any]) -> RouteDecision:
        """使用LLM进行意图识别和路由决策"""
        if not self.llm_client:
            return self._create_fallback_decision(
                "LLM客户端未设置",
                {"error": "llm_client_not_set"}
            )
        
        try:
            # 构建提示词
            prompt = self._build_intent_classification_prompt(query, context)
            
            # 调用LLM
            response = await self._call_llm(prompt)
            
            # 解析结果
            intent_result = self._parse_llm_response(response)
            
            if not intent_result:
                return self._create_fallback_decision(
                    "LLM响应解析失败",
                    {"error": "response_parsing_failed", "raw_response": response[:200]}
                )
            
            # 映射到处理器
            handler_name = self.intent_handler_mapping.get(
                intent_result["intent"], 
                "chat_handler"
            )
            
            return RouteDecision(
                handler_name=handler_name,
                confidence=intent_result.get("confidence", 0.5),
                metadata={
                    "strategy": "llm_intent",
                    "intent": intent_result["intent"],
                    "reasoning": intent_result.get("reasoning", ""),
                    "model": self.model,
                    "raw_response": response[:500]  # 限制长度
                }
            )
            
        except Exception as e:
            logger.error(f"LLM意图识别失败: {e}")
            return self._create_fallback_decision(
                str(e),
                {"error": "llm_call_failed", "exception": str(e)}
            )
    
    def _build_intent_classification_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """构建意图分类提示词"""
        
        # 获取对话历史
        conversation_history = context.get("conversation_history", [])
        history_text = ""
        if conversation_history:
            recent_history = conversation_history[-3:]  # 最近3轮对话
            history_items = []
            for msg in recent_history:
                role = "用户" if msg.get("role") == "user" else "助手"
                content = msg.get("content", "")[:100]  # 限制长度
                history_items.append(f"{role}: {content}")
            history_text = f"\n对话历史:\n" + "\n".join(history_items) + "\n"
        
        # 构建意图选项说明
        intent_options = []
        for intent, description in self.intent_descriptions.items():
            intent_options.append(f"- {intent}: {description}")
        
        prompt = f"""你是一个智能对话系统的意图分类器。请分析用户的输入并确定用户的意图类型。

可选的意图类型:
{chr(10).join(intent_options)}

请严格按照以下JSON格式返回结果:
{{
    "intent": "选择上述意图类型之一",
    "confidence": 0.95,
    "reasoning": "简短的分析理由"
}}

注意事项:
1. confidence值在0-1之间，越确定值越高
2. 如果不确定，选择UNCLEAR
3. 只返回JSON，不要其他文字
{history_text}
当前用户输入: {query}

请分析并返回JSON结果:"""

        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        try:
            # 检查是否是OpenAI客户端
            if hasattr(self.llm_client, 'chat') and hasattr(self.llm_client.chat, 'completions'):
                # OpenAI API调用
                response = await self.llm_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content
            
            elif hasattr(self.llm_client, 'generate'):
                # 其他LLM客户端
                response = await self.llm_client.generate(
                    prompt=prompt,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response
                
            else:
                # 尝试通用调用方式
                response = await self.llm_client(prompt)
                return response
                
        except Exception as e:
            logger.error(f"LLM API调用失败: {e}")
            raise
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析LLM响应"""
        try:
            # 清理响应文本
            response_clean = response.strip()
            
            # 尝试找到JSON部分
            start_idx = response_clean.find('{')
            end_idx = response_clean.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning(f"响应中未找到JSON格式: {response_clean[:100]}")
                return None
                
            json_str = response_clean[start_idx:end_idx]
            
            # 解析JSON
            result = json.loads(json_str)
            
            # 验证必需字段
            if "intent" not in result:
                logger.warning(f"响应缺少intent字段: {result}")
                return None
            
            # 验证意图类型
            intent = result["intent"]
            if intent not in self.intent_descriptions:
                logger.warning(f"未知的意图类型: {intent}")
                result["intent"] = "UNCLEAR"
            
            # 确保confidence字段存在且有效
            confidence = result.get("confidence", 0.5)
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                result["confidence"] = 0.5
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 响应: {response[:200]}")
            return None
        except Exception as e:
            logger.error(f"响应解析失败: {e}")
            return None
    
    def _create_fallback_decision(self, reason: str, metadata: Dict[str, Any]) -> RouteDecision:
        """创建回退决策"""
        return RouteDecision(
            handler_name="chat_handler",
            confidence=0.1,
            metadata={
                "strategy": "llm_intent",
                "fallback": True,
                "reason": reason,
                **metadata
            }
        )
        
    @property
    def strategy_name(self) -> str:
        return "llm_intent"
    
    def add_intent_mapping(self, intent: str, handler_name: str, description: str = "") -> None:
        """添加新的意图映射"""
        self.intent_handler_mapping[intent] = handler_name
        if description:
            self.intent_descriptions[intent] = description
        logger.info(f"已添加意图映射: {intent} -> {handler_name}")
    
    def remove_intent_mapping(self, intent: str) -> bool:
        """移除意图映射"""
        if intent in self.intent_handler_mapping:
            del self.intent_handler_mapping[intent]
            if intent in self.intent_descriptions:
                del self.intent_descriptions[intent]
            logger.info(f"已移除意图映射: {intent}")
            return True
        return False
    
    def get_intent_mappings(self) -> Dict[str, str]:
        """获取所有意图映射"""
        return self.intent_handler_mapping.copy()
    
    def update_model_config(self, model: str = None, temperature: float = None, max_tokens: int = None) -> None:
        """更新模型配置"""
        if model is not None:
            self.model = model
        if temperature is not None:
            self.temperature = max(0.0, min(2.0, temperature))
        if max_tokens is not None:
            self.max_tokens = max(1, min(4000, max_tokens))
            
        logger.info(f"模型配置已更新: model={self.model}, temperature={self.temperature}, max_tokens={self.max_tokens}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            "strategy": self.strategy_name,
            "llm_client_available": self.llm_client is not None,
            "openai_available": OPENAI_AVAILABLE,
            "model": self.model,
            "intent_mappings_count": len(self.intent_handler_mapping)
        }
        
        if self.llm_client:
            try:
                # 简单测试调用
                test_response = await self._call_llm("测试连接")
                status["llm_test"] = "success" if test_response else "failed"
            except Exception as e:
                status["llm_test"] = f"failed: {str(e)}"
        else:
            status["llm_test"] = "client_not_set"
            
        return status
    
    async def cleanup(self) -> None:
        """清理资源"""
        # LLM客户端通常不需要显式清理
        logger.info("LLMIntentStrategy 已清理")