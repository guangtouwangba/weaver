"""
Summary Query Handler

摘要查询处理器，专门处理需要高级概念和摘要信息的查询。
"""

import logging
from typing import Dict, Any, Optional, List

from .base import BaseQueryHandler

logger = logging.getLogger(__name__)


class SummaryQueryHandler(BaseQueryHandler):
    """摘要查询处理器"""
    
    def __init__(self, chat_service: Optional[Any] = None):
        super().__init__("summary_handler")
        self.chat_service = chat_service
        
        # 摘要特定配置
        self.default_max_results = 8  # 摘要查询需要更多结果来获取全面信息
        self.default_score_threshold = 0.4  # 摘要查询使用更低阈值，更包容
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
        
        logger.info(f"📋 SummaryQueryHandler处理【SUMMARY】类型查询: '{query}'")
        
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
            
            logger.info(f"📊 摘要查询参数: max_results={max_results}, score_threshold={score_threshold}, confidence={confidence}")
            
            # 构建摘要查询请求
            summary_request = self._build_summary_request(query, context, max_results, score_threshold)
            
            # 直接生成摘要回复，避免递归路由
            logger.info("🤖 SummaryQueryHandler使用AI客户端生成摘要风格回复...")
            response = await self._generate_summary_response(query, context, max_results, score_threshold, confidence)
            logger.info("✅ SummaryQueryHandler摘要回复生成完成")
            return response
                
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
        """根据置信度调整分数阈值 - 摘要查询使用更包容的阈值"""
        if confidence >= self.high_confidence_threshold:
            return self.default_score_threshold  # 0.4
        elif confidence >= 0.6:
            return max(0.3, self.default_score_threshold - 0.1)  # 0.3
        else:
            return max(0.25, self.default_score_threshold - 0.15)  # 0.25
    
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
            
            # 避免递归路由，直接生成AI回复
            return await self._generate_summary_response(enhanced_query, context, self.default_max_results, self.default_score_threshold, 0.5)
                
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
    
    async def _generate_summary_response(
        self,
        query: str,
        context: Dict[str, Any],
        max_results: int,
        score_threshold: float,
        confidence: float
    ) -> Dict[str, Any]:
        """实现双重向量检索策略的摘要回复生成"""
        try:
            import uuid
            from datetime import datetime
            
            topic_id = context.get("topic_id")
            
            # 智能检索策略：对于明确的topic摘要请求，使用直接检索
            is_direct_request = self._is_direct_topic_summary_request(query, topic_id)
            if is_direct_request:
                logger.info(f"🎯 检测到明确的topic摘要请求 (topic_id={topic_id})，启用直接检索模式")
                start_time = datetime.now()  # 为直接检索模式设置计时起点
                # 直接检索该topic的所有相关内容，不依赖向量相似度
                retrieved_contexts = await self._retrieve_topic_summaries_directly(topic_id, max_results)
                search_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                if retrieved_contexts:
                    logger.info(f"📊 直接检索成功: 检索到 {len(retrieved_contexts)} 个相关文档，耗时 {search_time_ms:.1f}ms")
                    
                    # 使用检索到的内容生成摘要
                    response = await self._generate_ai_summary(query, retrieved_contexts, confidence)
                    return {
                        "content": response,
                        "retrieved_contexts": retrieved_contexts[:max_results],
                        "metadata": {
                            "handler": "summary",
                            "search_type": "direct_topic_retrieval", 
                            "confidence": confidence,
                            "contexts_found": len(retrieved_contexts),
                            "search_time_ms": search_time_ms,
                            "topic_id": topic_id
                        },
                        "response_type": "direct_topic_summary",
                        "retrieval_used": True
                    }
                else:
                    logger.warning(f"📊 直接检索无结果，回退到常规检索模式")
                    # 回退到常规检索逻辑
                    pass
            else:
                logger.info(f"🔍 使用常规摘要检索模式")
                
            # 第一步：执行双重向量检索
            logger.info(f"🔍 开始双重向量棄取 - 查询: '{query}', max_results: {max_results}, threshold: {score_threshold}")
            
            retrieved_contexts = []
            search_time_ms = 0
            
            if self.chat_service:
                # 1. 检索普通document向量库
                try:
                    start_time = datetime.now()
                    
                    # 优先从Summaries集合检索摘要内容
                    if hasattr(self.chat_service, 'retrieve_contexts'):
                        logger.info(f"🔍 优先检索Summaries集合获取摘要内容")
                            
                        summaries_contexts = await self.chat_service.retrieve_contexts(
                            query, 
                            topic_id=topic_id,
                            max_results=max_results, 
                            score_threshold=score_threshold,
                            collection_name="Summaries"
                        )
                        
                        if summaries_contexts:
                            logger.info(f"✅ 从Summaries集合获取到 {len(summaries_contexts)} 个摘要")
                            retrieved_contexts.extend(summaries_contexts)
                        else:
                            logger.info(f"🔄 Summaries集合无结果，尝试Documents集合")
                                
                            documents_contexts = await self.chat_service.retrieve_contexts(
                                query, 
                                topic_id=topic_id,
                                max_results=max_results, 
                                score_threshold=score_threshold,
                                collection_name="documents"
                            )
                            retrieved_contexts.extend(documents_contexts)
                    
                    # 如果没有检索到结果，自动降低阈值重试（双集合策略）
                    if not retrieved_contexts and score_threshold > 0.25:
                        lower_threshold = max(0.25, score_threshold - 0.15)
                        logger.info(f"🔄 检索结果为空，降低阈值至 {lower_threshold} 重试双集合")
                        
                        if hasattr(self.chat_service, 'retrieve_contexts'):
                            # 优先重试Summaries集合
                            summaries_retry = await self.chat_service.retrieve_contexts(
                                query, 
                                topic_id=context.get("topic_id"),
                                max_results=max_results * 2,
                                score_threshold=lower_threshold,
                                collection_name="Summaries"
                            )
                            
                            if summaries_retry:
                                retrieved_contexts.extend(summaries_retry)
                                logger.info(f"✅ Summaries集合重试成功: {len(summaries_retry)} 个摘要")
                            else:
                                # Summaries重试失败，尝试Documents
                                documents_retry = await self.chat_service.retrieve_contexts(
                                    query, 
                                    topic_id=context.get("topic_id"),
                                    max_results=max_results * 2,
                                    score_threshold=lower_threshold,
                                    collection_name="documents"
                                )
                                retrieved_contexts.extend(documents_retry)
                                if documents_retry:
                                    logger.info(f"✅ Documents集合重试成功: {len(documents_retry)} 个文档")
                    
                    search_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                    logger.info(f"📊 向量检索完成: 检索到 {len(retrieved_contexts)} 个相关文档，耗时 {search_time_ms:.1f}ms")
                    
                except Exception as e:
                    logger.warning(f"向量检索失败: {e}")
            
            # 第二步：基于检索结果生成摘要回答
            if hasattr(self.chat_service, 'ai_client') and self.chat_service.ai_client:
                
                # 构建基于上下文的摘要提示词
                context_text = ""
                if retrieved_contexts:
                    context_items = []
                    for i, ctx in enumerate(retrieved_contexts[:max_results], 1):
                        content = ctx.get('content', ctx.get('text', ''))[:500]  # 限制长度
                        context_items.append(f"文档{i}: {content}")
                    context_text = "\n\n".join(context_items)
                
                prompt = self._build_rag_summary_prompt(query, context_text)
                
                # 调用AI生成摘要
                ai_response = await self.chat_service.ai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "你是一个专业的文档摘要助手，擅长基于提供的文档内容生成高质量的摘要。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.3
                )
                
                content = ai_response.choices[0].message.content
                message_id = str(uuid.uuid4())
                conversation_id = context.get("conversation_id") or str(uuid.uuid4())
                
                return {
                    "content": content,
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                    "retrieved_contexts": retrieved_contexts[:max_results] if retrieved_contexts else [],
                    "ai_metadata": {
                        "model": "gpt-3.5-turbo",
                        "tokens_used": ai_response.usage.total_tokens if ai_response.usage else 0,
                        "generation_time_ms": 2000,
                        "search_time_ms": int(search_time_ms),
                        "temperature": 0.3,
                        "max_tokens": 1000
                    },
                    "metadata": {
                        "handler": "summary",
                        "search_type": "dual_vector_retrieval",
                        "confidence": confidence,
                        "contexts_found": len(retrieved_contexts),
                        "threshold_used": score_threshold
                    },
                    "response_type": "rag_summary",
                    "retrieval_used": True
                }
            
            # AI客户端不可用时的回退
            logger.warning("AI客户端不可用，返回基于检索结果的简单摘要")
            if retrieved_contexts:
                summary_content = f"基于检索到的 {len(retrieved_contexts)} 个相关文档片段，以下是对您问题的摘要回答：\n\n"
                for i, ctx in enumerate(retrieved_contexts[:3], 1):
                    content = ctx.get('content', ctx.get('text', ''))[:200]
                    summary_content += f"{i}. {content}...\n\n"
            else:
                # 改进无内容时的回复，提供更有用的信息
                topic_id = context.get("topic_id")
                if topic_id:
                    summary_content = f"""抱歉，topic {topic_id} 中暂时没有可用的文档内容进行总结。

可能的原因：
1. 该topic下的文档尚未完成处理和向量化
2. 文档内容与查询的语义相似度较低
3. 向量存储服务暂时不可用

建议：
- 请检查该topic下是否有已上传并处理完成的文档
- 或者尝试使用更具体的查询词语
- 如果问题持续存在，请联系系统管理员"""
                else:
                    summary_content = "抱歉，无法检索到相关的文档内容。请指定具体的topic或上传相关文档后再进行查询。"
            
            return {
                "content": summary_content,
                "retrieved_contexts": retrieved_contexts[:max_results] if retrieved_contexts else [],
                "metadata": {
                    "handler": "summary",
                    "search_type": "retrieval_fallback",
                    "confidence": confidence,
                    "contexts_found": len(retrieved_contexts)
                },
                "response_type": "retrieval_summary",
                "retrieval_used": True
            }
                
        except Exception as e:
            logger.error(f"摘要检索生成失败: {e}")
            return {
                "content": f"抱歉，生成摘要回复时出现错误: {str(e)}",
                "error": "summary_generation_failed",
                "metadata": {
                    "handler": "summary",
                    "error_type": type(e).__name__,
                    "confidence": confidence
                },
                "retrieval_used": False
            }
            
    def _is_direct_topic_summary_request(self, query: str, topic_id: Optional[int]) -> bool:
        """
        检测是否为直接的topic摘要请求
        
        当满足以下条件时，认为是直接的topic摘要请求：
        1. 有明确的topic_id
        2. 查询意图是询问topic的整体内容
        
        Args:
            query: 用户查询
            topic_id: 主题ID
            
        Returns:
            bool: 是否为直接topic摘要请求
        """
        if not topic_id:
            return False
            
        # 检测典型的摘要查询模式
        summary_patterns = [
            "这个topic讲了什么", "这个话题讲了什么", "这个主题讲了什么",
            "topic讲了什么", "话题讲了什么", "主题讲了什么",
            "这个topic的内容", "这个话题的内容", "这个主题的内容",
            "topic内容", "话题内容", "主题内容",
            "讲了什么", "说了什么", "包含什么",
            "总结", "概括", "摘要", "概述"
        ]
        
        query_lower = query.lower().strip()
        for pattern in summary_patterns:
            if pattern in query_lower:
                return True
                
        return False
    
    async def _retrieve_topic_summaries_directly(self, topic_id: int, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        直接检索指定topic的所有摘要内容，不依赖向量相似度匹配
        
        Args:
            topic_id: 主题ID
            max_results: 最大结果数
            
        Returns:
            List[Dict[str, Any]]: 检索到的摘要内容列表
        """
        try:
            logger.info(f"🎯 执行topic_id={topic_id}的直接摘要检索（忽略相似度匹配）")
            
            if not self.chat_service or not hasattr(self.chat_service, 'retrieve_contexts'):
                logger.warning("ChatService不可用，无法执行直接摘要检索")
                return []
            
            # 使用极低的阈值进行检索，几乎不过滤任何结果
            direct_summaries = await self.chat_service.retrieve_contexts(
                query="topic摘要内容",  # 通用查询词，因为我们主要依赖topic_id过滤
                topic_id=topic_id,
                max_results=max_results,
                score_threshold=0.01,  # 极低阈值，几乎接受所有该topic的内容
                collection_name="Summaries"
            )
            
            if direct_summaries:
                logger.info(f"✅ 直接检索到{len(direct_summaries)}个topic={topic_id}的摘要")
                return direct_summaries
            
            # 如果Summaries集合没有内容，尝试Documents集合
            logger.info(f"🔄 Summaries无内容，尝试从Documents检索topic={topic_id}的内容")
            direct_documents = await self.chat_service.retrieve_contexts(
                query="文档内容",
                topic_id=topic_id,
                max_results=max_results,
                score_threshold=0.01,
                collection_name="documents"
            )
            
            if direct_documents:
                logger.info(f"✅ 从Documents检索到{len(direct_documents)}个topic={topic_id}的内容")
            else:
                logger.warning(f"⚠️ 两个集合都未找到topic={topic_id}的内容")
                
            return direct_documents
            
        except Exception as e:
            logger.error(f"直接摘要检索失败: {e}")
            return []

    async def retrieve_contexts(
        self, 
        query: str, 
        context: Dict[str, Any], 
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        为流式API提供上下文检索接口
        
        Args:
            query: 用户查询
            context: 上下文信息
            max_results: 最大结果数（如果为None则使用Handler的默认值）
            
        Returns:
            List[Dict[str, Any]]: 检索到的上下文列表
        """
        try:
            # 使用SummaryHandler优化的参数
            confidence = context.get("route_confidence", 0.5)
            actual_max_results = max_results or self._get_max_results(confidence)
            topic_id = context.get("topic_id")
            
            # 智能检索策略：对于明确的topic摘要请求，使用直接检索
            is_direct_request = self._is_direct_topic_summary_request(query, topic_id)
            if is_direct_request:
                logger.info(f"🎯 检测到明确的topic摘要请求 (topic_id={topic_id})，启用直接检索模式")
                # 直接检索该topic的所有相关内容
                retrieved_contexts = await self._retrieve_topic_summaries_directly(topic_id, actual_max_results)
                logger.info(f"📊 直接检索完成: 获得 {len(retrieved_contexts)} 个相关内容")
                return retrieved_contexts
            else:
                score_threshold = self._get_score_threshold(confidence)
                logger.info(f"🔍 使用常规摘要检索模式，阈值: {score_threshold}")
            
            logger.info(f"📊 SummaryHandler流式检索 - max_results: {actual_max_results}, threshold: {score_threshold}")
            
            retrieved_contexts = []
            
            if self.chat_service and hasattr(self.chat_service, 'retrieve_contexts'):
                # 首先尝试从Summaries集合检索摘要内容
                if is_direct_request:
                    logger.info(f"🔍 直接检索topic_id={topic_id}的Summaries集合（低阈值模式）")
                else:
                    logger.info(f"🔍 优先检索Summaries集合")
                    
                summaries_contexts = await self.chat_service.retrieve_contexts(
                    query, 
                    topic_id=topic_id,
                    max_results=actual_max_results, 
                    score_threshold=score_threshold,
                    collection_name="Summaries"
                )
                
                if summaries_contexts:
                    logger.info(f"✅ 从Summaries集合检索到 {len(summaries_contexts)} 个摘要")
                    retrieved_contexts.extend(summaries_contexts)
                else:
                    # 如果Summaries集合没有结果，回退到Documents集合
                    if is_direct_request:
                        logger.info(f"🔄 Summaries集合无结果，以低阈值回退到Documents集合")
                    else:
                        logger.info(f"🔄 Summaries集合无结果，回退到Documents集合")
                        
                    documents_contexts = await self.chat_service.retrieve_contexts(
                        query, 
                        topic_id=topic_id,
                        max_results=actual_max_results, 
                        score_threshold=score_threshold,
                        collection_name="documents"
                    )
                    retrieved_contexts.extend(documents_contexts)
                
                # 如果没有检索到结果，自动降低阈值重试
                if not retrieved_contexts and score_threshold > 0.25:
                    lower_threshold = max(0.25, score_threshold - 0.15)
                    logger.info(f"🔄 检索结果为空，降低阈值至 {lower_threshold} 重试双集合检索")
                    
                    # 重试Summaries集合
                    summaries_retry = await self.chat_service.retrieve_contexts(
                        query, 
                        topic_id=context.get("topic_id"),
                        max_results=actual_max_results * 2,
                        score_threshold=lower_threshold,
                        collection_name="Summaries"
                    )
                    
                    if summaries_retry:
                        retrieved_contexts.extend(summaries_retry)
                        logger.info(f"✅ Summaries集合重试成功，找到 {len(summaries_retry)} 个结果")
                    else:
                        # 如果Summaries重试仍无结果，重试Documents集合
                        documents_retry = await self.chat_service.retrieve_contexts(
                            query, 
                            topic_id=context.get("topic_id"),
                            max_results=actual_max_results * 2,
                            score_threshold=lower_threshold,
                            collection_name="documents"
                        )
                        retrieved_contexts.extend(documents_retry)
                        if documents_retry:
                            logger.info(f"✅ Documents集合重试成功，找到 {len(documents_retry)} 个结果")
                    
                # 如果仍然没有结果，尝试跨topic检索或使用更宽泛的查询
                if not retrieved_contexts:
                    logger.info(f"🔄 topic检索无结果，尝试跨topic语义检索")
                    try:
                        # 使用更通用的查询词进行跨topic检索，优先检索Summaries
                        broad_query = self._build_broad_summary_query(query)
                        
                        # 先尝试跨topic检索Summaries集合
                        summaries_broad = await self.chat_service.retrieve_contexts(
                            broad_query,
                            topic_id=None,  # 跨topic检索 
                            max_results=min(10, actual_max_results * 3),
                            score_threshold=0.2,  # 更低的阈值
                            collection_name="Summaries"
                        )
                        
                        if summaries_broad:
                            retrieved_contexts.extend(summaries_broad[:actual_max_results])
                            logger.info(f"🎯 跨topic Summaries检索成功，找到 {len(summaries_broad)} 个摘要")
                        else:
                            # 如果Summaries没有结果，再尝试Documents
                            documents_broad = await self.chat_service.retrieve_contexts(
                                broad_query,
                                topic_id=None,
                                max_results=min(10, actual_max_results * 3),
                                score_threshold=0.2,
                                collection_name="documents"
                            )
                            if documents_broad:
                                retrieved_contexts.extend(documents_broad[:actual_max_results])
                                logger.info(f"🎯 跨topic Documents检索成功，找到 {len(documents_broad)} 个文档")
                                
                    except Exception as e:
                        logger.warning(f"跨topic检索失败: {e}")
                    
                logger.info(f"📊 SummaryHandler流式检索完成: {len(retrieved_contexts)} 个文档")
                
            return retrieved_contexts[:actual_max_results] if retrieved_contexts else []
            
        except Exception as e:
            logger.error(f"SummaryHandler流式检索失败: {e}")
            return []

    def _build_broad_summary_query(self, query: str) -> str:
        """构建更宽泛的摘要查询，用于跨topic检索"""
        # 提取查询中的关键概念，生成更通用的搜索词
        broad_queries = [
            "主要内容 核心观点",
            "重要信息 关键点", 
            "概述 总结",
            "文档 资料 内容",
            "主题 话题 领域"
        ]
        
        # 基于原查询选择最相关的宽泛查询
        if "什么" in query or "内容" in query:
            return broad_queries[0]
        elif "重要" in query or "关键" in query:
            return broad_queries[1]
        elif "概述" in query or "总结" in query:
            return broad_queries[2]
        else:
            return broad_queries[0]  # 默认使用第一个

    def _build_rag_summary_prompt(self, query: str, context_text: str) -> str:
        """构建基于检索内容的摘要提示词"""
        if context_text.strip():
            return f"""基于以下检索到的文档内容，请回答用户的问题并提供摘要。

检索到的相关文档内容：
{context_text}

用户问题：{query}

请基于上述文档内容，生成一个简洁、准确的摘要回答。要求：
1. 重点关注主要概念和核心观点
2. 整合多个文档片段的信息
3. 用中文简洁地回答
4. 如果文档内容不足以完全回答问题，请诚实说明

摘要回答："""
        else:
            return f"""用户问题：{query}

虽然没有检索到直接相关的文档内容，但请基于你的知识尽可能回答这个总结类问题。

请用中文简洁地回答："""