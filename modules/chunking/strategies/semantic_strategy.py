"""
语义分块策略

基于语义相似度进行文档分块，保持相关内容在同一块中。
"""

import time
import math
from typing import Any, Dict, List, Optional, Set
from collections import Counter

from modules.chunking.base import (
    BaseChunkingStrategy,
    ChunkingContext, 
    ChunkingResult,
    StrategyPriority
)
from modules.chunking.strategy_factory import register_chunking_strategy


@register_chunking_strategy(
    name="semantic",
    metadata={
        "description": "基于语义相似度的智能分块",
        "best_for": ["结构化文档", "学术论文", "技术文档"],
        "complexity": "高",
        "speed": "中等"
    }
)
class SemanticStrategy(BaseChunkingStrategy):
    """语义分块策略"""
    
    @property
    def name(self) -> str:
        return "semantic"
    
    @property
    def priority(self) -> StrategyPriority:
        return StrategyPriority.HIGH
    
    @property
    def supported_content_types(self) -> List[str]:
        return ["text/plain", "text/markdown", "application/pdf"]
    
    def get_default_config(self) -> Dict[str, Any]:
        base_config = super().get_default_config()
        base_config.update({
            "similarity_threshold": 0.3,    # 语义相似度阈值
            "min_similarity_threshold": 0.1, # 最小相似度阈值
            "max_similarity_threshold": 0.8, # 最大相似度阈值
            "paragraph_weight": 0.6,         # 段落边界权重
            "sentence_weight": 0.4,          # 句子边界权重
            "keyword_overlap_weight": 0.7,   # 关键词重叠权重
            "position_weight": 0.3,          # 位置权重
            "adaptive_threshold": True,      # 自适应阈值调整
            "min_chunk_sentences": 2,        # 最少句子数
            "max_chunk_sentences": 15,       # 最多句子数
            "stopwords": {"的", "了", "和", "是", "在", "有", "我", "你", "他", "她", "它",
                         "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        })
        return base_config
    
    async def can_handle(self, context: ChunkingContext) -> bool:
        """检查是否能处理文档"""
        base_check = await super().can_handle(context)
        if not base_check:
            return False
        
        # 语义分块适合有一定结构的文档
        return (
            context.document_length >= 1000 and  # 需要一定长度
            context.sentence_count >= 10 and     # 需要足够的句子
            context.paragraph_count >= 3         # 需要多个段落
        )
    
    async def estimate_performance(self, context: ChunkingContext) -> Dict[str, float]:
        """估算性能"""
        doc_length = context.document_length
        sentence_count = context.sentence_count
        
        # 质量评分：结构化文档质量更高
        quality_score = 0.8
        if context.has_structure_markers:
            quality_score = 0.9
        if context.paragraph_count / sentence_count > 0.3:  # 段落密度高
            quality_score += 0.05
        
        # 处理速度：受句子数量影响
        processing_speed = 0.7
        if sentence_count > 500:
            processing_speed = 0.5
        elif sentence_count < 100:
            processing_speed = 0.9
        
        # 内存使用：需要存储语义特征
        memory_usage = min(1.5, 1.0 + sentence_count / 1000)
        
        # 适用性：基于文档结构特征
        suitability = 0.6
        if context.has_structure_markers:
            suitability = 0.9
        if context.avg_paragraph_length > 500:  # 长段落更适合语义分块
            suitability += 0.1
        
        return {
            "quality_score": quality_score,
            "processing_speed": processing_speed,
            "memory_usage": memory_usage,
            "suitability": suitability
        }
    
    async def chunk_document(self, context: ChunkingContext) -> ChunkingResult:
        """执行语义分块"""
        start_time = time.time()
        
        content = context.document.content
        
        # 1. 文本预处理和分割
        sentences = self._extract_sentences(content)
        if len(sentences) < self.config["min_chunk_sentences"]:
            # 回退到简单分块
            return await self._fallback_chunking(context)
        
        # 2. 计算句子特征
        sentence_features = self._extract_sentence_features(sentences)
        
        # 3. 计算语义相似度矩阵
        similarity_matrix = self._compute_similarity_matrix(sentence_features)
        
        # 4. 自适应阈值调整
        threshold = self._adaptive_threshold_adjustment(similarity_matrix, context)
        
        # 5. 基于相似度进行分块
        chunk_boundaries = self._find_semantic_boundaries(
            sentences, similarity_matrix, threshold, context
        )
        
        # 6. 创建文档块
        chunks = self._create_semantic_chunks(
            content, sentences, chunk_boundaries, context
        )
        
        # 7. 后处理优化
        optimized_chunks = self._optimize_chunks(chunks, context)
        
        # 计算处理时间和质量指标
        processing_time = (time.time() - start_time) * 1000
        metrics = self._calculate_quality_metrics(optimized_chunks, sentences)
        
        return ChunkingResult(
            chunks=optimized_chunks,
            strategy_used=self.name,
            processing_time_ms=processing_time,
            avg_chunk_size=metrics["avg_chunk_size"],
            size_variance=metrics["size_variance"],
            quality_score=metrics["quality_score"],
            coverage_ratio=metrics["coverage_ratio"],
            strategy_metadata={
                "semantic_threshold": threshold,
                "total_sentences": len(sentences),
                "avg_similarity": metrics["avg_similarity"],
                "boundary_confidence": metrics["boundary_confidence"],
                "semantic_coherence": metrics["semantic_coherence"]
            }
        )
    
    def _extract_sentences(self, content: str) -> List[str]:
        """提取句子"""
        # 简化的句子分割（可以集成更sophisticated的NLP库）
        import re
        
        # 基于标点符号分割
        sentence_endings = r'[.!?。！？]\s+'
        sentences = re.split(sentence_endings, content)
        
        # 清理和过滤
        clean_sentences = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) >= 20 and len(sent.split()) >= 3:  # 至少20个字符和3个词
                clean_sentences.append(sent)
        
        return clean_sentences
    
    def _extract_sentence_features(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """提取句子特征"""
        stopwords = self.config["stopwords"]
        features = []
        
        for sent in sentences:
            words = sent.lower().split()
            # 移除停用词
            keywords = [w for w in words if w not in stopwords and len(w) > 2]
            
            feature = {
                "keywords": set(keywords),
                "keyword_freq": Counter(keywords),
                "length": len(sent),
                "word_count": len(words),
                "keyword_count": len(keywords),
                "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0
            }
            features.append(feature)
        
        return features
    
    def _compute_similarity_matrix(
        self, 
        sentence_features: List[Dict[str, Any]]
    ) -> List[List[float]]:
        """计算句子间相似度矩阵"""
        n = len(sentence_features)
        similarity_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                similarity = self._compute_sentence_similarity(
                    sentence_features[i], 
                    sentence_features[j]
                )
                similarity_matrix[i][j] = similarity
                similarity_matrix[j][i] = similarity
            similarity_matrix[i][i] = 1.0
        
        return similarity_matrix
    
    def _compute_sentence_similarity(
        self, 
        feat1: Dict[str, Any], 
        feat2: Dict[str, Any]
    ) -> float:
        """计算两个句子的相似度"""
        # Jaccard相似度（关键词重叠）
        keywords1 = feat1["keywords"]
        keywords2 = feat2["keywords"]
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        jaccard_sim = intersection / union if union > 0 else 0.0
        
        # 长度相似度
        len1, len2 = feat1["length"], feat2["length"]
        length_sim = 1.0 - abs(len1 - len2) / max(len1, len2, 1)
        
        # 词频相似度（简化版余弦相似度）
        freq1 = feat1["keyword_freq"]
        freq2 = feat2["keyword_freq"]
        common_words = set(freq1.keys()).intersection(set(freq2.keys()))
        
        if common_words:
            freq_sim = sum(min(freq1[w], freq2[w]) for w in common_words) / \
                      max(sum(freq1.values()), sum(freq2.values()), 1)
        else:
            freq_sim = 0.0
        
        # 加权组合
        keyword_weight = self.config["keyword_overlap_weight"]
        return (
            jaccard_sim * keyword_weight +
            length_sim * 0.2 + 
            freq_sim * 0.3
        )
    
    def _adaptive_threshold_adjustment(
        self, 
        similarity_matrix: List[List[float]], 
        context: ChunkingContext
    ) -> float:
        """自适应阈值调整"""
        if not self.config["adaptive_threshold"]:
            return self.config["similarity_threshold"]
        
        # 计算相似度分布统计
        similarities = []
        n = len(similarity_matrix)
        
        for i in range(n):
            for j in range(i + 1, n):
                similarities.append(similarity_matrix[i][j])
        
        if not similarities:
            return self.config["similarity_threshold"]
        
        # 基于分布调整阈值
        avg_similarity = sum(similarities) / len(similarities)
        std_similarity = math.sqrt(
            sum((s - avg_similarity) ** 2 for s in similarities) / len(similarities)
        )
        
        # 动态阈值计算
        base_threshold = self.config["similarity_threshold"]
        
        # 如果相似度普遍较低，降低阈值
        if avg_similarity < 0.2:
            adjusted_threshold = max(
                self.config["min_similarity_threshold"],
                base_threshold * 0.7
            )
        # 如果相似度普遍较高，提高阈值
        elif avg_similarity > 0.6:
            adjusted_threshold = min(
                self.config["max_similarity_threshold"],
                base_threshold * 1.3
            )
        else:
            # 基于标准差调整
            adjusted_threshold = min(
                max(
                    base_threshold - std_similarity * 0.5,
                    self.config["min_similarity_threshold"]
                ),
                self.config["max_similarity_threshold"]
            )
        
        return adjusted_threshold
    
    def _find_semantic_boundaries(
        self,
        sentences: List[str],
        similarity_matrix: List[List[float]],
        threshold: float,
        context: ChunkingContext
    ) -> List[int]:
        """找到语义边界"""
        n = len(sentences)
        boundaries = [0]  # 开始位置
        
        current_chunk_start = 0
        current_chunk_size = 0
        
        for i in range(1, n):
            # 计算与当前块的平均相似度
            chunk_similarities = []
            for j in range(current_chunk_start, i):
                chunk_similarities.append(similarity_matrix[i][j])
            
            avg_similarity = sum(chunk_similarities) / len(chunk_similarities) if chunk_similarities else 0
            
            # 估计当前块大小
            chunk_content = " ".join(sentences[current_chunk_start:i+1])
            estimated_size = len(chunk_content)
            
            # 决定是否创建边界
            should_split = (
                avg_similarity < threshold or  # 相似度低于阈值
                estimated_size > context.max_chunk_size or  # 超过最大大小
                (i - current_chunk_start) > self.config["max_chunk_sentences"]  # 超过最大句子数
            )
            
            # 确保不会创建过小的块
            min_sentences = self.config["min_chunk_sentences"]
            if (should_split and 
                (i - current_chunk_start) >= min_sentences and
                estimated_size >= context.min_chunk_size):
                
                boundaries.append(i)
                current_chunk_start = i
        
        # 添加结束位置
        if boundaries[-1] != n:
            boundaries.append(n)
        
        return boundaries
    
    def _create_semantic_chunks(
        self,
        content: str,
        sentences: List[str], 
        boundaries: List[int],
        context: ChunkingContext
    ) -> List:
        """创建语义块"""
        chunks = []
        
        for i in range(len(boundaries) - 1):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1]
            
            # 合并句子
            chunk_sentences = sentences[start_idx:end_idx]
            chunk_content = ". ".join(chunk_sentences)
            
            if len(chunk_content.strip()) >= context.min_chunk_size:
                # 计算在原文中的位置
                start_pos = content.find(sentences[start_idx]) if start_idx < len(sentences) else 0
                end_pos = start_pos + len(chunk_content)
                
                chunk = self._create_chunk(
                    context=context,
                    content=chunk_content,
                    chunk_index=i,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    metadata={
                        "sentence_count": len(chunk_sentences),
                        "semantic_boundary_score": self._calculate_boundary_score(
                            sentences, start_idx, end_idx
                        ),
                        "chunk_type": "semantic_group"
                    }
                )
                
                # 计算质量分数
                quality_score = self._calculate_semantic_quality_score(chunk, chunk_sentences)
                chunk.metadata["quality_score"] = quality_score
                
                chunks.append(chunk)
        
        return chunks
    
    def _calculate_boundary_score(
        self, 
        sentences: List[str], 
        start_idx: int, 
        end_idx: int
    ) -> float:
        """计算边界分数（语义一致性）"""
        chunk_sentences = sentences[start_idx:end_idx]
        if len(chunk_sentences) <= 1:
            return 1.0
        
        # 计算块内句子的平均相似度
        features = self._extract_sentence_features(chunk_sentences)
        total_similarity = 0.0
        pairs = 0
        
        for i in range(len(features)):
            for j in range(i + 1, len(features)):
                total_similarity += self._compute_sentence_similarity(features[i], features[j])
                pairs += 1
        
        return total_similarity / pairs if pairs > 0 else 0.0
    
    def _calculate_semantic_quality_score(self, chunk, sentences: List[str]) -> float:
        """计算语义块的质量分数"""
        base_score = self._calculate_quality_score(chunk)
        
        # 语义一致性加分
        semantic_score = chunk.metadata.get("semantic_boundary_score", 0.0)
        
        # 句子数量合理性
        sentence_count = len(sentences)
        optimal_range = (3, 8)  # 理想句子数范围
        
        if optimal_range[0] <= sentence_count <= optimal_range[1]:
            sentence_bonus = 1.1
        elif sentence_count < optimal_range[0]:
            sentence_bonus = 0.9
        else:
            sentence_bonus = 0.95
        
        return min((base_score + semantic_score * 0.3) * sentence_bonus, 1.0)
    
    def _optimize_chunks(self, chunks: List, context: ChunkingContext) -> List:
        """优化块质量"""
        if not chunks:
            return chunks
        
        optimized = []
        
        for chunk in chunks:
            # 检查块大小
            if len(chunk.content) < context.min_chunk_size:
                # 尝试合并到前一个块
                if optimized and len(optimized[-1].content + chunk.content) <= context.max_chunk_size:
                    # 合并块
                    prev_chunk = optimized[-1]
                    merged_content = prev_chunk.content + ". " + chunk.content
                    
                    prev_chunk.content = merged_content
                    prev_chunk.end_char = chunk.end_char
                    prev_chunk.metadata.update({
                        "merged_chunks": prev_chunk.metadata.get("merged_chunks", 0) + 1
                    })
                    continue
            
            optimized.append(chunk)
        
        # 重新编号
        for i, chunk in enumerate(optimized):
            chunk.chunk_index = i
        
        return optimized
    
    def _calculate_quality_metrics(self, chunks: List, sentences: List[str]) -> Dict[str, float]:
        """计算质量指标"""
        if not chunks:
            return {
                "avg_chunk_size": 0,
                "size_variance": 0,
                "quality_score": 0,
                "coverage_ratio": 0,
                "avg_similarity": 0,
                "boundary_confidence": 0,
                "semantic_coherence": 0
            }
        
        # 基本指标
        chunk_sizes = [len(chunk.content) for chunk in chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        size_variance = sum((size - avg_size) ** 2 for size in chunk_sizes) / len(chunk_sizes)
        
        quality_scores = [chunk.metadata.get("quality_score", 0.5) for chunk in chunks]
        overall_quality = sum(quality_scores) / len(quality_scores)
        
        # 语义相关指标
        boundary_scores = [chunk.metadata.get("semantic_boundary_score", 0.0) for chunk in chunks]
        boundary_confidence = sum(boundary_scores) / len(boundary_scores)
        
        return {
            "avg_chunk_size": avg_size,
            "size_variance": size_variance,
            "quality_score": overall_quality,
            "coverage_ratio": sum(len(c.content) for c in chunks) / sum(len(s) for s in sentences),
            "avg_similarity": boundary_confidence,
            "boundary_confidence": boundary_confidence,
            "semantic_coherence": min(overall_quality + boundary_confidence * 0.2, 1.0)
        }
    
    async def _fallback_chunking(self, context: ChunkingContext) -> ChunkingResult:
        """回退到简单分块"""
        from .fixed_size_strategy import FixedSizeStrategy
        
        fallback_strategy = FixedSizeStrategy(self.config)
        return await fallback_strategy.chunk_document(context)