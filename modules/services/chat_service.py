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
        """初始化服务组件（线程安全）"""
        if self._initialized:
            return
            
        # 使用锁确保初始化只执行一次
        if not hasattr(self, '_init_lock'):
            self._init_lock = asyncio.Lock()
            
        async with self._init_lock:
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
                    # 使用新的配置管理
                    chat_config = ChatConfiguration.from_config(self.config)
                    chat_config.validate()
                    
                    self.ai_client = openai.AsyncOpenAI(
                        api_key=chat_config.api_key,
                        organization=chat_config.organization,
                        base_url=chat_config.base_url,
                        timeout=chat_config.timeout,
                        max_retries=chat_config.max_retries
                    )
                    logger.info("✅ OpenAI客户端初始化成功")
                
                self._initialized = True
                logger.info("✅ ChatService初始化完成")
                
            except ValueError as e:
                logger.error(f"❌ 配置错误: {e}")
                raise Exception(f"ChatService配置错误: {str(e)}") from e
            except Exception as e:
                logger.error(f"❌ ChatService初始化失败: {e}")
                # 清理已初始化的资源
                await self._cleanup_partial_initialization()
                raise
    
    async def _cleanup_partial_initialization(self):
        """清理部分初始化的资源"""
        try:
            if hasattr(self, '_vector_store') and self._vector_store:
                await self._vector_store.cleanup()
            if hasattr(self, '_embedding_service') and self._embedding_service:
                await self._embedding_service.cleanup()
        except Exception as e:
            logger.error(f"⚠️ 清理资源时出错: {e}")
    
    def _get_services(self):
        """获取服务实例"""
        # 创建配置
        chat_config = ChatConfiguration.from_config(self.config)
        
        # 创建检索服务
        retrieval_service = WeaviateContextRetrievalService(
            self._vector_store, 
            self._embedding_service
        )
        
        # 创建提示构建器
        prompt_builder = PromptBuilder()
        
        # 创建AI生成服务
        ai_service = AIGenerationService(self.ai_client, chat_config)
        
        # 创建对话管理器
        conversation_manager = ConversationManager(self.es_service)
        
        return retrieval_service, prompt_builder, ai_service, conversation_manager
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """处理聊天请求 - 重构后的职责分离版本"""
        await self.initialize()
        
        try:
            # 获取服务实例
            retrieval_service, prompt_builder, ai_service, conversation_manager = self._get_services()
            
            # 1. 生成对话ID
            conversation_id = request.conversation_id or str(uuid.uuid4())
            message_id = str(uuid.uuid4())
            
            # 2. 检索上下文
            retrieved_contexts, search_time_ms = await retrieval_service.retrieve_contexts(
                query=request.message,
                topic_id=request.topic_id,
                search_type=request.search_type,
                max_results=request.max_results,
                score_threshold=request.score_threshold
            )
            
            # 3. 获取对话历史
            conversation_history = []
            if request.context_window > 0:
                conversation_history = await conversation_manager.get_conversation_history(
                    conversation_id, limit=request.context_window * 2
                )
            
            # 4. 构建提示词
            prompt = prompt_builder.build_chat_prompt(
                user_message=request.message,
                retrieved_contexts=retrieved_contexts if request.include_context else [],
                conversation_history=conversation_history
            )
            
            # 5. 生成AI回答
            generation_start = datetime.now(timezone.utc)
            ai_response, tokens_used = await ai_service.generate_response(
                prompt=prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            generation_time_ms = int((datetime.now(timezone.utc) - generation_start).total_seconds() * 1000)
            
            # 6. 保存对话
            ai_metadata = {
                "model": ai_service.config.chat_model,
                "tokens_used": tokens_used,
                "generation_time_ms": generation_time_ms,
                "search_time_ms": search_time_ms,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens
            }
            
            await conversation_manager.save_conversation(
                conversation_id=conversation_id,
                user_message=request.message,
                assistant_message=ai_response,
                topic_id=request.topic_id,
                retrieved_contexts=retrieved_contexts,
                ai_metadata=ai_metadata
            )
            
            # 7. 构建响应
            return ChatResponse(
                message_id=message_id,
                conversation_id=conversation_id,
                content=ai_response,
                retrieved_contexts=retrieved_contexts,
                ai_metadata=AIMetadata(
                    model=ai_service.config.chat_model,
                    tokens_used=tokens_used,
                    generation_time_ms=generation_time_ms,
                    search_time_ms=search_time_ms,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                ),
                timestamp=datetime.now(timezone.utc)
            )
            
        except ValueError as e:
            logger.error(f"❌ 配置错误: {e}")
            raise Exception(f"聊天服务配置错误: {str(e)}") from e
        except Exception as e:
            logger.error(f"❌ 聊天处理失败: {e}")
            raise Exception(f"聊天处理失败: {str(e)}") from e
    
    async def chat_with_summary(self, request: Dict[str, Any]) -> ChatResponse:
        """基于摘要索引的聊天功能 - 重构版本"""
        await self.initialize()
        
        try:
            # 获取服务实例
            retrieval_service, prompt_builder, ai_service, conversation_manager = self._get_services()
            
            query = request.get("query", "")
            topic_id = request.get("topic_id")
            max_results = request.get("max_results", 5)
            score_threshold = request.get("score_threshold", 0.75)
            enhanced_query = request.get("enhanced_query", query)
            
            logger.info(f"🔍 开始摘要聊天 - 查询: '{query[:50]}{'...' if len(query) > 50 else ''}', topic_id: {topic_id}")
            
            # 检索摘要上下文
            summary_contexts, context_count = await retrieval_service.retrieve_summary_contexts(
                query=query,
                topic_id=topic_id,
                max_results=max_results,
                score_threshold=score_threshold
            )
            
            # 如果摘要上下文不足，回退到普通检索
            if context_count < 2:
                logger.info("🔄 摘要上下文不足，回退到普通检索")
                contexts, context_count = await retrieval_service.retrieve_contexts(
                    query=query,
                    topic_id=topic_id,
                    max_results=max_results,
                    score_threshold=score_threshold
                )
            else:
                contexts = summary_contexts
            
            # 构建摘要风格的提示
            prompt = prompt_builder.build_summary_prompt(
                query=enhanced_query or query,
                contexts=contexts,
                style=request.get("response_style", "summary")
            )
            
            # 生成AI响应
            if request.get("stream", False):
                response_content = await ai_service.generate_response_stream(prompt)
                tokens_used = 0  # 流式模式无法准确计算
            else:
                response_content, tokens_used = await ai_service.generate_response(prompt)
            
            # 构建响应
            response = ChatResponse(
                content=response_content,
                retrieved_context=contexts,
                ai_metadata=AIMetadata(
                    model=ai_service.config.chat_model,
                    search_type="summary",
                    context_count=context_count,
                    processing_time=0.0,
                    tokens_used=tokens_used
                ),
                timestamp=datetime.now(timezone.utc)
            )
            
            logger.info(f"✅ 摘要聊天完成 - 上下文: {context_count}个")
            return response
            
        except Exception as e:
            logger.error(f"❌ 摘要聊天处理失败: {e}")
            raise
    

    

    
    async def retrieve_contexts(
        self,
        query: str,
        topic_id: Optional[int] = None,
        search_type: SearchType = SearchType.SEMANTIC,
        max_results: int = 5,
        score_threshold: float = 0.0,
        collection_name: str = "documents"
    ) -> List[Dict[str, Any]]:
        """
        公共检索上下文方法，供Handler使用 - 重构版本
        
        Returns:
            List[Dict[str, Any]]: 检索到的上下文列表（简化格式）
        """
        await self.initialize()
        
        # 获取检索服务
        retrieval_service = WeaviateContextRetrievalService(
            self._vector_store, 
            self._embedding_service
        )
        
        contexts, search_time = await retrieval_service.retrieve_contexts(
            query=query,
            topic_id=topic_id,
            search_type=search_type,
            max_results=max_results,
            score_threshold=score_threshold,
            collection_name=collection_name
        )
        
        # 转换为简化的字典格式供Handler使用
        result = []
        for ctx in contexts:
            result.append({
                "content": ctx.content,
                "document_id": getattr(ctx, 'document_id', ''),
                "chunk_index": getattr(ctx, 'chunk_index', 0),
                "similarity_score": getattr(ctx, 'similarity_score', getattr(ctx, 'score', 0)),
                "document_title": getattr(ctx, 'document_title', ''),
                "file_id": getattr(ctx, 'file_id', ''),
                "metadata": getattr(ctx, 'metadata', {})
            })
        
        return result


    

    

    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        before: Optional[str] = None
    ) -> List[ChatMessage]:
        """获取对话消息历史 - 重构版本"""
        await self.initialize()
        conversation_manager = ConversationManager(self.es_service)
        return await conversation_manager.get_conversation_history(conversation_id, limit)
    
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
    


from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class ChatConfiguration:
    """聊天服务配置管理"""
    chat_model: str
    api_key: str
    organization: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3
    
    @classmethod
    def from_config(cls, config) -> 'ChatConfiguration':
        """从全局配置创建聊天配置"""
        try:
            ai_config = config.ai.chat.openai
            api_key = getattr(ai_config, 'api_key', None)
            if not api_key:
                raise ValueError("未配置OpenAI API密钥，请检查 AI__CHAT__OPENAI__API_KEY 环境变量")
            
            return cls(
                chat_model=getattr(ai_config, 'chat_model', 'gpt-3.5-turbo'),
                api_key=api_key,
                organization=getattr(ai_config, 'organization', None),
                base_url=getattr(ai_config, 'api_base', None),
                timeout=getattr(ai_config, 'timeout', 60),
                max_retries=getattr(ai_config, 'max_retries', 3)
            )
        except AttributeError as e:
            raise ValueError(f"配置结构错误: {e}，请检查AI配置") from e
    
    def validate(self) -> None:
        """验证配置有效性"""
        if not self.api_key:
            raise ValueError("API密钥不能为空")
        if not self.chat_model:
            raise ValueError("聊天模型不能为空")
        if self.timeout <= 0:
            raise ValueError("超时时间必须大于0")
        if self.max_retries < 0:
            raise ValueError("重试次数不能小于0")


class ContextRetrievalService(ABC):
    """上下文检索服务抽象基类"""
    
    @abstractmethod
    async def retrieve_contexts(
        self,
        query: str,
        topic_id: Optional[int] = None,
        search_type: SearchType = SearchType.SEMANTIC,
        max_results: int = 5,
        score_threshold: float = 0.0,
        collection_name: str = "documents"
    ) -> Tuple[List[RetrievedContext], int]:
        """检索文档上下文"""
        pass
    
    @abstractmethod
    async def retrieve_summary_contexts(
        self,
        query: str,
        topic_id: Optional[int] = None,
        max_results: int = 5,
        score_threshold: float = 0.75
    ) -> Tuple[List[RetrievedContext], int]:
        """检索摘要上下文"""
        pass


class WeaviateContextRetrievalService(ContextRetrievalService):
    """基于Weaviate的上下文检索服务实现"""
    
    def __init__(self, vector_store: WeaviateVectorStore, embedding_service: OpenAIEmbeddingService):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    async def retrieve_contexts(
        self,
        query: str,
        topic_id: Optional[int] = None,
        search_type: SearchType = SearchType.SEMANTIC,
        max_results: int = 5,
        score_threshold: float = 0.0,
        collection_name: str = "documents"
    ) -> Tuple[List[RetrievedContext], int]:
        """检索文档上下文"""
        return await self._retrieve_contexts_generic(
            query=query,
            topic_id=topic_id,
            max_results=max_results,
            score_threshold=score_threshold,
            collection_name=collection_name,
            search_type="documents"
        )
    
    async def retrieve_summary_contexts(
        self,
        query: str,
        topic_id: Optional[int] = None,
        max_results: int = 5,
        score_threshold: float = 0.75
    ) -> Tuple[List[RetrievedContext], int]:
        """检索摘要上下文"""
        return await self._retrieve_contexts_generic(
            query=query,
            topic_id=topic_id,
            max_results=max_results,
            score_threshold=score_threshold,
            collection_name="documents",  # 统一使用documents集合
            search_type="summaries"
        )
    
    async def _retrieve_contexts_generic(
        self,
        query: str,
        topic_id: Optional[int] = None,
        max_results: int = 5,
        score_threshold: float = 0.0,
        collection_name: str = "documents",
        search_type: str = "documents"
    ) -> Tuple[List[RetrievedContext], int]:
        """通用检索方法，统一处理文档和摘要检索"""
        
        start_time = datetime.now(timezone.utc)
        
        # 记录检索参数
        self.logger.info(f"🔍 开始{search_type}检索 - 查询: '{query[:50]}{'...' if len(query) > 50 else ''}', "
                        f"topic_id: {topic_id}, max_results: {max_results}, "
                        f"score_threshold: {score_threshold}")
        
        if not self.vector_store or not self.embedding_service:
            self.logger.warning("⚠️ 向量存储或嵌入服务未初始化，跳过检索")
            return [], 0
        
        try:
            # 生成查询嵌入
            self.logger.debug("🧮 生成查询向量嵌入...")
            query_embedding = await self.embedding_service.generate_embedding(query)
            self.logger.debug(f"✅ 查询向量生成成功，维度: {len(query_embedding)}")
            
            # 准备过滤条件
            filters = None
            if topic_id:
                from modules.vector_store.base import SearchFilter
                filters = SearchFilter(metadata_filters={"topic_id": topic_id})
                self.logger.info(f"🎯 应用过滤条件: topic_id={topic_id}")
            else:
                self.logger.info("🌐 无过滤条件，搜索所有文档")
            
            # 根据搜索类型选择不同的搜索方法
            if search_type == "summaries":
                self.logger.debug(f"🔎 执行摘要向量相似度搜索...")
                search_results = await self.vector_store.search_summaries(
                    query_vector=query_embedding,
                    top_k=max_results,
                    score_threshold=score_threshold,
                    filters=filters
                )
            else:
                self.logger.debug(f"🔎 执行文档向量相似度搜索，集合: {collection_name}")
                search_results = await self.vector_store.search_similar(
                    query_vector=query_embedding,
                    limit=max_results,
                    score_threshold=score_threshold,
                    filters=filters,
                    collection_name=collection_name
                )
            
            # 记录原始搜索结果
            self.logger.info(f"📊 向量搜索返回 {len(search_results)} 个原始结果")
            
            # 转换为RetrievedContext并记录详细信息
            contexts = []
            empty_content_filtered = 0
            
            for i, result in enumerate(search_results, 1):
                doc = result.document
                doc_metadata = doc.metadata or {}
                result_metadata = result.metadata or {}
                
                # 对于摘要搜索，检查是否是摘要文档
                if search_type == "summaries" and not doc_metadata.get('summary_document', False):
                    continue
                
                # 过滤空内容文档
                min_content_length = 20 if search_type == "summaries" else 10
                if not doc.content or len(doc.content.strip()) < min_content_length:
                    empty_content_filtered += 1
                    self.logger.debug(f"❌ 文档{i} 被过滤：内容为空或太短 (长度={len(doc.content) if doc.content else 0})")
                    continue
                
                # 获取文档信息用于日志
                doc_title = result_metadata.get("document_title", "") or doc_metadata.get("title", "")
                file_id = result_metadata.get("file_id", "") or doc_metadata.get("file_id", "")
                chunk_index = doc_metadata.get("chunk_index", 0)
                content_preview = doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                
                # 记录每个召回文档的详细信息
                self.logger.info(f"📄 文档{i}: ID={doc.id}, 标题='{doc_title}', "
                               f"文件ID={file_id}, 块索引={chunk_index}, "
                               f"相似度={result.score:.4f}, 内容预览='{content_preview}'")
                
                # 为摘要上下文创建特殊的context
                if search_type == "summaries":
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
                            "rank": result.rank if hasattr(result, 'rank') else i
                        }
                    )
                else:
                    context = RetrievedContext(
                        content=doc.content,
                        document_id=doc.id or "",
                        chunk_index=chunk_index,
                        similarity_score=result.score,
                        document_title=doc_title,
                        file_id=file_id,
                        metadata={**doc_metadata, **result_metadata}
                    )
                
                contexts.append(context)
            
            # 记录空内容过滤统计
            if empty_content_filtered > 0:
                self.logger.info(f"🚫 空内容过滤移除了 {empty_content_filtered} 个文档")
            
            search_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
            # 详细的结果摘要
            if contexts:
                avg_score = sum(getattr(ctx, 'similarity_score', getattr(ctx, 'score', 0)) for ctx in contexts) / len(contexts)
                best_score = max(getattr(ctx, 'similarity_score', getattr(ctx, 'score', 0)) for ctx in contexts)
                self.logger.info(f"✅ {search_type}检索完成: 召回{len(contexts)}个文档, 耗时{search_time_ms}ms, "
                               f"平均相似度={avg_score:.4f}, 最高相似度={best_score:.4f}")
            else:
                self.logger.warning(f"⚠️ {search_type}检索完成但无结果: 耗时{search_time_ms}ms")
                # 分析可能的原因
                if topic_id:
                    self.logger.warning(f"💡 可能原因: 1) topic_id={topic_id}没有对应文档 "
                                      f"2) 相似度阈值{score_threshold}过高 3) 查询与文档内容差异较大")
                else:
                    self.logger.warning(f"💡 可能原因: 1) 向量数据库为空 "
                                      f"2) 相似度阈值{score_threshold}过高 3) 查询与所有文档内容差异较大")
            
            return contexts, search_time_ms
            
        except Exception as e:
            self.logger.error(f"❌ {search_type}检索失败: {e}")
            return [], 0


class PromptBuilder:
    """提示词构建服务"""
    
    def build_chat_prompt(
        self,
        user_message: str,
        retrieved_contexts: List[RetrievedContext],
        conversation_history: List[ChatMessage] = None
    ) -> str:
        """构建聊天提示词"""
        
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
                doc_title = getattr(context, 'document_title', None) or f"文档{i}"
                prompt_parts.append(f"\n【文档{i}: {doc_title}】")
                prompt_parts.append(f"内容: {context.content}")
                
                # 获取相似度分数（兼容不同的字段名）
                score = getattr(context, 'similarity_score', getattr(context, 'score', 0))
                prompt_parts.append(f"相似度: {score:.3f}")
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
    
    def build_summary_prompt(
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
            
            # 获取相似度分数（兼容不同的字段名）
            score = getattr(context, 'similarity_score', getattr(context, 'score', 0))
            
            context_text += f"""
=== 摘要 {i} ({scope_level} 级别{topics_text}) ===
{context.content}
相关性得分: {score:.3f}
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


class AIGenerationService:
    """AI生成服务"""
    
    def __init__(self, ai_client, config: ChatConfiguration):
        self.ai_client = ai_client
        self.config = config
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    async def generate_response(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Tuple[str, int]:
        """生成AI回答"""
        
        if not self.ai_client:
            raise Exception("OpenAI客户端未初始化，请检查API密钥配置")
        
        try:
            self.logger.debug(f"🤖 开始AI生成 - 模型: {self.config.chat_model}, "
                            f"max_tokens: {max_tokens}, temperature: {temperature}")
            
            response = await self.ai_client.chat.completions.create(
                model=self.config.chat_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            self.logger.info(f"✅ AI生成成功 - tokens: {tokens_used}, "
                           f"内容长度: {len(content) if content else 0}")
            
            return content, tokens_used
            
        except Exception as e:
            self.logger.error(f"❌ AI生成失败: {e}")
            error_response = f"抱歉，AI服务暂时不可用。错误信息: {str(e)}"
            return error_response, 0
    
    async def generate_response_stream(
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
            self.logger.debug(f"🌊 开始AI流式生成 - 模型: {self.config.chat_model}")
            
            stream = await self.ai_client.chat.completions.create(
                model=self.config.chat_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            total_tokens = 0
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    total_tokens += 1  # 简化token计算
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "tokens": 1
                    }
            
            self.logger.info(f"✅ AI流式生成完成 - 估计tokens: {total_tokens}")
                    
        except Exception as e:
            self.logger.error(f"❌ 流式AI生成失败: {e}")
            yield {
                "content": f"抱歉，AI服务暂时不可用: {str(e)}",
                "tokens": 0
            }


class ConversationManager:
    """对话管理服务"""
    
    def __init__(self, es_service):
        self.es_service = es_service
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    async def save_conversation(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        topic_id: Optional[int] = None,
        retrieved_contexts: List[RetrievedContext] = None,
        ai_metadata: Dict[str, Any] = None
    ):
        """保存对话"""
        try:
            self.logger.debug(f"💾 保存对话 - conversation_id: {conversation_id}, "
                            f"topic_id: {topic_id}")
            
            await self.es_service.save_conversation(
                conversation_id=conversation_id,
                user_message=user_message,
                assistant_message=assistant_message,
                topic_id=topic_id,
                retrieved_contexts=retrieved_contexts or [],
                ai_metadata=ai_metadata or {}
            )
            
            self.logger.info(f"✅ 对话保存成功 - conversation_id: {conversation_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 对话保存失败: {e}")
            # 不重新抛出异常，避免影响主流程
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[ChatMessage]:
        """获取对话历史"""
        try:
            self.logger.debug(f"📜 获取对话历史 - conversation_id: {conversation_id}, limit: {limit}")
            
            messages = await self.es_service.get_conversation_messages(
                conversation_id, limit
            )
            
            self.logger.info(f"✅ 获取对话历史成功 - {len(messages)}条消息")
            return messages
            
        except Exception as e:
            self.logger.error(f"❌ 获取对话历史失败: {e}")
            return []


# 便捷函数
def get_chat_service() -> ChatService:
    """获取ChatService实例"""
    return ChatService()