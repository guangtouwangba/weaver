"""
重排序器组件实现

对检索到的文档进行重新排序，提高检索质量。
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from modules.rag.base import (
    IReranker,
    RetrievedDocument,
    RAGContext,
    RAGPipelineError,
)

logger = logging.getLogger(__name__)


class ScoreBasedReranker(IReranker):
    """基于分数的重排序器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 配置参数
        self.score_weights = config.get("score_weights", {
            "vector_score": 0.7,
            "bm25_score": 0.3
        })
        self.diversity_factor = config.get("diversity_factor", 0.1)
        self.enable_diversity = config.get("enable_diversity", True)
        
        logger.info(f"ScoreBasedReranker 初始化: weights={self.score_weights}")
    
    async def initialize(self) -> None:
        """初始化重排序器"""
        if self._initialized:
            return
        
        self._initialized = True
        logger.info("ScoreBasedReranker 初始化完成")
    
    async def process(self, context: RAGContext) -> RAGContext:
        """处理RAG上下文 - 重排序文档"""
        if not self._initialized:
            await self.initialize()
        
        try:
            if not context.retrieved_documents:
                return context
            
            # 从上下文获取重排序参数
            top_k = context.user_context.get("rerank_top_k")
            
            # 执行重排序
            reranked_docs = await self.rerank(
                query=context.query,
                documents=context.retrieved_documents,
                top_k=top_k
            )
            
            # 更新上下文
            context.retrieved_documents = reranked_docs
            
            # 记录重排序元数据
            context.processing_metadata["reranking"] = {
                "original_count": len(context.retrieved_documents),
                "reranked_count": len(reranked_docs),
                "method": "score_based",
                "weights": self.score_weights,
                "diversity_enabled": self.enable_diversity
            }
            
            logger.info(f"重排序完成: {len(reranked_docs)} 个文档")
            
            return context
            
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            raise RAGPipelineError(
                f"重排序失败: {e}",
                component_type=self.component_type
            )
    
    async def rerank(
        self, 
        query: str, 
        documents: List[RetrievedDocument],
        top_k: Optional[int] = None
    ) -> List[RetrievedDocument]:
        """重新排序文档"""
        try:
            if not documents:
                return []
            
            start_time = time.time()
            
            # 计算综合分数
            scored_docs = []
            for doc in documents:
                combined_score = self._calculate_combined_score(doc)
                
                # 创建新的文档对象以避免修改原始文档
                reranked_doc = RetrievedDocument(
                    id=doc.id,
                    content=doc.content,
                    score=combined_score,
                    source=doc.source,
                    metadata={**doc.metadata, "original_score": doc.score, "reranked": True},
                    rank=0  # 将在排序后设置
                )
                scored_docs.append(reranked_doc)
            
            # 按综合分数排序
            scored_docs.sort(key=lambda x: x.score, reverse=True)
            
            # 应用多样性重排序
            if self.enable_diversity:
                scored_docs = self._apply_diversity_reranking(scored_docs)
            
            # 限制结果数量
            if top_k:
                scored_docs = scored_docs[:top_k]
            
            # 更新排名
            for i, doc in enumerate(scored_docs):
                doc.rank = i + 1
            
            rerank_time = (time.time() - start_time) * 1000
            logger.debug(f"重排序耗时: {rerank_time:.1f}ms")
            
            return scored_docs
            
        except Exception as e:
            logger.error(f"重排序执行失败: {e}")
            raise RAGPipelineError(f"重排序执行失败: {e}")
    
    def _calculate_combined_score(self, document: RetrievedDocument) -> float:
        """计算综合分数"""
        combined_score = 0.0
        
        # 获取各种分数
        vector_score = document.metadata.get("vector_score", document.score)
        bm25_score = document.metadata.get("bm25_score", 0.0)
        
        # 归一化分数（简单线性归一化）
        normalized_vector_score = min(vector_score, 1.0)
        normalized_bm25_score = min(bm25_score / 10.0, 1.0)  # BM25分数通常较大，需要缩放
        
        # 加权组合
        combined_score += normalized_vector_score * self.score_weights.get("vector_score", 0.7)
        combined_score += normalized_bm25_score * self.score_weights.get("bm25_score", 0.3)
        
        # 添加其他因素
        # 文档长度因子（适中长度的文档可能更有用）
        content_length = len(document.content)
        if 100 <= content_length <= 1000:
            length_bonus = 0.1
        elif content_length > 1000:
            length_bonus = 0.05
        else:
            length_bonus = 0.0
        
        combined_score += length_bonus
        
        return combined_score
    
    def _apply_diversity_reranking(self, documents: List[RetrievedDocument]) -> List[RetrievedDocument]:
        """应用多样性重排序"""
        if len(documents) <= 1:
            return documents
        
        # 简单的多样性算法：避免内容过于相似的文档连续出现
        reranked = [documents[0]]  # 保留最高分的文档
        remaining = documents[1:]
        
        while remaining and len(reranked) < len(documents):
            best_doc = None
            best_score = -1
            
            for doc in remaining:
                # 计算与已选文档的相似度惩罚
                similarity_penalty = 0.0
                for selected_doc in reranked[-3:]:  # 只考虑最近3个文档
                    similarity = self._calculate_content_similarity(doc.content, selected_doc.content)
                    similarity_penalty += similarity * self.diversity_factor
                
                # 调整后的分数
                adjusted_score = doc.score - similarity_penalty
                
                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_doc = doc
            
            if best_doc:
                reranked.append(best_doc)
                remaining.remove(best_doc)
        
        return reranked
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """计算内容相似度（简化版本）"""
        # 简单的Jaccard相似度
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


class CrossEncoderReranker(IReranker):
    """基于CrossEncoder的重排序器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 配置参数
        self.model_name = config.get("model_name", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.max_length = config.get("max_length", 512)
        self.batch_size = config.get("batch_size", 32)
        self.device = config.get("device", "cpu")
        
        # 模型相关
        self.model = None
        self.tokenizer = None
        
        logger.info(f"CrossEncoderReranker 初始化: model={self.model_name}")
    
    async def initialize(self) -> None:
        """初始化CrossEncoder重排序器"""
        if self._initialized:
            return
        
        try:
            # 尝试加载模型
            try:
                from sentence_transformers import CrossEncoder
                
                self.model = CrossEncoder(self.model_name, device=self.device)
                logger.info(f"CrossEncoder模型加载成功: {self.model_name}")
                
            except ImportError:
                logger.warning("sentence-transformers未安装，回退到基于分数的重排序")
                # 回退到基于分数的重排序
                self.model = None
            except Exception as e:
                logger.warning(f"CrossEncoder模型加载失败: {e}，回退到基于分数的重排序")
                self.model = None
            
            self._initialized = True
            logger.info("CrossEncoderReranker 初始化完成")
            
        except Exception as e:
            logger.error(f"CrossEncoderReranker 初始化失败: {e}")
            raise RAGPipelineError(
                f"CrossEncoder重排序器初始化失败: {e}",
                component_type=self.component_type
            )
    
    async def process(self, context: RAGContext) -> RAGContext:
        """处理RAG上下文 - CrossEncoder重排序"""
        if not self._initialized:
            await self.initialize()
        
        try:
            if not context.retrieved_documents:
                return context
            
            # 从上下文获取重排序参数
            top_k = context.user_context.get("rerank_top_k")
            
            # 执行重排序
            reranked_docs = await self.rerank(
                query=context.query,
                documents=context.retrieved_documents,
                top_k=top_k
            )
            
            # 更新上下文
            context.retrieved_documents = reranked_docs
            
            # 记录重排序元数据
            context.processing_metadata["reranking"] = {
                "original_count": len(context.retrieved_documents),
                "reranked_count": len(reranked_docs),
                "method": "cross_encoder" if self.model else "fallback",
                "model": self.model_name if self.model else "score_based"
            }
            
            logger.info(f"CrossEncoder重排序完成: {len(reranked_docs)} 个文档")
            
            return context
            
        except Exception as e:
            logger.error(f"CrossEncoder重排序失败: {e}")
            raise RAGPipelineError(
                f"CrossEncoder重排序失败: {e}",
                component_type=self.component_type
            )
    
    async def rerank(
        self, 
        query: str, 
        documents: List[RetrievedDocument],
        top_k: Optional[int] = None
    ) -> List[RetrievedDocument]:
        """使用CrossEncoder重新排序文档"""
        try:
            if not documents:
                return []
            
            start_time = time.time()
            
            # 如果模型未加载，回退到简单排序
            if not self.model:
                logger.warning("CrossEncoder模型未加载，使用原始分数排序")
                sorted_docs = sorted(documents, key=lambda x: x.score, reverse=True)
                if top_k:
                    sorted_docs = sorted_docs[:top_k]
                for i, doc in enumerate(sorted_docs):
                    doc.rank = i + 1
                return sorted_docs
            
            # 准备查询-文档对
            query_doc_pairs = []
            for doc in documents:
                # 截断文档内容以适应模型输入长度限制
                content = doc.content[:self.max_length] if len(doc.content) > self.max_length else doc.content
                query_doc_pairs.append([query, content])
            
            # 批量计算相关性分数
            relevance_scores = []
            for i in range(0, len(query_doc_pairs), self.batch_size):
                batch = query_doc_pairs[i:i + self.batch_size]
                batch_scores = self.model.predict(batch)
                relevance_scores.extend(batch_scores.tolist())
            
            # 创建重排序后的文档
            scored_docs = []
            for doc, score in zip(documents, relevance_scores):
                reranked_doc = RetrievedDocument(
                    id=doc.id,
                    content=doc.content,
                    score=float(score),
                    source=doc.source,
                    metadata={**doc.metadata, "original_score": doc.score, "cross_encoder_score": float(score)},
                    rank=0
                )
                scored_docs.append(reranked_doc)
            
            # 按CrossEncoder分数排序
            scored_docs.sort(key=lambda x: x.score, reverse=True)
            
            # 限制结果数量
            if top_k:
                scored_docs = scored_docs[:top_k]
            
            # 更新排名
            for i, doc in enumerate(scored_docs):
                doc.rank = i + 1
            
            rerank_time = (time.time() - start_time) * 1000
            logger.debug(f"CrossEncoder重排序耗时: {rerank_time:.1f}ms")
            
            return scored_docs
            
        except Exception as e:
            logger.error(f"CrossEncoder重排序执行失败: {e}")
            raise RAGPipelineError(f"CrossEncoder重排序执行失败: {e}")


class HybridReranker(IReranker):
    """混合重排序器 - 组合多种重排序方法"""
    
    def __init__(self, rerankers: List[IReranker], config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.rerankers = rerankers
        
        # 配置参数
        self.combination_method = config.get("combination_method", "weighted_average")
        self.weights = config.get("weights", [1.0] * len(rerankers))
        
        logger.info(f"HybridReranker 初始化: {len(rerankers)} 个重排序器")
    
    async def initialize(self) -> None:
        """初始化混合重排序器"""
        if self._initialized:
            return
        
        try:
            # 初始化所有子重排序器
            for i, reranker in enumerate(self.rerankers):
                if not reranker.is_initialized:
                    await reranker.initialize()
                    logger.info(f"子重排序器 {i} 初始化完成: {reranker.component_name}")
            
            self._initialized = True
            logger.info("HybridReranker 初始化完成")
            
        except Exception as e:
            logger.error(f"HybridReranker 初始化失败: {e}")
            raise RAGPipelineError(
                f"混合重排序器初始化失败: {e}",
                component_type=self.component_type
            )
    
    async def process(self, context: RAGContext) -> RAGContext:
        """处理RAG上下文 - 混合重排序"""
        if not self._initialized:
            await self.initialize()
        
        try:
            if not context.retrieved_documents:
                return context
            
            # 从上下文获取重排序参数
            top_k = context.user_context.get("rerank_top_k")
            
            # 执行混合重排序
            reranked_docs = await self.rerank(
                query=context.query,
                documents=context.retrieved_documents,
                top_k=top_k
            )
            
            # 更新上下文
            context.retrieved_documents = reranked_docs
            
            # 记录重排序元数据
            context.processing_metadata["reranking"] = {
                "original_count": len(context.retrieved_documents),
                "reranked_count": len(reranked_docs),
                "method": "hybrid",
                "rerankers_used": len(self.rerankers),
                "combination_method": self.combination_method
            }
            
            logger.info(f"混合重排序完成: {len(reranked_docs)} 个文档")
            
            return context
            
        except Exception as e:
            logger.error(f"混合重排序失败: {e}")
            raise RAGPipelineError(
                f"混合重排序失败: {e}",
                component_type=self.component_type
            )
    
    async def rerank(
        self, 
        query: str, 
        documents: List[RetrievedDocument],
        top_k: Optional[int] = None
    ) -> List[RetrievedDocument]:
        """执行混合重排序"""
        try:
            if not documents:
                return []
            
            start_time = time.time()
            
            # 并行执行所有重排序器
            rerank_tasks = [
                reranker.rerank(query, documents.copy(), top_k)
                for reranker in self.rerankers
            ]
            
            rerank_results = await asyncio.gather(*rerank_tasks, return_exceptions=True)
            
            # 收集有效结果
            valid_results = []
            for i, result in enumerate(rerank_results):
                if isinstance(result, Exception):
                    logger.warning(f"重排序器 {i} 失败: {result}")
                    valid_results.append([])
                else:
                    valid_results.append(result)
            
            # 组合结果
            if self.combination_method == "weighted_average":
                combined_docs = self._weighted_average_combination(valid_results)
            elif self.combination_method == "rank_fusion":
                combined_docs = self._rank_fusion_combination(valid_results)
            else:
                # 简单选择第一个有效结果
                combined_docs = valid_results[0] if valid_results else []
            
            # 限制结果数量
            if top_k:
                combined_docs = combined_docs[:top_k]
            
            # 更新排名
            for i, doc in enumerate(combined_docs):
                doc.rank = i + 1
            
            rerank_time = (time.time() - start_time) * 1000
            logger.debug(f"混合重排序耗时: {rerank_time:.1f}ms")
            
            return combined_docs
            
        except Exception as e:
            logger.error(f"混合重排序执行失败: {e}")
            raise RAGPipelineError(f"混合重排序执行失败: {e}")
    
    def _weighted_average_combination(self, rerank_results: List[List[RetrievedDocument]]) -> List[RetrievedDocument]:
        """加权平均组合"""
        document_scores = {}
        
        for reranker_idx, documents in enumerate(rerank_results):
            if not documents:
                continue
                
            weight = self.weights[reranker_idx] if reranker_idx < len(self.weights) else 1.0
            
            for doc in documents:
                doc_id = doc.id
                weighted_score = doc.score * weight
                
                if doc_id not in document_scores:
                    document_scores[doc_id] = {
                        "document": doc,
                        "score": 0.0,
                        "count": 0
                    }
                
                document_scores[doc_id]["score"] += weighted_score
                document_scores[doc_id]["count"] += 1
        
        # 计算平均分数
        for doc_info in document_scores.values():
            doc_info["score"] = doc_info["score"] / doc_info["count"]
        
        # 按分数排序
        sorted_docs = sorted(
            document_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )
        
        # 构建最终结果
        result_documents = []
        for doc_info in sorted_docs:
            doc = doc_info["document"]
            doc.score = doc_info["score"]
            doc.metadata["hybrid_score"] = doc_info["score"]
            result_documents.append(doc)
        
        return result_documents
    
    def _rank_fusion_combination(self, rerank_results: List[List[RetrievedDocument]]) -> List[RetrievedDocument]:
        """排名融合组合"""
        document_scores = {}
        
        for reranker_idx, documents in enumerate(rerank_results):
            if not documents:
                continue
                
            weight = self.weights[reranker_idx] if reranker_idx < len(self.weights) else 1.0
            
            for rank, doc in enumerate(documents):
                doc_id = doc.id
                # 使用倒数排名融合
                rrf_score = weight / (60 + rank + 1)  # RRF with k=60
                
                if doc_id not in document_scores:
                    document_scores[doc_id] = {
                        "document": doc,
                        "score": 0.0
                    }
                
                document_scores[doc_id]["score"] += rrf_score
        
        # 按分数排序
        sorted_docs = sorted(
            document_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )
        
        # 构建最终结果
        result_documents = []
        for doc_info in sorted_docs:
            doc = doc_info["document"]
            doc.score = doc_info["score"]
            doc.metadata["rrf_score"] = doc_info["score"]
            result_documents.append(doc)
        
        return result_documents
