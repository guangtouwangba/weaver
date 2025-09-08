"""
BM25检索器实现

基于BM25算法的关键词检索器，用于补充向量检索的不足。
"""

import asyncio
import logging
import math
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from modules.rag.base import (
    IRetriever,
    RetrievedDocument,
    RAGContext,
    RAGPipelineError,
)

logger = logging.getLogger(__name__)


class BM25Retriever(IRetriever):
    """BM25检索器 - 基于关键词的检索"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # BM25参数
        self.k1 = config.get("k1", 1.5)  # 词频饱和参数
        self.b = config.get("b", 0.75)   # 长度归一化参数
        
        # 文档处理参数
        self.min_word_length = config.get("min_word_length", 2)
        self.max_word_length = config.get("max_word_length", 20)
        
        # 停用词
        self.stop_words = set(config.get("stop_words", self._get_default_stop_words()))
        
        # 文档索引
        self.documents: Dict[str, RetrievedDocument] = {}
        self.document_tokens: Dict[str, List[str]] = {}
        self.document_lengths: Dict[str, int] = {}
        self.term_frequencies: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.document_frequencies: Dict[str, int] = defaultdict(int)
        self.average_document_length: float = 0.0
        self.total_documents: int = 0
        
        logger.info(f"BM25Retriever 初始化: k1={self.k1}, b={self.b}")
    
    async def initialize(self) -> None:
        """初始化BM25检索器"""
        if self._initialized:
            return
        
        try:
            # 这里可以从数据库或文件加载预建索引
            # 目前使用空索引，需要通过add_documents方法添加文档
            
            self._initialized = True
            logger.info("BM25Retriever 初始化完成")
            
        except Exception as e:
            logger.error(f"BM25Retriever 初始化失败: {e}")
            raise RAGPipelineError(
                f"BM25检索器初始化失败: {e}",
                component_type=self.component_type
            )
    
    async def process(self, context: RAGContext) -> RAGContext:
        """处理RAG上下文 - 执行BM25检索"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 从上下文获取检索参数
            top_k = context.user_context.get("bm25_top_k", 10)
            filters = context.user_context.get("filters")
            
            # 执行BM25检索
            documents = await self.retrieve(
                query=context.query,
                top_k=top_k,
                filters=filters
            )
            
            # 标记为BM25检索结果
            for doc in documents:
                doc.source = "bm25"
                doc.metadata["retrieval_method"] = "bm25"
            
            # 更新上下文
            context.retrieved_documents.extend(documents)
            
            # 记录检索元数据
            context.processing_metadata["bm25_retrieval"] = {
                "documents_found": len(documents),
                "top_k": top_k,
                "index_size": self.total_documents,
                "avg_score": sum(doc.score for doc in documents) / len(documents) if documents else 0.0
            }
            
            logger.info(f"BM25检索完成: 找到 {len(documents)} 个文档")
            
            return context
            
        except Exception as e:
            logger.error(f"BM25检索失败: {e}")
            raise RAGPipelineError(
                f"BM25检索失败: {e}",
                component_type=self.component_type
            )
    
    async def retrieve(
        self, 
        query: str, 
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedDocument]:
        """执行BM25检索"""
        try:
            if self.total_documents == 0:
                logger.warning("BM25索引为空，无法检索")
                return []
            
            # 预处理查询
            query_tokens = self._tokenize(query)
            if not query_tokens:
                return []
            
            # 计算每个文档的BM25分数
            document_scores = {}
            
            for doc_id in self.documents:
                # 应用过滤器
                if filters and not self._apply_filters(self.documents[doc_id], filters):
                    continue
                
                score = self._calculate_bm25_score(query_tokens, doc_id)
                if score > 0:
                    document_scores[doc_id] = score
            
            # 按分数排序
            sorted_docs = sorted(
                document_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # 构建结果
            results = []
            for i, (doc_id, score) in enumerate(sorted_docs[:top_k]):
                doc = self.documents[doc_id]
                result_doc = RetrievedDocument(
                    id=doc.id,
                    content=doc.content,
                    score=score,
                    source="bm25",
                    metadata={**doc.metadata, "bm25_score": score},
                    rank=i + 1
                )
                results.append(result_doc)
            
            logger.debug(f"BM25检索完成: 查询='{query}', 结果数={len(results)}")
            
            return results
            
        except Exception as e:
            logger.error(f"BM25检索执行失败: {e}")
            raise RAGPipelineError(f"BM25检索执行失败: {e}")
    
    async def batch_retrieve(
        self, 
        queries: List[str], 
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[List[RetrievedDocument]]:
        """批量BM25检索"""
        try:
            tasks = [
                self.retrieve(query, top_k, filters)
                for query in queries
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            batch_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"批量BM25检索第 {i} 个查询失败: {result}")
                    batch_results.append([])
                else:
                    batch_results.append(result)
            
            return batch_results
            
        except Exception as e:
            logger.error(f"批量BM25检索失败: {e}")
            raise RAGPipelineError(f"批量BM25检索失败: {e}")
    
    async def add_documents(self, documents: List[RetrievedDocument]) -> None:
        """添加文档到BM25索引"""
        try:
            for doc in documents:
                await self.add_document(doc)
            
            # 重新计算平均文档长度
            if self.document_lengths:
                self.average_document_length = sum(self.document_lengths.values()) / len(self.document_lengths)
            
            logger.info(f"添加 {len(documents)} 个文档到BM25索引，总文档数: {self.total_documents}")
            
        except Exception as e:
            logger.error(f"添加文档到BM25索引失败: {e}")
            raise RAGPipelineError(f"添加文档到BM25索引失败: {e}")
    
    async def add_document(self, document: RetrievedDocument) -> None:
        """添加单个文档到BM25索引"""
        try:
            doc_id = document.id
            
            # 如果文档已存在，先移除
            if doc_id in self.documents:
                await self.remove_document(doc_id)
            
            # 分词
            tokens = self._tokenize(document.content)
            
            # 存储文档信息
            self.documents[doc_id] = document
            self.document_tokens[doc_id] = tokens
            self.document_lengths[doc_id] = len(tokens)
            
            # 计算词频
            token_counts = Counter(tokens)
            for term, count in token_counts.items():
                self.term_frequencies[doc_id][term] = count
                
                # 更新文档频率
                if term not in [t for other_doc in self.term_frequencies 
                               if other_doc != doc_id 
                               for t in self.term_frequencies[other_doc]]:
                    self.document_frequencies[term] = 1
                else:
                    # 重新计算文档频率（简化版本）
                    self.document_frequencies[term] = sum(
                        1 for other_doc in self.term_frequencies
                        if term in self.term_frequencies[other_doc]
                    )
            
            self.total_documents += 1
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise RAGPipelineError(f"添加文档失败: {e}")
    
    async def remove_document(self, doc_id: str) -> None:
        """从BM25索引移除文档"""
        try:
            if doc_id not in self.documents:
                return
            
            # 移除文档信息
            del self.documents[doc_id]
            del self.document_tokens[doc_id]
            del self.document_lengths[doc_id]
            
            # 更新词频统计
            if doc_id in self.term_frequencies:
                for term in self.term_frequencies[doc_id]:
                    # 重新计算文档频率
                    self.document_frequencies[term] = sum(
                        1 for other_doc in self.term_frequencies
                        if other_doc != doc_id and term in self.term_frequencies[other_doc]
                    )
                    
                    # 如果词不再出现在任何文档中，删除它
                    if self.document_frequencies[term] == 0:
                        del self.document_frequencies[term]
                
                del self.term_frequencies[doc_id]
            
            self.total_documents -= 1
            
        except Exception as e:
            logger.error(f"移除文档失败: {e}")
            raise RAGPipelineError(f"移除文档失败: {e}")
    
    def _calculate_bm25_score(self, query_tokens: List[str], doc_id: str) -> float:
        """计算BM25分数"""
        score = 0.0
        doc_length = self.document_lengths[doc_id]
        
        for term in query_tokens:
            if term not in self.term_frequencies[doc_id]:
                continue
            
            # 词频
            tf = self.term_frequencies[doc_id][term]
            
            # 文档频率
            df = self.document_frequencies.get(term, 0)
            if df == 0:
                continue
            
            # IDF计算
            idf = math.log((self.total_documents - df + 0.5) / (df + 0.5))
            
            # BM25公式
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.average_document_length))
            
            score += idf * (numerator / denominator)
        
        return score
    
    def _tokenize(self, text: str) -> List[str]:
        """文本分词"""
        # 转换为小写
        text = text.lower()
        
        # 使用正则表达式分词（支持中英文）
        # 匹配中文字符、英文单词、数字
        tokens = re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+|\d+', text)
        
        # 过滤停用词和长度不合适的词
        filtered_tokens = []
        for token in tokens:
            if (token not in self.stop_words and 
                self.min_word_length <= len(token) <= self.max_word_length):
                filtered_tokens.append(token)
        
        return filtered_tokens
    
    def _apply_filters(self, document: RetrievedDocument, filters: Dict[str, Any]) -> bool:
        """应用过滤条件"""
        try:
            # 元数据过滤
            if "metadata_filters" in filters:
                metadata_filters = filters["metadata_filters"]
                for key, expected_value in metadata_filters.items():
                    actual_value = document.metadata.get(key)
                    if actual_value != expected_value:
                        return False
            
            # 文档ID过滤
            if "document_ids" in filters:
                document_ids = filters["document_ids"]
                if document.id not in document_ids:
                    return False
            
            # 内容过滤
            if "content_filters" in filters:
                content_filters = filters["content_filters"]
                for key, pattern in content_filters.items():
                    if pattern and pattern.lower() not in document.content.lower():
                        return False
            
            return True
            
        except Exception as e:
            logger.warning(f"应用过滤条件时出错: {e}")
            return True  # 出错时不过滤
    
    def _get_default_stop_words(self) -> List[str]:
        """获取默认停用词列表"""
        return [
            # 中文停用词
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '里', '就是', '还', '把', '比', '或者', '已经', '但是',
            
            # 英文停用词
            'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'as', 'are', 'was', 'were',
            'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'shall', 'to', 'of', 'in', 'for', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'among', 'this', 'that', 'these', 'those', 'i', 'me',
            'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself',
            'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it',
            'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves'
        ]
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        return {
            "total_documents": self.total_documents,
            "total_terms": len(self.document_frequencies),
            "average_document_length": self.average_document_length,
            "parameters": {
                "k1": self.k1,
                "b": self.b
            },
            "stop_words_count": len(self.stop_words)
        }


class DatabaseBM25Retriever(BM25Retriever):
    """基于数据库的BM25检索器"""
    
    def __init__(self, db_session, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.db_session = db_session
        self.table_name = config.get("table_name", "documents")
        
        logger.info(f"DatabaseBM25Retriever 初始化: table={self.table_name}")
    
    async def initialize(self) -> None:
        """从数据库初始化BM25索引"""
        if self._initialized:
            return
        
        try:
            # 从数据库加载文档
            await self._load_documents_from_db()
            
            await super().initialize()
            
            logger.info(f"从数据库加载 {self.total_documents} 个文档到BM25索引")
            
        except Exception as e:
            logger.error(f"DatabaseBM25Retriever 初始化失败: {e}")
            raise RAGPipelineError(
                f"数据库BM25检索器初始化失败: {e}",
                component_type=self.component_type
            )
    
    async def _load_documents_from_db(self) -> None:
        """从数据库加载文档"""
        try:
            # 这里需要根据实际的数据库模型来实现
            # 示例代码，需要根据实际情况调整
            
            from modules.database.models import Document
            
            # 查询所有文档
            documents = self.db_session.query(Document).all()
            
            # 转换为RetrievedDocument并添加到索引
            for doc in documents:
                retrieved_doc = RetrievedDocument(
                    id=str(doc.id),
                    content=doc.content,
                    score=0.0,  # 初始分数
                    source="database",
                    metadata={
                        "title": doc.title,
                        "content_type": doc.content_type.value if hasattr(doc.content_type, 'value') else str(doc.content_type),
                        "created_at": doc.created_at.isoformat() if hasattr(doc, 'created_at') else None
                    }
                )
                
                await self.add_document(retrieved_doc)
            
        except Exception as e:
            logger.error(f"从数据库加载文档失败: {e}")
            raise RAGPipelineError(f"从数据库加载文档失败: {e}")
