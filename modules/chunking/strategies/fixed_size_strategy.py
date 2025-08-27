"""
固定大小分块策略

最基础的分块策略，按固定字符数分割文档。
"""

import time
from typing import Any, Dict, List

from modules.chunking.base import (
    BaseChunkingStrategy,
    ChunkingContext,
    ChunkingResult, 
    StrategyPriority
)
from modules.chunking.strategy_factory import register_chunking_strategy


@register_chunking_strategy(
    name="fixed_size",
    metadata={
        "description": "按固定字符数分割文档",
        "best_for": ["通用文档", "长文本"],
        "complexity": "低",
        "speed": "快"
    }
)
class FixedSizeStrategy(BaseChunkingStrategy):
    """固定大小分块策略"""
    
    @property
    def name(self) -> str:
        return "fixed_size"
    
    @property
    def priority(self) -> StrategyPriority:
        return StrategyPriority.MEDIUM
    
    @property
    def supported_content_types(self) -> List[str]:
        return ["text/plain", "text/markdown", "text/html", "application/pdf"]
    
    def get_default_config(self) -> Dict[str, Any]:
        base_config = super().get_default_config()
        base_config.update({
            "chunk_size": 1000,
            "overlap_size": 200,
            "split_on_word_boundary": True,
            "word_boundary_threshold": 0.8,  # 在词边界分割的最小比例
            "preserve_sentences": False
        })
        return base_config
    
    async def can_handle(self, context: ChunkingContext) -> bool:
        """检查是否能处理文档"""
        base_check = await super().can_handle(context)
        if not base_check:
            return False
        
        # 固定大小策略适合所有文档，但有长度限制
        return context.document_length >= self.config.get("min_chunk_size", 50)
    
    async def estimate_performance(self, context: ChunkingContext) -> Dict[str, float]:
        """估算性能"""
        # 固定大小策略性能可预测
        doc_length = context.document_length
        
        # 处理速度基于文档长度
        processing_speed = 1.0
        if doc_length > 100000:  # 100KB以上
            processing_speed = 0.9
        elif doc_length < 5000:  # 5KB以下
            processing_speed = 1.1
        
        # 质量评分中等（不考虑语义完整性）
        quality_score = 0.6
        if context.has_structure_markers:
            quality_score = 0.5  # 结构化文档用固定大小分块质量下降
        
        return {
            "quality_score": quality_score,
            "processing_speed": processing_speed,
            "memory_usage": 0.8,  # 内存使用较少
            "suitability": 0.7
        }
    
    async def chunk_document(self, context: ChunkingContext) -> ChunkingResult:
        """执行固定大小分块"""
        start_time = time.time()
        
        content = context.document.content
        chunk_size = context.target_chunk_size
        overlap_size = context.overlap_size
        
        chunks = []
        chunk_index = 0
        start = 0
        
        while start < len(content):
            end = min(start + chunk_size, len(content))
            
            # 在词边界分割（如果启用）
            if (self.config.get("split_on_word_boundary", True) and 
                end < len(content) and 
                not content[end].isspace()):
                
                # 寻找最近的空格
                boundary_threshold = int(chunk_size * self.config.get("word_boundary_threshold", 0.8))
                last_space = content.rfind(" ", start + boundary_threshold, end)
                
                if last_space > start + boundary_threshold:
                    end = last_space
            
            # 提取块内容
            chunk_content = content[start:end].strip()
            
            if len(chunk_content) >= context.min_chunk_size:
                # 创建文档块
                chunk = self._create_chunk(
                    context=context,
                    content=chunk_content,
                    chunk_index=chunk_index,
                    start_pos=start,
                    end_pos=end,
                    metadata={
                        "split_method": "word_boundary" if end != start + chunk_size else "fixed_size",
                        "overlap_with_previous": overlap_size if chunk_index > 0 else 0
                    }
                )
                
                # 计算质量分数
                quality_score = self._calculate_quality_score(chunk)
                chunk.metadata["quality_score"] = quality_score
                
                chunks.append(chunk)
                chunk_index += 1
            
            # 计算下一个起始位置（考虑重叠）
            start = max(start + 1, end - overlap_size)
        
        # 计算处理时间
        processing_time = (time.time() - start_time) * 1000
        
        # 计算质量指标
        if chunks:
            chunk_sizes = [len(chunk.content) for chunk in chunks]
            avg_size = sum(chunk_sizes) / len(chunk_sizes)
            size_variance = sum((size - avg_size) ** 2 for size in chunk_sizes) / len(chunk_sizes)
            quality_scores = [chunk.metadata.get("quality_score", 0.5) for chunk in chunks]
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
                "chunk_size_config": chunk_size,
                "overlap_size_config": overlap_size,
                "word_boundary_splits": sum(1 for c in chunks 
                                          if c.metadata.get("split_method") == "word_boundary"),
                "total_original_length": len(content)
            }
        )