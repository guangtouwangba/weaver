"""
Summary Generation Service

摘要生成服务，负责从文档生成摘要并存储到摘要索引中。
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

try:
    import openai
except ImportError:
    openai = None

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_config
from logging_system import get_logger
from modules.services.base_service import BaseService
from modules.vector_store import SummaryDocument, VectorStoreError
from modules.vector_store.weaviate_service import WeaviateVectorStore
from modules.embedding.openai_service import OpenAIEmbeddingService
from modules.repository import DocumentRepository
from modules.schemas import Document

logger = get_logger(__name__)


class SummaryGenerationService(BaseService):
    """摘要生成服务"""
    
    def __init__(self, session: AsyncSession, vector_store: WeaviateVectorStore = None):
        super().__init__(session)
        self.config = get_config()
        self.vector_store = vector_store
        self.embedding_service: Optional[OpenAIEmbeddingService] = None
        self.ai_client = None
        
        # 摘要生成配置
        self.max_chunk_length = 4000  # 单个摘要处理的最大文本长度
        self.summary_overlap = 200    # 摘要重叠长度
        self.min_content_length = 500 # 最小内容长度才生成摘要
        
    async def initialize(self):
        """初始化服务"""
        try:
            # 初始化嵌入服务
            if hasattr(self.config, 'ai') and hasattr(self.config.ai, 'embedding'):
                openai_config = self.config.ai.embedding.openai
                api_key = getattr(openai_config, 'api_key', None)
                if api_key:
                    # 构建嵌入服务配置（包含代理）
                    service_kwargs = {'api_key': api_key}
                    
                    # 添加代理配置
                    http_proxy = getattr(openai_config, 'http_proxy', None)
                    https_proxy = getattr(openai_config, 'https_proxy', None)
                    api_base = getattr(openai_config, 'api_base', None)
                    
                    if http_proxy:
                        service_kwargs['http_proxy'] = http_proxy
                    if https_proxy:
                        service_kwargs['https_proxy'] = https_proxy
                    if api_base:
                        service_kwargs['api_base'] = api_base
                    
                    self.embedding_service = OpenAIEmbeddingService(**service_kwargs)
                    await self.embedding_service.initialize()
                    logger.info("✅ 嵌入服务初始化成功")
            
            # 初始化AI客户端用于生成摘要
            if hasattr(self.config, 'ai') and hasattr(self.config.ai, 'chat'):
                openai_chat_config = self.config.ai.chat.openai
                chat_api_key = getattr(openai_chat_config, 'api_key', None)
                if chat_api_key and openai:
                    # 构建AI客户端配置（包含代理）
                    client_kwargs = {'api_key': chat_api_key}
                    
                    # 添加API base URL配置
                    api_base = getattr(openai_chat_config, 'api_base', None)
                    if api_base:
                        client_kwargs['base_url'] = api_base
                    
                    # 添加代理配置
                    http_proxy = getattr(openai_chat_config, 'http_proxy', None)
                    https_proxy = getattr(openai_chat_config, 'https_proxy', None)
                    
                    if http_proxy or https_proxy:
                        import httpx
                        # 使用HTTPS代理（通常HTTP和HTTPS代理地址相同）
                        proxy_url = https_proxy or http_proxy
                        
                        # 创建httpx客户端with proxy
                        http_client = httpx.AsyncClient(proxy=proxy_url)
                        client_kwargs["http_client"] = http_client
                        logger.info(f"AI客户端配置代理: {proxy_url}")
                    
                    self.ai_client = openai.AsyncOpenAI(**client_kwargs)
                    logger.info("✅ AI客户端初始化成功")
            
            # 初始化向量存储
            if not self.vector_store:
                weaviate_url = getattr(self.config, 'weaviate_url', 'http://localhost:8080')
                self.vector_store = WeaviateVectorStore(url=weaviate_url)
                await self.vector_store.initialize()
                logger.info("✅ 向量存储初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 摘要服务初始化失败: {e}")
            raise
    
    async def generate_document_summary(
        self,
        document_id: str,
        content: str,
        topic_id: Optional[str] = None,
        force_regenerate: bool = False
    ) -> SummaryDocument:
        """为单个文档生成摘要"""
        
        if len(content) < self.min_content_length:
            raise ValueError(f"文档内容太短，无法生成摘要 (最小长度: {self.min_content_length})")
        
        logger.info(f"🔄 开始生成文档摘要: document_id={document_id}, content_length={len(content)}")
        
        try:
            # 检查是否已存在摘要（如果不强制重新生成）
            if not force_regenerate:
                existing_summary = await self._check_existing_summary(document_id)
                if existing_summary:
                    logger.info(f"📋 发现已存在的摘要: {document_id}")
                    return existing_summary
            
            # 将长文档分块处理
            chunks = self._split_content_for_summary(content)
            
            # 为每个块生成子摘要
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                logger.debug(f"🧮 处理第 {i+1}/{len(chunks)} 个文档块...")
                chunk_summary = await self._generate_chunk_summary(chunk, i+1, len(chunks))
                if chunk_summary:
                    chunk_summaries.append(chunk_summary)
            
            # 如果有多个块，需要生成总体摘要
            if len(chunk_summaries) > 1:
                final_summary = await self._generate_consolidated_summary(chunk_summaries)
            else:
                final_summary = chunk_summaries[0] if chunk_summaries else "无法生成摘要"
            
            # 提取关键主题
            key_topics = await self._extract_key_topics(final_summary, content[:2000])
            
            # 生成摘要向量
            summary_embedding = await self.embedding_service.generate_embedding(final_summary)
            
            # 创建摘要文档
            summary_doc = SummaryDocument(
                id=str(uuid.uuid4()),
                vector=summary_embedding,
                summary=final_summary,
                key_topics=key_topics,
                document_ids=[document_id],
                metadata={
                    "topic_id": topic_id,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "source_length": len(content),
                    "chunk_count": len(chunks),
                    "processing_method": "consolidated" if len(chunk_summaries) > 1 else "direct"
                },
                scope_level="document",
                created_at=datetime.now(timezone.utc)
            )
            
            # 存储到向量数据库
            result = await self.vector_store.upsert_summary_documents([summary_doc])
            
            if result.success_count > 0:
                logger.info(f"✅ 文档摘要生成并存储成功: {document_id}")
            else:
                logger.error(f"❌ 摘要存储失败: {result.errors}")
                raise VectorStoreError("摘要存储失败")
            
            return summary_doc
            
        except Exception as e:
            logger.error(f"❌ 文档摘要生成失败 {document_id}: {e}")
            raise
    
    async def generate_topic_summary(
        self,
        topic_id: str,
        document_ids: List[str],
        force_regenerate: bool = False
    ) -> SummaryDocument:
        """为主题生成综合摘要"""
        
        logger.info(f"🔄 开始生成主题摘要: topic_id={topic_id}, documents={len(document_ids)}")
        
        try:
            # 获取主题下所有文档的摘要
            document_summaries = []
            async with self.session.begin():
                doc_repo = DocumentRepository(self.session)
                
                for doc_id in document_ids:
                    document = await doc_repo.get_document_by_id(doc_id)
                    if document and document.content:
                        # 尝试获取已有摘要，否则生成新摘要
                        try:
                            doc_summary = await self.generate_document_summary(
                                doc_id,
                                document.content,
                                topic_id,
                                force_regenerate=False
                            )
                            document_summaries.append(doc_summary.summary)
                        except Exception as e:
                            logger.warning(f"⚠️ 跳过文档 {doc_id} 的摘要生成: {e}")
                            continue
            
            if not document_summaries:
                raise ValueError("没有可用的文档摘要来生成主题摘要")
            
            # 生成主题综合摘要
            topic_summary = await self._generate_topic_consolidated_summary(
                document_summaries,
                topic_id
            )
            
            # 提取主题关键词
            key_topics = await self._extract_topic_key_topics(topic_summary, document_summaries)
            
            # 生成摘要向量
            summary_embedding = await self.embedding_service.generate_embedding(topic_summary)
            
            # 创建主题摘要文档
            topic_summary_doc = SummaryDocument(
                id=str(uuid.uuid4()),
                vector=summary_embedding,
                summary=topic_summary,
                key_topics=key_topics,
                document_ids=document_ids,
                metadata={
                    "topic_id": topic_id,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "source_documents_count": len(document_ids),
                    "processing_method": "topic_consolidation"
                },
                scope_level="topic",
                created_at=datetime.now(timezone.utc)
            )
            
            # 存储主题摘要
            result = await self.vector_store.upsert_summary_documents([topic_summary_doc])
            
            if result.success_count > 0:
                logger.info(f"✅ 主题摘要生成并存储成功: {topic_id}")
            else:
                logger.error(f"❌ 主题摘要存储失败: {result.errors}")
                raise VectorStoreError("主题摘要存储失败")
            
            return topic_summary_doc
            
        except Exception as e:
            logger.error(f"❌ 主题摘要生成失败 {topic_id}: {e}")
            raise
    
    def _split_content_for_summary(self, content: str) -> List[str]:
        """将长内容分块以便生成摘要"""
        if len(content) <= self.max_chunk_length:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + self.max_chunk_length
            
            # 如果不是最后一块，尝试在句号处分割
            if end < len(content):
                # 向后查找句号
                last_period = content.rfind('.', start, end)
                if last_period > start + self.max_chunk_length // 2:
                    end = last_period + 1
            
            chunk = content[start:end]
            chunks.append(chunk)
            
            # 设置下一块的开始位置（考虑重叠）
            if end < len(content):
                start = end - self.summary_overlap
            else:
                break
        
        return chunks
    
    async def _generate_chunk_summary(self, chunk: str, chunk_num: int, total_chunks: int) -> str:
        """生成单个块的摘要"""
        if not self.ai_client:
            raise ValueError("AI客户端未初始化")
        
        context_info = f"（这是第{chunk_num}部分，共{total_chunks}部分）" if total_chunks > 1 else ""
        
        prompt = f"""请为以下文本生成一个简洁的摘要{context_info}：

文本内容：
{chunk}

要求：
1. 提取主要观点和核心信息
2. 保持逻辑清晰，内容准确
3. 长度控制在200-300字
4. 使用中文回答"""
        
        try:
            response = await self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=400
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ 生成块摘要失败: {e}")
            return f"第{chunk_num}部分摘要生成失败"
    
    async def _generate_consolidated_summary(self, chunk_summaries: List[str]) -> str:
        """生成综合摘要 - 使用递归式策略处理长文档"""
        if not self.ai_client:
            raise ValueError("AI客户端未初始化")
        
        # 如果摘要很少，直接处理
        if len(chunk_summaries) <= 3:
            return await self._merge_summaries_direct(chunk_summaries)
        
        # 递归式处理：分批合并摘要
        logger.info(f"📊 开始递归式摘要处理: {len(chunk_summaries)} 个子摘要")
        
        current_summaries = chunk_summaries.copy()
        batch_size = 4  # 每批处理4个摘要
        
        while len(current_summaries) > 1:
            next_level_summaries = []
            
            # 分批处理当前层级的摘要
            for i in range(0, len(current_summaries), batch_size):
                batch = current_summaries[i:i + batch_size]
                logger.debug(f"🔄 处理第 {i//batch_size + 1} 批摘要: {len(batch)} 个")
                
                merged_summary = await self._merge_summaries_direct(batch)
                next_level_summaries.append(merged_summary)
            
            current_summaries = next_level_summaries
            logger.info(f"📈 完成一轮合并，剩余摘要数: {len(current_summaries)}")
        
        final_summary = current_summaries[0]
        logger.info("✅ 递归式摘要处理完成")
        return final_summary
    
    async def _merge_summaries_direct(self, summaries: List[str]) -> str:
        """直接合并少量摘要"""
        if not summaries:
            return "无内容"
        
        if len(summaries) == 1:
            return summaries[0]
        
        summaries_text = "\n\n".join([
            f"部分{i+1}摘要：{summary}" 
            for i, summary in enumerate(summaries)
        ])
        
        # 估算token数量（粗略估算：4个字符≈1个token）
        estimated_tokens = len(summaries_text) // 4
        if estimated_tokens > 12000:  # 留出安全边界
            logger.warning(f"⚠️ 摘要内容过长 ({estimated_tokens} tokens)，进一步分割")
            # 如果还是太长，继续分割
            mid = len(summaries) // 2
            left_part = await self._merge_summaries_direct(summaries[:mid])
            right_part = await self._merge_summaries_direct(summaries[mid:])
            return await self._merge_summaries_direct([left_part, right_part])
        
        prompt = f"""以下是一个文档各部分的摘要，请生成一个统一的综合摘要：

{summaries_text}

要求：
1. 整合所有部分的核心信息
2. 消除重复，保持逻辑连贯
3. 突出主要观点和结论
4. 长度控制在300-500字
5. 使用中文回答"""
        
        try:
            response = await self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=600
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ 生成综合摘要失败: {e}")
            # 如果是token限制错误，尝试进一步分割
            if "context_length_exceeded" in str(e).lower():
                logger.warning("🔄 检测到token超限，尝试进一步分割")
                if len(summaries) > 1:
                    mid = len(summaries) // 2
                    left_part = await self._merge_summaries_direct(summaries[:mid])
                    right_part = await self._merge_summaries_direct(summaries[mid:])
                    return await self._merge_summaries_direct([left_part, right_part])
            return "综合摘要生成失败"
    
    async def _generate_topic_consolidated_summary(
        self,
        document_summaries: List[str],
        topic_id: str
    ) -> str:
        """生成主题综合摘要 - 使用递归策略处理多文档"""
        if not self.ai_client:
            raise ValueError("AI客户端未初始化")
        
        # 如果文档摘要很少，直接处理
        if len(document_summaries) <= 3:
            return await self._merge_topic_summaries_direct(document_summaries, topic_id)
        
        # 递归式处理：分批合并文档摘要
        logger.info(f"📊 开始主题递归式摘要处理: {len(document_summaries)} 个文档摘要")
        
        current_summaries = document_summaries.copy()
        batch_size = 4  # 每批处理4个文档摘要
        
        while len(current_summaries) > 1:
            next_level_summaries = []
            
            # 分批处理当前层级的摘要
            for i in range(0, len(current_summaries), batch_size):
                batch = current_summaries[i:i + batch_size]
                logger.debug(f"🔄 处理第 {i//batch_size + 1} 批文档摘要: {len(batch)} 个")
                
                merged_summary = await self._merge_topic_summaries_direct(batch, topic_id)
                next_level_summaries.append(merged_summary)
            
            current_summaries = next_level_summaries
            logger.info(f"📈 完成一轮主题合并，剩余摘要数: {len(current_summaries)}")
        
        final_summary = current_summaries[0]
        logger.info("✅ 主题递归式摘要处理完成")
        return final_summary
    
    async def _merge_topic_summaries_direct(self, summaries: List[str], topic_id: str) -> str:
        """直接合并少量主题摘要"""
        if not summaries:
            return "无内容"
        
        if len(summaries) == 1:
            return summaries[0]
        
        summaries_text = "\n\n".join([
            f"文档{i+1}摘要：{summary}" 
            for i, summary in enumerate(summaries)
        ])
        
        # 估算token数量（粗略估算：4个字符≈1个token）
        estimated_tokens = len(summaries_text) // 4
        if estimated_tokens > 12000:  # 留出安全边界
            logger.warning(f"⚠️ 主题摘要内容过长 ({estimated_tokens} tokens)，进一步分割")
            # 如果还是太长，继续分割
            mid = len(summaries) // 2
            left_part = await self._merge_topic_summaries_direct(summaries[:mid], topic_id)
            right_part = await self._merge_topic_summaries_direct(summaries[mid:], topic_id)
            return await self._merge_topic_summaries_direct([left_part, right_part], topic_id)
        
        prompt = f"""以下是主题 {topic_id} 下各个文档的摘要，请生成一个主题级别的综合摘要：

{summaries_text}

要求：
1. 从主题角度整合所有文档的信息
2. 识别共同模式和主要趋势
3. 突出主题的核心概念和关键洞察
4. 提供高层次的概括性描述
5. 长度控制在400-600字
6. 使用中文回答"""
        
        try:
            response = await self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ 生成主题综合摘要失败: {e}")
            # 如果是token限制错误，尝试进一步分割
            if "context_length_exceeded" in str(e).lower():
                logger.warning("🔄 检测到主题摘要token超限，尝试进一步分割")
                if len(summaries) > 1:
                    mid = len(summaries) // 2
                    left_part = await self._merge_topic_summaries_direct(summaries[:mid], topic_id)
                    right_part = await self._merge_topic_summaries_direct(summaries[mid:], topic_id)
                    return await self._merge_topic_summaries_direct([left_part, right_part], topic_id)
            return "主题综合摘要生成失败"
    
    async def _extract_key_topics(self, summary: str, content_preview: str) -> List[str]:
        """提取关键主题"""
        if not self.ai_client:
            return ["主题提取失败"]
        
        prompt = f"""基于以下摘要和内容片段，提取3-5个关键主题词：

摘要：
{summary}

内容片段：
{content_preview}

要求：
1. 提取最重要的主题关键词
2. 每个关键词2-4个字
3. 按重要性排序
4. 用逗号分隔
5. 只返回关键词，不要其他文字"""
        
        try:
            response = await self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )
            
            keywords_text = response.choices[0].message.content.strip()
            keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
            return keywords[:5]  # 最多5个关键词
            
        except Exception as e:
            logger.error(f"❌ 提取关键主题失败: {e}")
            return ["关键词提取失败"]
    
    async def _extract_topic_key_topics(
        self,
        topic_summary: str,
        document_summaries: List[str]
    ) -> List[str]:
        """提取主题级别的关键词"""
        if not self.ai_client:
            return ["主题关键词提取失败"]
        
        all_summaries = "\n".join(document_summaries)
        
        prompt = f"""基于主题摘要和相关文档摘要，提取3-5个最重要的主题关键词：

主题摘要：
{topic_summary}

相关文档摘要：
{all_summaries[:1500]}...

要求：
1. 提取能代表整个主题的核心关键词
2. 每个关键词2-4个字
3. 按重要性排序
4. 用逗号分隔
5. 只返回关键词，不要其他文字"""
        
        try:
            response = await self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )
            
            keywords_text = response.choices[0].message.content.strip()
            keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
            return keywords[:5]
            
        except Exception as e:
            logger.error(f"❌ 提取主题关键词失败: {e}")
            return ["主题关键词提取失败"]
    
    async def _check_existing_summary(self, document_id: str) -> Optional[SummaryDocument]:
        """检查是否已存在文档摘要"""
        try:
            # 这里应该查询摘要索引，简化实现先返回None
            # 实际实现中需要查询Weaviate的summaries collection
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ 检查已存在摘要失败: {e}")
            return None