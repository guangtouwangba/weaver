"""
段落分块策略

按段落边界进行文档分块，保持段落完整性。
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
    name="paragraph",
    metadata={
        "description": "按段落边界进行分块",
        "best_for": ["结构化文档", "学术论文", "文章"],
        "complexity": "中等",
        "speed": "快"
    }
)
class ParagraphStrategy(BaseChunkingStrategy):
    """段落分块策略"""
    
    @property
    def name(self) -> str:
        return "paragraph"
    
    @property
    def priority(self) -> StrategyPriority:
        return StrategyPriority.MEDIUM
    
    @property
    def supported_content_types(self) -> List[str]:
        return ["text/plain", "text/markdown", "text/html", "application/pdf"]
    
    def get_default_config(self) -> Dict[str, Any]:
        base_config = super().get_default_config()
        base_config.update({
            "paragraph_separators": ["\n\n", "\r\n\r\n", "\n\r\n\r"],
            "min_paragraph_length": 100,
            "max_paragraphs_per_chunk": 3,
            "merge_short_paragraphs": True,
            "preserve_line_breaks": False,
            "handle_list_items": True,
            "list_item_patterns": [r"^\s*[-*+]\s+", r"^\s*\d+\.\s+", r"^\s*[a-zA-Z]\.\s+"]
        })
        return base_config
    
    async def can_handle(self, context: ChunkingContext) -> bool:
        """检查是否能处理文档"""
        base_check = await super().can_handle(context)
        if not base_check:
            return False
        
        # 段落策略需要文档有明显的段落结构
        return context.paragraph_count >= 2
    
    async def estimate_performance(self, context: ChunkingContext) -> Dict[str, float]:
        """估算性能"""
        doc_length = context.document_length
        paragraph_count = context.paragraph_count
        
        # 处理速度基于段落数量和文档长度
        processing_speed = 1.0
        if paragraph_count > 100:
            processing_speed = 0.8
        elif paragraph_count < 10:
            processing_speed = 1.1
        
        # 质量评分基于段落结构
        quality_score = 0.8
        if context.avg_paragraph_length < 50:
            quality_score = 0.6  # 段落太短
        elif context.avg_paragraph_length > 2000:
            quality_score = 0.7  # 段落太长
        
        # 适用性基于文档结构
        suitability = 0.9 if context.has_structure_markers else 0.7
        
        return {
            "quality_score": quality_score,
            "processing_speed": processing_speed,
            "memory_usage": 0.7,
            "suitability": suitability
        }
    
    async def chunk_document(self, context: ChunkingContext) -> ChunkingResult:
        """执行段落分块"""
        start_time = time.time()
        
        content = context.document.content
        target_chunk_size = context.target_chunk_size
        
        # 提取段落
        paragraphs = self._extract_paragraphs(content)
        
        # 处理段落
        processed_paragraphs = self._process_paragraphs(paragraphs)
        
        # 组合成块
        chunks = self._combine_paragraphs_into_chunks(
            context, processed_paragraphs, target_chunk_size
        )
        
        # 计算处理时间
        processing_time = (time.time() - start_time) * 1000
        
        # 计算质量指标
        if chunks:
            chunk_sizes = [len(chunk.content) for chunk in chunks]
            avg_size = sum(chunk_sizes) / len(chunk_sizes)
            size_variance = sum((size - avg_size) ** 2 for size in chunk_sizes) / len(chunk_sizes)
            quality_scores = [chunk.metadata.get("quality_score", 0.7) for chunk in chunks]
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
                "original_paragraph_count": len(paragraphs),
                "processed_paragraph_count": len(processed_paragraphs),
                "paragraphs_per_chunk": [
                    chunk.metadata.get("paragraph_count", 1) for chunk in chunks
                ],
                "merge_operations": sum(1 for chunk in chunks 
                                     if chunk.metadata.get("paragraph_count", 1) > 1)
            }
        )
    
    def _extract_paragraphs(self, content: str) -> List[str]:
        """提取段落"""
        separators = self.config.get("paragraph_separators", ["\n\n"])
        
        # 使用多种分隔符分割
        paragraphs = [content]
        for separator in separators:
            new_paragraphs = []
            for paragraph in paragraphs:
                new_paragraphs.extend(paragraph.split(separator))
            paragraphs = new_paragraphs
        
        # 清理和过滤段落
        clean_paragraphs = []
        for paragraph in paragraphs:
            cleaned = paragraph.strip()
            if cleaned and len(cleaned) >= self.config.get("min_paragraph_length", 50):
                clean_paragraphs.append(cleaned)
        
        return clean_paragraphs
    
    def _process_paragraphs(self, paragraphs: List[str]) -> List[Dict[str, Any]]:
        """处理段落，添加元数据"""
        processed = []
        
        for i, paragraph in enumerate(paragraphs):
            paragraph_info = {
                "content": paragraph,
                "index": i,
                "length": len(paragraph),
                "word_count": len(paragraph.split()),
                "is_list_item": self._is_list_item(paragraph),
                "is_header": self._is_header(paragraph),
                "quality_score": self._calculate_paragraph_quality(paragraph)
            }
            processed.append(paragraph_info)
        
        # 合并短段落（如果启用）
        if self.config.get("merge_short_paragraphs", True):
            processed = self._merge_short_paragraphs(processed)
        
        return processed
    
    def _is_list_item(self, paragraph: str) -> bool:
        """判断是否为列表项"""
        if not self.config.get("handle_list_items", True):
            return False
        
        patterns = self.config.get("list_item_patterns", [])
        for pattern in patterns:
            if re.match(pattern, paragraph.strip()):
                return True
        return False
    
    def _is_header(self, paragraph: str) -> bool:
        """判断是否为标题"""
        # 简单的标题检测
        stripped = paragraph.strip()
        
        # Markdown 标题
        if stripped.startswith("#"):
            return True
        
        # 短且以标点结尾可能是标题
        if (len(stripped) < 100 and 
            not stripped.endswith(('.', '!', '?', '。', '！', '？')) and
            stripped[0].isupper()):
            return True
        
        return False
    
    def _calculate_paragraph_quality(self, paragraph: str) -> float:
        """计算段落质量分数"""
        score = 1.0
        
        # 长度评分
        length = len(paragraph)
        if length < 100:
            score *= 0.7
        elif length > 2000:
            score *= 0.8
        elif 200 <= length <= 1000:
            score *= 1.0
        
        # 句子完整性
        if paragraph.strip().endswith(('.', '!', '?', '。', '！', '？')):
            score *= 1.1
        elif paragraph.strip().endswith(','):
            score *= 0.8
        
        # 内容密度
        words = paragraph.split()
        if words:
            avg_word_length = sum(len(w) for w in words) / len(words)
            if 3 <= avg_word_length <= 8:
                score *= 1.0
            else:
                score *= 0.9
        
        return min(max(score, 0.0), 1.0)
    
    def _merge_short_paragraphs(self, paragraphs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并过短的段落"""
        if not paragraphs:
            return paragraphs
        
        min_length = self.config.get("min_paragraph_length", 100)
        merged = []
        current_group = []
        current_length = 0
        
        for paragraph in paragraphs:
            if (paragraph["length"] >= min_length or 
                paragraph["is_header"] or 
                (current_length > 0 and current_length + paragraph["length"] > min_length * 2)):
                
                # 完成当前组
                if current_group:
                    merged.append(self._merge_paragraph_group(current_group))
                    current_group = []
                    current_length = 0
                
                # 添加当前段落
                if paragraph["length"] >= min_length or paragraph["is_header"]:
                    merged.append(paragraph)
                else:
                    current_group = [paragraph]
                    current_length = paragraph["length"]
            else:
                current_group.append(paragraph)
                current_length += paragraph["length"]
        
        # 处理剩余的组
        if current_group:
            merged.append(self._merge_paragraph_group(current_group))
        
        return merged
    
    def _merge_paragraph_group(self, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并段落组"""
        if len(group) == 1:
            return group[0]
        
        # 合并内容
        separator = "\n\n" if not self.config.get("preserve_line_breaks", False) else "\n"
        merged_content = separator.join(p["content"] for p in group)
        
        return {
            "content": merged_content,
            "index": group[0]["index"],
            "length": len(merged_content),
            "word_count": sum(p["word_count"] for p in group),
            "is_list_item": any(p["is_list_item"] for p in group),
            "is_header": any(p["is_header"] for p in group),
            "quality_score": sum(p["quality_score"] for p in group) / len(group),
            "merged_count": len(group)
        }
    
    def _combine_paragraphs_into_chunks(
        self, 
        context: ChunkingContext, 
        paragraphs: List[Dict[str, Any]], 
        target_size: int
    ) -> List:
        """将段落组合成块"""
        chunks = []
        chunk_index = 0
        current_chunk_paragraphs = []
        current_length = 0
        
        max_paragraphs_per_chunk = self.config.get("max_paragraphs_per_chunk", 3)
        
        for paragraph in paragraphs:
            para_length = paragraph["length"]
            
            # 检查是否应该开始新块
            should_start_new_chunk = (
                current_length > 0 and (
                    current_length + para_length > target_size or
                    len(current_chunk_paragraphs) >= max_paragraphs_per_chunk or
                    paragraph["is_header"]  # 标题开始新块
                )
            )
            
            if should_start_new_chunk:
                # 完成当前块
                chunk = self._create_chunk_from_paragraphs(
                    context, current_chunk_paragraphs, chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # 重置
                current_chunk_paragraphs = []
                current_length = 0
            
            # 添加段落到当前块
            current_chunk_paragraphs.append(paragraph)
            current_length += para_length
        
        # 处理最后一块
        if current_chunk_paragraphs:
            chunk = self._create_chunk_from_paragraphs(
                context, current_chunk_paragraphs, chunk_index
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk_from_paragraphs(
        self, 
        context: ChunkingContext, 
        paragraphs: List[Dict[str, Any]], 
        chunk_index: int
    ):
        """从段落列表创建块"""
        # 组合段落内容
        separator = "\n\n" if not self.config.get("preserve_line_breaks", False) else "\n"
        content = separator.join(p["content"] for p in paragraphs)
        
        # 计算位置信息（简化）
        start_pos = chunk_index * context.target_chunk_size
        end_pos = start_pos + len(content)
        
        # 计算元数据
        metadata = {
            "paragraph_count": len(paragraphs),
            "word_count": sum(p["word_count"] for p in paragraphs),
            "has_headers": any(p["is_header"] for p in paragraphs),
            "has_list_items": any(p["is_list_item"] for p in paragraphs),
            "avg_paragraph_quality": sum(p["quality_score"] for p in paragraphs) / len(paragraphs),
            "paragraph_lengths": [p["length"] for p in paragraphs],
            "split_method": "paragraph_boundary"
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
        quality_score = self._calculate_chunk_quality(chunk, paragraphs)
        chunk.metadata["quality_score"] = quality_score
        
        return chunk
    
    def _calculate_chunk_quality(self, chunk, paragraphs: List[Dict[str, Any]]) -> float:
        """计算块的质量分数"""
        base_score = self._calculate_quality_score(chunk)
        
        # 段落特定的质量调整
        if paragraphs:
            # 段落质量平均分
            para_quality = sum(p["quality_score"] for p in paragraphs) / len(paragraphs)
            
            # 结构完整性奖励
            structure_bonus = 0.0
            if any(p["is_header"] for p in paragraphs):
                structure_bonus += 0.1  # 包含标题
            if len(paragraphs) <= 3:  # 合理的段落数量
                structure_bonus += 0.05
            
            # 组合评分
            combined_score = (base_score * 0.7 + para_quality * 0.3) + structure_bonus
            return min(max(combined_score, 0.0), 1.0)
        
        return base_score