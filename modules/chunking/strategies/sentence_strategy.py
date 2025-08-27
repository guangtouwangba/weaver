"""
句子分块策略

按句子边界进行文档分块，保持句子完整性。
"""

import time
import re
from typing import Any, Dict, List

from modules.chunking.base import (
    BaseChunkingStrategy,
    ChunkingContext,
    ChunkingResult, 
    StrategyPriority
)
from modules.chunking.strategy_factory import register_chunking_strategy


@register_chunking_strategy(
    name="sentence",
    metadata={
        "description": "按句子边界进行分块",
        "best_for": ["对话文本", "问答数据", "短文本"],
        "complexity": "中等",
        "speed": "快"
    }
)
class SentenceStrategy(BaseChunkingStrategy):
    """句子分块策略"""
    
    @property
    def name(self) -> str:
        return "sentence"
    
    @property
    def priority(self) -> StrategyPriority:
        return StrategyPriority.MEDIUM
    
    @property
    def supported_content_types(self) -> List[str]:
        return ["text/plain", "text/markdown", "text/html", "application/pdf"]
    
    def get_default_config(self) -> Dict[str, Any]:
        base_config = super().get_default_config()
        base_config.update({
            # 句子分割配置
            "sentence_endings": ['.', '!', '?', '。', '！', '？', '；'],
            "abbreviations": ['Dr', 'Mr', 'Mrs', 'Ms', 'Prof', 'Inc', 'Ltd', 'etc', 'vs'],
            "min_sentence_length": 20,
            "max_sentences_per_chunk": 10,
            
            # 句子合并配置
            "merge_short_sentences": True,
            "short_sentence_threshold": 50,
            "context_window": 2,  # 考虑前后句子的窗口大小
            
            # 语言特定配置
            "language_patterns": {
                "en": r'[.!?]+\s+[A-Z]',
                "zh": r'[。！？；]+\s*',
                "mixed": r'[.!?。！？；]+\s*'
            },
            
            # 质量控制
            "preserve_dialogue": True,
            "dialogue_markers": ['"', "'", '"', '"', ''', '''],
            "min_chunk_sentences": 2
        })
        return base_config
    
    async def can_handle(self, context: ChunkingContext) -> bool:
        """检查是否能处理文档"""
        base_check = await super().can_handle(context)
        if not base_check:
            return False
        
        # 句子策略需要文档有明显的句子结构
        return context.sentence_count >= 3
    
    async def estimate_performance(self, context: ChunkingContext) -> Dict[str, float]:
        """估算性能"""
        doc_length = context.document_length
        sentence_count = context.sentence_count
        
        # 处理速度基于句子数量
        processing_speed = 1.0
        if sentence_count > 500:
            processing_speed = 0.8
        elif sentence_count < 20:
            processing_speed = 1.1
        
        # 质量评分基于句子结构
        quality_score = 0.75
        if context.avg_sentence_length < 20:
            quality_score = 0.6  # 句子太短
        elif context.avg_sentence_length > 200:
            quality_score = 0.7  # 句子太长
        elif 40 <= context.avg_sentence_length <= 120:
            quality_score = 0.9  # 理想长度
        
        # 适用性基于文档类型
        suitability = 0.8
        if doc_length < 2000:  # 短文档更适合
            suitability = 0.9
        
        return {
            "quality_score": quality_score,
            "processing_speed": processing_speed,
            "memory_usage": 0.6,
            "suitability": suitability
        }
    
    async def chunk_document(self, context: ChunkingContext) -> ChunkingResult:
        """执行句子分块"""
        start_time = time.time()
        
        content = context.document.content
        target_chunk_size = context.target_chunk_size
        
        # 检测语言
        language = self._detect_language(content)
        
        # 分割句子
        sentences = self._split_sentences(content, language)
        
        # 处理句子
        processed_sentences = self._process_sentences(sentences)
        
        # 组合成块
        chunks = self._combine_sentences_into_chunks(
            context, processed_sentences, target_chunk_size
        )
        
        # 计算处理时间
        processing_time = (time.time() - start_time) * 1000
        
        # 计算质量指标
        if chunks:
            chunk_sizes = [len(chunk.content) for chunk in chunks]
            avg_size = sum(chunk_sizes) / len(chunk_sizes)
            size_variance = sum((size - avg_size) ** 2 for size in chunk_sizes) / len(chunk_sizes)
            quality_scores = [chunk.metadata.get("quality_score", 0.75) for chunk in chunks]
            overall_quality = sum(quality_scores) / len(quality_scores)
        else:
            avg_size = 0
            size_variance = 0
            overall_quality = 0
        
        return ChunkingResult(
            chunks=chunks,
            strategy_used=self.name,
            processing_time_ms=processing_time,
            avg_chunk_size=avg_size,
            size_variance=size_variance,
            quality_score=overall_quality,
            coverage_ratio=sum(len(c.content) for c in chunks) / len(content) if content else 0,
            strategy_metadata={
                "original_sentence_count": len(sentences),
                "processed_sentence_count": len(processed_sentences),
                "sentences_per_chunk": [
                    chunk.metadata.get("sentence_count", 1) for chunk in chunks
                ],
                "detected_language": language,
                "merge_operations": sum(1 for chunk in chunks 
                                     if chunk.metadata.get("sentence_count", 1) > 1)
            }
        )
    
    def _detect_language(self, content: str) -> str:
        """简单的语言检测"""
        # 统计中文字符比例
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        total_chars = len(content.replace(' ', '').replace('\n', ''))
        
        if total_chars == 0:
            return "en"
        
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.3:
            return "zh"
        elif chinese_ratio > 0.1:
            return "mixed"
        else:
            return "en"
    
    def _split_sentences(self, content: str, language: str) -> List[str]:
        """分割句子"""
        pattern = self.config.get("language_patterns", {}).get(language, r'[.!?]+\s+')
        
        # 使用正则表达式进行初步分割
        sentences = re.split(pattern, content)
        
        # 清理和过滤
        clean_sentences = []
        for sentence in sentences:
            cleaned = sentence.strip()
            if cleaned and len(cleaned) >= self.config.get("min_sentence_length", 20):
                # 处理缩写
                if not self._is_abbreviation_ending(cleaned):
                    clean_sentences.append(cleaned)
        
        return clean_sentences
    
    def _is_abbreviation_ending(self, sentence: str) -> bool:
        """检查是否以缩写结尾（可能是误分割）"""
        abbreviations = self.config.get("abbreviations", [])
        words = sentence.split()
        
        if words:
            last_word = words[-1].rstrip('.!?')
            return last_word in abbreviations
        
        return False
    
    def _process_sentences(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """处理句子，添加元数据"""
        processed = []
        
        for i, sentence in enumerate(sentences):
            sentence_info = {
                "content": sentence,
                "index": i,
                "length": len(sentence),
                "word_count": len(sentence.split()),
                "is_dialogue": self._is_dialogue(sentence),
                "is_question": self._is_question(sentence),
                "sentence_type": self._classify_sentence_type(sentence),
                "quality_score": self._calculate_sentence_quality(sentence)
            }
            processed.append(sentence_info)
        
        # 合并短句子（如果启用）
        if self.config.get("merge_short_sentences", True):
            processed = self._merge_short_sentences(processed)
        
        return processed
    
    def _is_dialogue(self, sentence: str) -> bool:
        """判断是否为对话"""
        if not self.config.get("preserve_dialogue", True):
            return False
        
        markers = self.config.get("dialogue_markers", ['"', "'"])
        stripped = sentence.strip()
        
        for marker in markers:
            if stripped.startswith(marker) and stripped.endswith(marker):
                return True
            if stripped.count(marker) >= 2:
                return True
        
        return False
    
    def _is_question(self, sentence: str) -> bool:
        """判断是否为疑问句"""
        return sentence.strip().endswith(('?', '？'))
    
    def _classify_sentence_type(self, sentence: str) -> str:
        """分类句子类型"""
        stripped = sentence.strip()
        
        if self._is_question(sentence):
            return "question"
        elif self._is_dialogue(sentence):
            return "dialogue"
        elif stripped.endswith(('!', '！')):
            return "exclamation"
        elif stripped.endswith(('.', '。')):
            return "statement"
        else:
            return "fragment"
    
    def _calculate_sentence_quality(self, sentence: str) -> float:
        """计算句子质量分数"""
        score = 1.0
        
        # 长度评分
        length = len(sentence)
        if length < 20:
            score *= 0.6
        elif length > 300:
            score *= 0.8
        elif 40 <= length <= 150:
            score *= 1.0
        
        # 完整性评分
        stripped = sentence.strip()
        if stripped.endswith(('.', '!', '?', '。', '！', '？')):
            score *= 1.1
        elif not stripped.endswith((',', '，', ';', '；')):
            score *= 0.7  # 可能不完整
        
        # 词汇密度
        words = sentence.split()
        if words:
            avg_word_length = sum(len(w) for w in words) / len(words)
            if 2 <= avg_word_length <= 10:
                score *= 1.0
            else:
                score *= 0.9
        
        return min(max(score, 0.0), 1.0)
    
    def _merge_short_sentences(self, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并过短的句子"""
        if not sentences:
            return sentences
        
        threshold = self.config.get("short_sentence_threshold", 50)
        merged = []
        current_group = []
        
        for sentence in sentences:
            if (sentence["length"] >= threshold or 
                sentence["is_dialogue"] or  # 保持对话完整性
                sentence["sentence_type"] == "question"):  # 保持问句独立
                
                # 完成当前组
                if current_group:
                    merged.append(self._merge_sentence_group(current_group))
                    current_group = []
                
                # 添加当前句子
                merged.append(sentence)
            else:
                current_group.append(sentence)
                
                # 如果组内句子够长了，完成组
                group_length = sum(s["length"] for s in current_group)
                if group_length >= threshold:
                    merged.append(self._merge_sentence_group(current_group))
                    current_group = []
        
        # 处理剩余的组
        if current_group:
            merged.append(self._merge_sentence_group(current_group))
        
        return merged
    
    def _merge_sentence_group(self, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并句子组"""
        if len(group) == 1:
            return group[0]
        
        # 合并内容，保持句子间的空格
        merged_content = " ".join(s["content"] for s in group)
        
        # 确定合并后的类型
        types = [s["sentence_type"] for s in group]
        if "question" in types:
            merged_type = "question"
        elif "dialogue" in types:
            merged_type = "dialogue"
        elif "exclamation" in types:
            merged_type = "exclamation"
        else:
            merged_type = "statement"
        
        return {
            "content": merged_content,
            "index": group[0]["index"],
            "length": len(merged_content),
            "word_count": sum(s["word_count"] for s in group),
            "is_dialogue": any(s["is_dialogue"] for s in group),
            "is_question": any(s["is_question"] for s in group),
            "sentence_type": merged_type,
            "quality_score": sum(s["quality_score"] for s in group) / len(group),
            "merged_count": len(group)
        }
    
    def _combine_sentences_into_chunks(
        self, 
        context: ChunkingContext, 
        sentences: List[Dict[str, Any]], 
        target_size: int
    ) -> List:
        """将句子组合成块"""
        chunks = []
        chunk_index = 0
        current_chunk_sentences = []
        current_length = 0
        
        max_sentences_per_chunk = self.config.get("max_sentences_per_chunk", 10)
        min_chunk_sentences = self.config.get("min_chunk_sentences", 2)
        
        for sentence in sentences:
            sentence_length = sentence["length"]
            
            # 检查是否应该开始新块
            should_start_new_chunk = (
                current_length > 0 and (
                    current_length + sentence_length > target_size or
                    len(current_chunk_sentences) >= max_sentences_per_chunk
                )
            )
            
            if should_start_new_chunk and len(current_chunk_sentences) >= min_chunk_sentences:
                # 完成当前块
                chunk = self._create_chunk_from_sentences(
                    context, current_chunk_sentences, chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # 重置
                current_chunk_sentences = []
                current_length = 0
            
            # 添加句子到当前块
            current_chunk_sentences.append(sentence)
            current_length += sentence_length
        
        # 处理最后一块
        if current_chunk_sentences:
            # 如果最后一块太小，尝试与前一块合并
            if (len(current_chunk_sentences) < min_chunk_sentences and 
                chunks and 
                len(chunks[-1].content) + current_length <= target_size * 1.2):
                
                # 合并到前一块
                last_chunk = chunks.pop()
                last_sentences = last_chunk.metadata.get("sentence_details", [])
                combined_sentences = last_sentences + current_chunk_sentences
                
                merged_chunk = self._create_chunk_from_sentences(
                    context, combined_sentences, len(chunks)
                )
                chunks.append(merged_chunk)
            else:
                chunk = self._create_chunk_from_sentences(
                    context, current_chunk_sentences, chunk_index
                )
                chunks.append(chunk)
        
        return chunks
    
    def _create_chunk_from_sentences(
        self, 
        context: ChunkingContext, 
        sentences: List[Dict[str, Any]], 
        chunk_index: int
    ):
        """从句子列表创建块"""
        # 组合句子内容
        content = " ".join(s["content"] for s in sentences)
        
        # 计算位置信息（简化）
        start_pos = chunk_index * context.target_chunk_size
        end_pos = start_pos + len(content)
        
        # 分析句子类型分布
        sentence_types = [s["sentence_type"] for s in sentences]
        type_counts = {stype: sentence_types.count(stype) for stype in set(sentence_types)}
        
        # 计算元数据
        metadata = {
            "sentence_count": len(sentences),
            "word_count": sum(s["word_count"] for s in sentences),
            "has_dialogue": any(s["is_dialogue"] for s in sentences),
            "has_questions": any(s["is_question"] for s in sentences),
            "sentence_type_distribution": type_counts,
            "avg_sentence_quality": sum(s["quality_score"] for s in sentences) / len(sentences),
            "sentence_lengths": [s["length"] for s in sentences],
            "split_method": "sentence_boundary",
            "sentence_details": sentences  # 保存详细信息供后续处理
        }
        
        # 创建文档块
        chunk = self._create_chunk(
            context=context,
            content=content,
            chunk_index=chunk_index,
            start_pos=start_pos,
            end_pos=end_pos,
            metadata=metadata
        )
        
        # 计算整体质量分数
        quality_score = self._calculate_chunk_quality(chunk, sentences)
        chunk.metadata["quality_score"] = quality_score
        
        return chunk
    
    def _calculate_chunk_quality(self, chunk, sentences: List[Dict[str, Any]]) -> float:
        """计算块的质量分数"""
        base_score = self._calculate_quality_score(chunk)
        
        # 句子特定的质量调整
        if sentences:
            # 句子质量平均分
            sentence_quality = sum(s["quality_score"] for s in sentences) / len(sentences)
            
            # 多样性奖励
            diversity_bonus = 0.0
            types = set(s["sentence_type"] for s in sentences)
            if len(types) > 1:
                diversity_bonus += 0.05  # 句子类型多样性
            
            # 对话和问题的连贯性奖励
            coherence_bonus = 0.0
            if any(s["is_dialogue"] for s in sentences) or any(s["is_question"] for s in sentences):
                coherence_bonus += 0.1  # 包含互动内容
            
            # 组合评分
            combined_score = (base_score * 0.6 + sentence_quality * 0.4) + diversity_bonus + coherence_bonus
            return min(max(combined_score, 0.0), 1.0)
        
        return base_score