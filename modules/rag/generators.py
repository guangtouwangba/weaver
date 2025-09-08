"""
响应生成器组件实现

负责基于检索到的文档生成最终的回答。
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from modules.rag.base import (
    IResponseGenerator,
    RetrievedDocument,
    RAGContext,
    RAGPipelineError,
)

logger = logging.getLogger(__name__)


class OpenAIResponseGenerator(IResponseGenerator):
    """基于OpenAI的响应生成器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 配置参数
        self.model = config.get("model", "gpt-3.5-turbo")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.3)
        self.max_context_tokens = config.get("max_context_tokens", 4000)
        
        # 提示词模板
        self.system_prompt = config.get("system_prompt", self._get_default_system_prompt())
        self.user_prompt_template = config.get("user_prompt_template", self._get_default_user_prompt_template())
        
        self.ai_client = None
        
        logger.info(f"OpenAIResponseGenerator 初始化: model={self.model}")
    
    async def initialize(self) -> None:
        """初始化响应生成器"""
        if self._initialized:
            return
        
        try:
            # 初始化OpenAI客户端
            from openai import AsyncOpenAI
            import os
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RAGPipelineError("OPENAI_API_KEY 环境变量未设置")
            
            self.ai_client = AsyncOpenAI(api_key=api_key)
            
            # 测试连接
            await self._test_connection()
            
            self._initialized = True
            logger.info("OpenAIResponseGenerator 初始化完成")
            
        except Exception as e:
            logger.error(f"OpenAIResponseGenerator 初始化失败: {e}")
            raise RAGPipelineError(
                f"响应生成器初始化失败: {e}",
                component_type=self.component_type
            )
    
    async def process(self, context: RAGContext) -> RAGContext:
        """处理RAG上下文 - 生成响应"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 生成响应
            answer = await self.generate(
                query=context.query,
                documents=context.retrieved_documents,
                conversation_history=context.conversation_history
            )
            
            # 计算置信度（简化版本）
            confidence = self._calculate_confidence(context.retrieved_documents, answer)
            
            # 更新上下文
            context.processing_metadata["generated_answer"] = answer
            context.processing_metadata["confidence"] = confidence
            context.processing_metadata["generation_model"] = self.model
            
            logger.info(f"响应生成完成: 长度={len(answer)}, 置信度={confidence:.3f}")
            
            return context
            
        except Exception as e:
            logger.error(f"响应生成失败: {e}")
            raise RAGPipelineError(
                f"响应生成失败: {e}",
                component_type=self.component_type
            )
    
    async def generate(
        self, 
        query: str, 
        documents: List[RetrievedDocument],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """生成响应"""
        try:
            start_time = time.time()
            
            # 准备上下文文档
            context_text = self._prepare_context(documents)
            
            # 构建对话历史
            history_text = self._prepare_conversation_history(conversation_history or [])
            
            # 构建用户提示词
            user_prompt = self.user_prompt_template.format(
                query=query,
                context=context_text,
                history=history_text
            )
            
            # 构建消息
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # 调用OpenAI API
            response = await self.ai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False
            )
            
            answer = response.choices[0].message.content.strip()
            
            generation_time = (time.time() - start_time) * 1000
            logger.debug(f"响应生成耗时: {generation_time:.1f}ms")
            
            return answer
            
        except Exception as e:
            logger.error(f"响应生成执行失败: {e}")
            raise RAGPipelineError(f"响应生成执行失败: {e}")
    
    def _prepare_context(self, documents: List[RetrievedDocument]) -> str:
        """准备上下文文档"""
        if not documents:
            return "没有找到相关文档。"
        
        context_parts = []
        current_tokens = 0
        
        for i, doc in enumerate(documents):
            # 估算token数量（粗略估计：1个token约4个字符）
            doc_tokens = len(doc.content) // 4
            
            if current_tokens + doc_tokens > self.max_context_tokens:
                break
            
            # 格式化文档
            doc_text = f"文档 {i+1} (相关度: {doc.score:.3f}):\n{doc.content}\n"
            context_parts.append(doc_text)
            current_tokens += doc_tokens
        
        return "\n".join(context_parts)
    
    def _prepare_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """准备对话历史"""
        if not history:
            return ""
        
        history_parts = []
        for msg in history[-5:]:  # 只保留最近5轮对话
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                history_parts.append(f"用户: {content}")
            elif role == "assistant":
                history_parts.append(f"助手: {content}")
        
        return "\n".join(history_parts) if history_parts else ""
    
    def _calculate_confidence(self, documents: List[RetrievedDocument], answer: str) -> float:
        """计算响应置信度"""
        if not documents:
            return 0.1
        
        # 基于检索文档的平均分数
        avg_score = sum(doc.score for doc in documents) / len(documents)
        
        # 基于文档数量
        doc_count_factor = min(len(documents) / 5, 1.0)  # 5个文档为满分
        
        # 基于答案长度（太短或太长都降低置信度）
        answer_length = len(answer)
        if 50 <= answer_length <= 500:
            length_factor = 1.0
        elif answer_length < 50:
            length_factor = 0.7
        else:
            length_factor = 0.9
        
        # 综合计算
        confidence = avg_score * 0.6 + doc_count_factor * 0.3 + length_factor * 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        return """你是一个专业的AI助手，擅长基于提供的文档内容回答用户问题。

请遵循以下原则：
1. 基于提供的文档内容回答问题，不要编造信息
2. 如果文档中没有相关信息，请明确说明
3. 回答要准确、简洁、有条理
4. 可以引用文档中的具体内容来支持你的回答
5. 如果有多个相关文档，请综合考虑所有信息
6. 保持客观中立的语调"""
    
    def _get_default_user_prompt_template(self) -> str:
        """获取默认用户提示词模板"""
        return """基于以下文档内容回答用户问题：

{context}

{history}

用户问题: {query}

请基于上述文档内容回答问题。如果文档中没有足够信息回答问题，请说明这一点。"""
    
    async def _test_connection(self) -> None:
        """测试API连接"""
        try:
            response = await self.ai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个测试助手。"},
                    {"role": "user", "content": "请回复'连接测试成功'"}
                ],
                max_tokens=10,
                temperature=0
            )
            
            if not response.choices:
                raise RAGPipelineError("API测试失败: 返回数据为空")
            
            logger.debug("OpenAI API连接测试成功")
            
        except Exception as e:
            logger.error(f"OpenAI API连接测试失败: {e}")
            raise RAGPipelineError(f"API连接测试失败: {e}")


class StreamingResponseGenerator(OpenAIResponseGenerator):
    """流式响应生成器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.enable_streaming = config.get("enable_streaming", True)
        
        logger.info("StreamingResponseGenerator 初始化")
    
    async def generate_stream(
        self, 
        query: str, 
        documents: List[RetrievedDocument],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ):
        """生成流式响应"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 准备上下文文档
            context_text = self._prepare_context(documents)
            
            # 构建对话历史
            history_text = self._prepare_conversation_history(conversation_history or [])
            
            # 构建用户提示词
            user_prompt = self.user_prompt_template.format(
                query=query,
                context=context_text,
                history=history_text
            )
            
            # 构建消息
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # 调用流式API
            stream = await self.ai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True
            )
            
            # 返回异步生成器
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
        except Exception as e:
            logger.error(f"流式响应生成失败: {e}")
            raise RAGPipelineError(f"流式响应生成失败: {e}")


class TemplateResponseGenerator(IResponseGenerator):
    """基于模板的响应生成器（用于测试或简单场景）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 配置参数
        self.max_documents = config.get("max_documents", 5)
        self.response_template = config.get("response_template", self._get_default_template())
        
        logger.info("TemplateResponseGenerator 初始化")
    
    async def initialize(self) -> None:
        """初始化模板响应生成器"""
        if self._initialized:
            return
        
        self._initialized = True
        logger.info("TemplateResponseGenerator 初始化完成")
    
    async def process(self, context: RAGContext) -> RAGContext:
        """处理RAG上下文 - 生成模板响应"""
        try:
            # 生成响应
            answer = await self.generate(
                query=context.query,
                documents=context.retrieved_documents,
                conversation_history=context.conversation_history
            )
            
            # 更新上下文
            context.processing_metadata["generated_answer"] = answer
            context.processing_metadata["confidence"] = 0.8  # 固定置信度
            context.processing_metadata["generation_method"] = "template"
            
            logger.info(f"模板响应生成完成: 长度={len(answer)}")
            
            return context
            
        except Exception as e:
            logger.error(f"模板响应生成失败: {e}")
            raise RAGPipelineError(
                f"模板响应生成失败: {e}",
                component_type=self.component_type
            )
    
    async def generate(
        self, 
        query: str, 
        documents: List[RetrievedDocument],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """生成模板响应"""
        try:
            if not documents:
                return "抱歉，我没有找到相关的文档来回答您的问题。"
            
            # 选择最相关的文档
            top_documents = documents[:self.max_documents]
            
            # 构建文档摘要
            doc_summaries = []
            for i, doc in enumerate(top_documents):
                summary = doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
                doc_summaries.append(f"{i+1}. {summary} (相关度: {doc.score:.3f})")
            
            # 使用模板生成响应
            response = self.response_template.format(
                query=query,
                document_count=len(top_documents),
                documents="\n".join(doc_summaries)
            )
            
            return response
            
        except Exception as e:
            logger.error(f"模板响应生成执行失败: {e}")
            raise RAGPipelineError(f"模板响应生成执行失败: {e}")
    
    def _get_default_template(self) -> str:
        """获取默认响应模板"""
        return """基于您的问题"{query}"，我找到了{document_count}个相关文档：

{documents}

根据这些文档，我可以为您提供以下信息：
[这里是基于文档内容的回答]

如果您需要更详细的信息，请告诉我您想了解哪个方面。"""
