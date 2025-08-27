"""
Chat Service

提供聊天功能的核心业务逻辑，集成RAG检索和AI生成。
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List, Optional, Any, Tuple

try:
    import openai
except ImportError:
    openai = None

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_config
from logging_system import get_logger
from modules.services.base_service import BaseService
from modules.services.elasticsearch_service import elasticsearch_chat_service
from modules.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    RetrievedContext,
    AIMetadata,
    MessageRole,
    ConversationSummary,
    ChatSearchResult,
    SearchType
)
from modules.vector_store.weaviate_service import WeaviateVectorStore
from modules.embedding.openai_service import OpenAIEmbeddingService

logger = get_logger(__name__)


class ChatService(BaseService):
    """聊天服务"""
    
    def __init__(self, session: AsyncSession = None, ai_client=None):
        if session:
            super().__init__(session)
        else:
            self.session = None
            self.logger = logger
        
        self.config = get_config()
        self.ai_client = ai_client
        self.es_service = elasticsearch_chat_service
        
        # RAG组件
        self._vector_store: Optional[WeaviateVectorStore] = None
        self._embedding_service: Optional[OpenAIEmbeddingService] = None
        
        # 初始化标志
        self._initialized = False
    
    async def initialize(self):
        """初始化服务组件"""
        if self._initialized:
            return
            
        try:
            # 初始化Elasticsearch
            await self.es_service.initialize()
            
            # 初始化向量存储
            weaviate_url = getattr(self.config, 'weaviate_url', 'http://localhost:8080')
            self._vector_store = WeaviateVectorStore(url=weaviate_url)
            await self._vector_store.initialize()
            
            # 初始化嵌入服务
            if hasattr(self.config, 'ai') and hasattr(self.config.ai, 'embedding'):
                api_key = getattr(self.config.ai.embedding.openai, 'api_key', None)
                if api_key:
                    self._embedding_service = OpenAIEmbeddingService(api_key=api_key)
                    await self._embedding_service.initialize()
                    
            # 初始化OpenAI客户端
            if not self.ai_client and openai and hasattr(self.config, 'ai'):
                # 正确的配置路径：config.ai.chat.openai.api_key
                api_key = getattr(self.config.ai.chat.openai, 'api_key', None)
                if api_key:
                    self.ai_client = openai.AsyncOpenAI(
                        api_key=api_key,
                        organization=getattr(self.config.ai.chat.openai, 'organization', None),
                        base_url=getattr(self.config.ai.chat.openai, 'api_base', None),
                        timeout=getattr(self.config.ai.chat.openai, 'timeout', 60),
                        max_retries=getattr(self.config.ai.chat.openai, 'max_retries', 3)
                    )
                    logger.info("✅ OpenAI客户端初始化成功")
                else:
                    raise Exception("未配置OpenAI API密钥，请检查 AI__CHAT__OPENAI__API_KEY 环境变量")
            
            self._initialized = True
            logger.info("✅ ChatService初始化完成")
            
        except Exception as e:
            logger.error(f"❌ ChatService初始化失败: {e}")
            raise
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """处理聊天请求（同步方式）"""
        await self.initialize()
        
        try:
            # 生成对话ID
            conversation_id = request.conversation_id or str(uuid.uuid4())
            message_id = str(uuid.uuid4())
            
            # 1. RAG检索
            start_time = datetime.now(timezone.utc)
            retrieved_contexts, search_time_ms = await self._retrieve_contexts(
                query=request.message,
                topic_id=request.topic_id,
                search_type=request.search_type,
                max_results=request.max_results,
                score_threshold=request.score_threshold
            )
            
            # 2. 获取对话历史
            conversation_history = []
            if request.context_window > 0:
                conversation_history = await self.get_conversation_messages(
                    conversation_id, 
                    limit=request.context_window * 2
                )
            
            # 3. 构建提示词
            prompt = self._build_prompt(
                user_message=request.message,
                retrieved_contexts=retrieved_contexts if request.include_context else [],
                conversation_history=conversation_history
            )
            
            # 4. 生成AI回答
            generation_start = datetime.now(timezone.utc)
            ai_response, tokens_used = await self._generate_ai_response(
                prompt=prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            generation_time_ms = int((datetime.now(timezone.utc) - generation_start).total_seconds() * 1000)
            
            # 5. 保存对话
            await self.es_service.save_conversation(
                conversation_id=conversation_id,
                user_message=request.message,
                assistant_message=ai_response,
                topic_id=request.topic_id,
                retrieved_contexts=retrieved_contexts,
                ai_metadata={
                    "model": "gpt-3.5-turbo",
                    "tokens_used": tokens_used,
                    "generation_time_ms": generation_time_ms,
                    "search_time_ms": search_time_ms,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens
                }
            )
            
            # 6. 构建响应
            return ChatResponse(
                message_id=message_id,
                conversation_id=conversation_id,
                content=ai_response,
                retrieved_contexts=retrieved_contexts,
                ai_metadata=AIMetadata(
                    model="gpt-3.5-turbo",
                    tokens_used=tokens_used,
                    generation_time_ms=generation_time_ms,
                    search_time_ms=search_time_ms,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                ),
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"❌ 聊天处理失败: {e}")
            raise
    
    async def chat_with_summary(self, request: Dict[str, Any]) -> ChatResponse:
        """基于摘要索引的聊天功能"""
        try:
            query = request.get("query", "")
            topic_id = request.get("topic_id")
            max_results = request.get("max_results", 5)
            score_threshold = request.get("score_threshold", 0.75)
            enhanced_query = request.get("enhanced_query", query)
            
            logger.info(f"🔍 开始摘要聊天 - 查询: '{query[:50]}{'...' if len(query) > 50 else ''}', topic_id: {topic_id}")
            
            # 检索摘要上下文
            summary_contexts, context_count = await self._retrieve_summary_contexts(
                query=query,
                topic_id=topic_id,
                max_results=max_results,
                score_threshold=score_threshold
            )
            
            # 如果摘要上下文不足，回退到普通检索
            if context_count < 2:
                logger.info("🔄 摘要上下文不足，回退到普通检索")
                contexts, context_count = await self._retrieve_contexts(
                    query=query,
                    topic_id=topic_id,
                    max_results=max_results,
                    score_threshold=score_threshold
                )
            else:
                contexts = summary_contexts
            
            # 构建摘要风格的提示
            prompt = self._build_summary_prompt(
                query=enhanced_query or query,
                contexts=contexts,
                style=request.get("response_style", "summary")
            )
            
            # 生成AI响应
            if request.get("stream", False):
                response_content = await self._generate_ai_response_stream(prompt)
            else:
                response_content = await self._generate_ai_response(prompt)
            
            # 构建响应
            response = ChatResponse(
                content=response_content,
                retrieved_context=contexts,
                ai_metadata=AIMetadata(
                    model="gpt-3.5-turbo",
                    search_type="summary",
                    context_count=context_count,
                    processing_time=0.0
                ),
                timestamp=datetime.now(timezone.utc)
            )
            
            logger.info(f"✅ 摘要聊天完成 - 上下文: {context_count}个")
            return response
            
        except Exception as e:
            logger.error(f"❌ 摘要聊天处理失败: {e}")
            raise
    
    async def _retrieve_summary_contexts(
        self,
        query: str,
        topic_id: Optional[str] = None,
        max_results: int = 5,
        score_threshold: float = 0.75
    ) -> tuple[List[RetrievedContext], int]:
        """检索摘要上下文"""
        logger.info(f"🔍 开始摘要检索 - 查询: '{query[:50]}{'...' if len(query) > 50 else ''}', "
                   f"topic_id: {topic_id}, max_results: {max_results}, "
                   f"score_threshold: {score_threshold}")
        
        if not self._vector_store or not self._embedding_service:
            logger.warning("⚠️ 向量存储或嵌入服务未初始化，跳过摘要检索")
            return [], 0
        
        try:
            # 生成查询嵌入
            logger.debug("🧮 生成查询向量嵌入...")
            query_embedding = await self._embedding_service.generate_embedding(query)
            logger.debug(f"✅ 查询向量生成成功，维度: {len(query_embedding)}")
            
            # 准备过滤条件
            filters = None
            if topic_id:
                from modules.vector_store.base import SearchFilter
                filters = SearchFilter(metadata_filters={"topic_id": topic_id})
                logger.info(f"🎯 应用过滤条件: topic_id={topic_id}")
            else:
                logger.info("🌐 无过滤条件，搜索所有摘要文档")
            
            # 摘要向量搜索
            logger.debug(f"🔎 执行摘要向量相似度搜索...")
            search_results = await self._vector_store.search_summaries(
                query_vector=query_embedding,
                top_k=max_results,
                score_threshold=score_threshold,
                filters=filters
            )
            
            # 记录原始搜索结果
            logger.info(f"📊 摘要搜索返回 {len(search_results)} 个原始结果")
            
            # 转换为RetrievedContext
            contexts = []
            empty_content_filtered = 0
            
            for i, result in enumerate(search_results, 1):
                doc = result.document
                doc_metadata = doc.metadata or {}
                
                # 检查是否是摘要文档
                if not doc_metadata.get('summary_document', False):
                    continue
                
                # 过滤空内容摘要
                if not doc.content or len(doc.content.strip()) < 20:
                    empty_content_filtered += 1
                    logger.debug(f"❌ 摘要{i} 被过滤：内容为空或太短")
                    continue
                
                # 创建摘要上下文
                context = RetrievedContext(
                    content=doc.content,
                    source="summary",
                    score=result.score,
                    document_id=doc_metadata.get('document_ids', [None])[0] if doc_metadata.get('document_ids') else doc.id,
                    chunk_index=0,  # 摘要没有chunk概念
                    metadata={
                        "type": "summary",
                        "scope_level": doc_metadata.get('scope_level', 'document'),
                        "key_topics": doc_metadata.get('key_topics', []),
                        "source_documents": doc_metadata.get('document_ids', []),
                        "original_score": result.score,
                        "rank": result.rank
                    }
                )
                contexts.append(context)
                
                logger.debug(f"✅ 摘要{i}: score={result.score:.3f}, "
                           f"scope={doc_metadata.get('scope_level')}, "
                           f"topics={len(doc_metadata.get('key_topics', []))}, "
                           f"content_len={len(doc.content)}")
            
            # 记录过滤统计
            if empty_content_filtered > 0:
                logger.info(f"🚮 过滤空摘要: {empty_content_filtered}个")
            
            final_count = len(contexts)
            logger.info(f"📋 最终摘要上下文: {final_count}个")
            
            return contexts, final_count
            
        except Exception as e:
            logger.error(f"❌ 摘要检索失败: {e}")
            return [], 0
    
    def _build_summary_prompt(
        self,
        query: str,
        contexts: List[RetrievedContext],
        style: str = "summary"
    ) -> str:
        """构建摘要风格的提示"""
        if not contexts:
            return f"""请回答以下问题：{query}
            
注意：当前没有相关的文档摘要可供参考，请基于你的知识进行回答。"""
        
        # 构建上下文部分
        context_text = ""
        for i, context in enumerate(contexts, 1):
            metadata = context.metadata or {}
            scope_level = metadata.get('scope_level', 'document')
            key_topics = metadata.get('key_topics', [])
            
            topics_text = f" (关键主题: {', '.join(key_topics)})" if key_topics else ""
            
            context_text += f"""
=== 摘要 {i} ({scope_level} 级别{topics_text}) ===
{context.content}
相关性得分: {context.score:.3f}
"""
        
        # 根据风格调整提示
        if style == "summary":
            style_instruction = """请基于以上文档摘要，从高层次角度回答用户问题。
重点关注：
1. 主要概念和核心观点
2. 整体趋势和模式
3. 关键要点的综合分析
4. 避免过多具体细节

请用清晰、结构化的方式组织回答。"""
        else:
            style_instruction = "请基于以上摘要信息回答用户问题。"
        
        return f"""你是一个智能助手，需要基于提供的文档摘要回答用户问题。

=== 相关文档摘要 ===
{context_text}

=== 用户问题 ===
{query}

=== 回答指导 ===
{style_instruction}"""
    
    async def _retrieve_contexts(
        self,
        query: str,
        topic_id: Optional[int] = None,
        search_type: SearchType = SearchType.SEMANTIC,
        max_results: int = 5,
        score_threshold: float = 0.0
    ) -> Tuple[List[RetrievedContext], int]:
        """检索相关上下文"""
        
        start_time = datetime.now(timezone.utc)
        
        # 记录检索参数
        logger.info(f"🔍 开始RAG检索 - 查询: '{query[:50]}{'...' if len(query) > 50 else ''}', "
                   f"topic_id: {topic_id}, max_results: {max_results}, "
                   f"score_threshold: {score_threshold}, search_type: {search_type}")
        
        if not self._vector_store or not self._embedding_service:
            logger.warning("⚠️ 向量存储或嵌入服务未初始化，跳过检索")
            return [], 0
        
        try:
            # 生成查询嵌入
            logger.debug("🧮 生成查询向量嵌入...")
            query_embedding = await self._embedding_service.generate_embedding(query)
            logger.debug(f"✅ 查询向量生成成功，维度: {len(query_embedding)}")
            
            # 准备过滤条件
            filters = None
            if topic_id:
                from modules.vector_store.base import SearchFilter
                filters = SearchFilter(metadata_filters={"topic_id": topic_id})
                logger.info(f"🎯 应用过滤条件: topic_id={topic_id}")
            else:
                logger.info("🌐 无过滤条件，搜索所有文档")
            
            # 向量搜索
            logger.debug(f"🔎 执行向量相似度搜索...")
            search_results = await self._vector_store.search_similar(
                query_vector=query_embedding,
                limit=max_results,
                score_threshold=score_threshold,
                filters=filters
            )
            
            # 记录原始搜索结果
            logger.info(f"📊 向量搜索返回 {len(search_results)} 个原始结果")
            
            # 转换为RetrievedContext并记录详细信息
            contexts = []
            empty_content_filtered = 0
            
            for i, result in enumerate(search_results, 1):
                # 从SearchResult.document中获取信息
                doc = result.document
                doc_metadata = doc.metadata or {}
                result_metadata = result.metadata or {}
                
                # 过滤空内容文档
                if not doc.content or len(doc.content.strip()) < 10:
                    empty_content_filtered += 1
                    logger.debug(f"❌ 文档{i} 被过滤：内容为空或太短 (长度={len(doc.content) if doc.content else 0})")
                    continue
                
                # 获取文档信息用于日志
                doc_title = result_metadata.get("document_title", "") or doc_metadata.get("title", "")
                file_id = result_metadata.get("file_id", "") or doc_metadata.get("file_id", "")
                chunk_index = doc_metadata.get("chunk_index", 0)
                content_preview = doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                
                # 记录每个召回文档的详细信息
                logger.info(f"📄 文档{i}: ID={doc.id}, 标题='{doc_title}', "
                           f"文件ID={file_id}, 块索引={chunk_index}, "
                           f"相似度={result.score:.4f}, 内容预览='{content_preview}'")
                
                contexts.append(RetrievedContext(
                    content=doc.content,
                    document_id=doc.id or "",
                    chunk_index=chunk_index,
                    similarity_score=result.score,
                    document_title=doc_title,
                    file_id=file_id,
                    metadata={**doc_metadata, **result_metadata}
                ))
            
            # 记录空内容过滤统计
            if empty_content_filtered > 0:
                logger.info(f"🚫 空内容过滤移除了 {empty_content_filtered} 个文档")
            
            search_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
            # 详细的结果摘要
            if contexts:
                avg_score = sum(ctx.similarity_score for ctx in contexts) / len(contexts)
                best_score = max(ctx.similarity_score for ctx in contexts)
                logger.info(f"✅ RAG检索完成: 召回{len(contexts)}个文档, 耗时{search_time_ms}ms, "
                           f"平均相似度={avg_score:.4f}, 最高相似度={best_score:.4f}")
            else:
                logger.warning(f"⚠️ RAG检索完成但无结果: 耗时{search_time_ms}ms")
                # 分析可能的原因
                if topic_id:
                    logger.warning(f"💡 可能原因: 1) topic_id={topic_id}没有对应文档 "
                                 f"2) 相似度阈值{score_threshold}过高 3) 查询与文档内容差异较大")
                else:
                    logger.warning(f"💡 可能原因: 1) 向量数据库为空 "
                                 f"2) 相似度阈值{score_threshold}过高 3) 查询与所有文档内容差异较大")
            
            return contexts, search_time_ms
            
        except Exception as e:
            logger.error(f"❌ RAG检索失败: {e}")
            return [], 0
    
    def _build_prompt(
        self,
        user_message: str,
        retrieved_contexts: List[RetrievedContext],
        conversation_history: List[ChatMessage] = None
    ) -> str:
        """构建AI提示词"""
        
        prompt_parts = []
        
        # 根据是否有检索结果调整系统提示
        if retrieved_contexts:
            # 有检索结果时的系统提示
            prompt_parts.append("""你是一个专业的AI助手，基于提供的文档内容回答用户问题。请遵循以下原则：

1. 优先使用检索到的文档内容来回答问题
2. 如果文档内容不足以完全回答问题，可以结合你的知识补充
3. 明确指出哪些信息来自文档，哪些是你的补充
4. 保持回答准确、有用、友好""")
            
            # 检索到的上下文
            prompt_parts.append("\n\n=== 相关文档内容 ===")
            for i, context in enumerate(retrieved_contexts, 1):
                doc_title = context.document_title or f"文档{i}"
                prompt_parts.append(f"\n【文档{i}: {doc_title}】")
                prompt_parts.append(f"内容: {context.content}")
                prompt_parts.append(f"相似度: {context.similarity_score:.3f}")
        else:
            # 无检索结果时的系统提示
            prompt_parts.append("""你是一个专业的AI助手。虽然没有找到相关的文档内容，但请基于你的知识为用户提供有价值的回答。请遵循以下原则：

1. 根据问题的类型和领域，提供准确、实用的信息
2. 承认没有特定的文档支持，但仍然尽力帮助用户
3. 如果问题涉及专业领域，建议用户查找更权威的资料
4. 保持回答友好、有建设性，避免简单地说"我不知道"
5. 可以提供相关的概念、方法、建议或学习方向""")
            
            prompt_parts.append(f"\n\n💡 提示：没有找到相关的文档内容，以下回答基于AI的一般知识。")
        
        # 对话历史
        if conversation_history:
            prompt_parts.append("\n\n=== 对话历史 ===")
            for msg in conversation_history[-6:]:  # 最近3轮对话
                role_name = "用户" if msg.role == MessageRole.USER else "助手"
                prompt_parts.append(f"\n{role_name}: {msg.content}")
        
        # 当前用户问题
        prompt_parts.append(f"\n\n=== 当前问题 ===\n用户: {user_message}")
        
        if retrieved_contexts:
            prompt_parts.append("\n\n请基于上述文档内容回答用户问题:")
        else:
            prompt_parts.append("\n\n请基于你的知识为用户提供有价值的回答:")
        
        return "".join(prompt_parts)
    
    async def _generate_ai_response(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Tuple[str, int]:
        """生成AI回答"""
        
        if not self.ai_client:
            raise Exception("OpenAI客户端未初始化，请检查API密钥配置")
        
        try:
            # 使用配置中的模型和参数
            chat_model = getattr(self.config.ai.chat.openai, 'chat_model', 'gpt-3.5-turbo')
            
            response = await self.ai_client.chat.completions.create(
                model=chat_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            return content, tokens_used
            
        except Exception as e:
            logger.error(f"❌ AI生成失败: {e}")
            error_response = f"抱歉，AI服务暂时不可用。错误信息: {str(e)}"
            return error_response, 0
    
    async def _generate_ai_response_stream(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式生成AI回答"""
        
        if not self.ai_client:
            yield {
                "content": "❌ OpenAI客户端未初始化，请检查API密钥配置",
                "tokens": 0
            }
            return
        
        try:
            # 使用配置中的模型和参数
            chat_model = getattr(self.config.ai.chat.openai, 'chat_model', 'gpt-3.5-turbo')
            
            stream = await self.ai_client.chat.completions.create(
                model=chat_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "tokens": 1  # 简化token计算
                    }
                    
        except Exception as e:
            logger.error(f"❌ 流式AI生成失败: {e}")
            yield {
                "content": f"抱歉，AI服务暂时不可用: {str(e)}",
                "tokens": 0
            }
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        before: Optional[str] = None
    ) -> List[ChatMessage]:
        """获取对话消息历史"""
        return await self.es_service.get_conversation_messages(
            conversation_id, limit, before
        )
    
    async def search_chat_content(
        self,
        query: str,
        topic_id: Optional[int] = None,
        limit: int = 20
    ) -> List[ChatSearchResult]:
        """搜索聊天内容"""
        return await self.es_service.search_chat_content(
            query, topic_id, limit
        )
    
    async def get_conversations_list(
        self,
        topic_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[ConversationSummary]:
        """获取对话列表"""
        # 这个方法需要基于ES聚合查询实现
        # 暂时返回空列表，后续完善
        logger.warning("get_conversations_list方法待实现")
        return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        # 这个方法需要在ES中删除对应的文档
        # 暂时返回True，后续完善
        logger.warning("delete_conversation方法待实现")
        return True
    
    async def get_chat_statistics(
        self,
        topic_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取聊天统计"""
        return await self.es_service.get_conversation_statistics(topic_id)
    
    async def close(self):
        """关闭服务"""
        await self.es_service.close()
        if self._vector_store:
            await self._vector_store.cleanup()
        if self._embedding_service:
            await self._embedding_service.cleanup()


# 便捷函数
def get_chat_service() -> ChatService:
    """获取ChatService实例"""
    return ChatService()
