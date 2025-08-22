"""
分块处理器

专门负责文档分块的高级处理器，支持多种分块策略和优化。
"""

import logging
from typing import List, Optional, Dict, Any, Union
import asyncio
import math

from .base import IDocumentProcessor, DocumentProcessorError
from .text_processor import TextProcessor
from ...models import (
    Document, DocumentChunk, ProcessingRequest, ProcessingResult,
    ProcessingStatus, ChunkingStrategy
)

logger = logging.getLogger(__name__)


class ChunkingProcessor(IDocumentProcessor):
    """分块处理器实现"""
    
    def __init__(self, 
                 default_chunk_size: int = 1000,
                 default_overlap: int = 200,
                 min_chunk_size: int = 50,
                 max_chunk_size: int = 4000,
                 quality_threshold: float = 0.8):
        """
        初始化分块处理器
        
        Args:
            default_chunk_size: 默认块大小
            default_overlap: 默认重叠大小
            min_chunk_size: 最小块大小
            max_chunk_size: 最大块大小
            quality_threshold: 质量阈值
        """
        self.default_chunk_size = default_chunk_size
        self.default_overlap = default_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.quality_threshold = quality_threshold
        
        # 使用文本处理器进行预处理
        self.text_processor = TextProcessor(min_chunk_size=min_chunk_size)
    
    async def initialize(self):
        """Initialize the chunking processor"""
        # All components are already initialized in __init__, nothing more needed
        pass
    
    @property
    def processor_name(self) -> str:
        """获取处理器名称"""
        return "ChunkingProcessor"
    
    @property
    def supported_strategies(self) -> List[str]:
        """获取支持的处理策略"""
        return [
            ChunkingStrategy.FIXED_SIZE.value,
            ChunkingStrategy.SEMANTIC.value,
            ChunkingStrategy.PARAGRAPH.value,
            ChunkingStrategy.SENTENCE.value
        ]
    
    async def validate_document(self, document: Document) -> bool:
        """验证文档是否可以处理"""
        return await self.text_processor.validate_document(document)
    
    async def clean_content(self, content: str) -> str:
        """清理文档内容"""
        return await self.text_processor.clean_content(content)
    
    async def create_chunks(self, document: Document, **kwargs) -> List[DocumentChunk]:
        """创建文档块（高级版本）"""
        try:
            strategy = kwargs.get('strategy', ChunkingStrategy.FIXED_SIZE)
            chunk_size = kwargs.get('chunk_size', self.default_chunk_size)
            overlap = kwargs.get('overlap', self.default_overlap)
            
            # 参数验证和调整
            chunk_size = max(self.min_chunk_size, min(chunk_size, self.max_chunk_size))
            overlap = max(0, min(overlap, chunk_size // 2))
            
            # 清理内容
            content = await self.clean_content(document.content)
            
            # 根据策略创建块
            if strategy == ChunkingStrategy.SEMANTIC:
                chunks = await self._create_semantic_chunks(document, content, chunk_size, overlap)
            else:
                # 使用文本处理器的基础分块
                chunks = await self.text_processor.create_chunks(
                    document,
                    strategy=strategy,
                    chunk_size=chunk_size,
                    overlap=overlap
                )
            
            # 优化块质量
            optimized_chunks = await self._optimize_chunks(chunks)
            
            # 添加块质量评分
            scored_chunks = await self._score_chunks(optimized_chunks)
            
            return scored_chunks
            
        except Exception as e:
            logger.error(f"创建高级文档块失败 {document.id}: {e}")
            raise DocumentProcessorError(
                f"高级分块失败: {str(e)}",
                document_id=document.id,
                error_code="ADVANCED_CHUNKING_FAILED"
            )
    
    async def process_document(self, request: ProcessingRequest) -> ProcessingResult:
        """处理文档（高级版本）"""
        start_time = asyncio.get_event_loop().time()
        document = request.document
        
        try:
            # 验证文档
            if not await self.validate_document(document):
                raise DocumentProcessorError(
                    f"文档验证失败: {document.id}",
                    document_id=document.id,
                    error_code="VALIDATION_FAILED"
                )
            
            # 分析文档特征
            doc_analysis = await self._analyze_document(document)
            
            # 根据分析结果调整参数
            optimized_params = await self._optimize_parameters(request, doc_analysis)
            
            # 创建文档块
            chunks = await self.create_chunks(
                document,
                strategy=optimized_params['strategy'],
                chunk_size=optimized_params['chunk_size'],
                overlap=optimized_params['overlap']
            )
            
            # 生成嵌入向量（如果需要）
            if request.generate_embeddings:
                chunks = await self._generate_embeddings(chunks)
            
            # 计算处理时间
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # 计算质量指标
            quality_metrics = await self._calculate_quality_metrics(chunks, doc_analysis)
            
            # 创建处理结果
            result = ProcessingResult(
                document_id=document.id,
                status=ProcessingStatus.COMPLETED,
                chunks_created=len(chunks),
                chunks=chunks,
                processing_time_ms=processing_time,
                metadata={
                    "processor_name": self.processor_name,
                    "optimized_params": optimized_params,
                    "document_analysis": doc_analysis,
                    "quality_metrics": quality_metrics,
                    "high_quality_chunks": sum(1 for c in chunks if c.metadata.get('quality_score', 0) >= self.quality_threshold)
                }
            )
            
            logger.info(f"高级文档处理完成 {document.id}: {len(chunks)} 块, {processing_time:.2f}ms")
            return result
            
        except DocumentProcessorError:
            raise
        except Exception as e:
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error(f"高级文档处理失败 {document.id}: {e}")
            
            return ProcessingResult(
                document_id=document.id,
                status=ProcessingStatus.FAILED,
                chunks_created=0,
                chunks=[],
                processing_time_ms=processing_time,
                error_message=str(e),
                metadata={"processor_name": self.processor_name}
            )
    
    async def _analyze_document(self, document: Document) -> Dict[str, Any]:
        """分析文档特征"""
        content = document.content
        
        analysis = {
            "length": len(content),
            "word_count": len(content.split()),
            "line_count": len(content.split('\n')),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "avg_line_length": 0,
            "avg_paragraph_length": 0,
            "has_structure": False,
            "content_type": document.content_type.value
        }
        
        lines = content.split('\n')
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        
        if lines:
            analysis["avg_line_length"] = sum(len(line) for line in lines) / len(lines)
        
        if paragraphs:
            analysis["avg_paragraph_length"] = sum(len(p) for p in paragraphs) / len(paragraphs)
        
        # 检测结构化内容
        structure_indicators = [
            '\n# ',      # Markdown标题
            '\n## ',     # Markdown子标题
            '\n1. ',     # 编号列表
            '\n- ',      # 无序列表
            '\n* ',      # 无序列表
            '```',       # 代码块
            '</h',       # HTML标题
            '<p>',       # HTML段落
        ]
        
        analysis["has_structure"] = any(indicator in content for indicator in structure_indicators)
        
        return analysis
    
    async def _optimize_parameters(self, request: ProcessingRequest, 
                                 analysis: Dict[str, Any]) -> Dict[str, Any]:
        """根据文档分析优化参数"""
        params = {
            "strategy": request.chunking_strategy,
            "chunk_size": request.chunk_size,
            "overlap": request.chunk_overlap
        }
        
        # 根据文档长度调整块大小
        doc_length = analysis["length"]
        if doc_length < 2000:
            params["chunk_size"] = min(params["chunk_size"], 500)
        elif doc_length > 50000:
            params["chunk_size"] = max(params["chunk_size"], 1500)
        
        # 根据段落结构调整策略
        if analysis["has_structure"] and params["strategy"] == ChunkingStrategy.FIXED_SIZE:
            avg_para_length = analysis["avg_paragraph_length"]
            if avg_para_length > 100 and avg_para_length < params["chunk_size"] * 0.8:
                params["strategy"] = ChunkingStrategy.PARAGRAPH
                logger.info(f"文档有良好结构，切换到段落分块策略")
        
        # 根据平均行长调整重叠
        avg_line_length = analysis["avg_line_length"]
        if avg_line_length > 200:  # 长行文本
            params["overlap"] = max(params["overlap"], 300)
        elif avg_line_length < 50:  # 短行文本
            params["overlap"] = min(params["overlap"], 100)
        
        return params
    
    async def _create_semantic_chunks(self, document: Document, content: str,
                                    chunk_size: int, overlap: int) -> List[DocumentChunk]:
        """创建语义块（简化版本）"""
        # 这里实现一个简化的语义分块
        # 在实际应用中，可以集成更复杂的NLP模型
        
        chunks = []
        
        # 首先按段落分割
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        current_chunk = ""
        chunk_index = 0
        start_position = 0
        
        for paragraph in paragraphs:
            # 计算语义相似度（简化版本 - 基于关键词重叠）
            similarity = self._calculate_semantic_similarity(current_chunk, paragraph)
            
            # 如果相似度高且大小允许，合并到当前块
            if (similarity > 0.3 and 
                len(current_chunk + paragraph) <= chunk_size):
                if current_chunk:
                    current_chunk += '\n\n' + paragraph
                else:
                    current_chunk = paragraph
            else:
                # 创建新块
                if current_chunk:
                    chunk = DocumentChunk(
                        document_id=document.id,
                        content=current_chunk.strip(),
                        chunk_index=chunk_index,
                        start_position=start_position,
                        end_position=start_position + len(current_chunk),
                        strategy=ChunkingStrategy.SEMANTIC,
                        metadata={
                            "type": "semantic_group",
                            "similarity_threshold": 0.3
                        }
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    start_position += len(current_chunk) + 2
                
                current_chunk = paragraph
        
        # 处理最后一个块
        if current_chunk:
            chunk = DocumentChunk(
                document_id=document.id,
                content=current_chunk.strip(),
                chunk_index=chunk_index,
                start_position=start_position,
                end_position=start_position + len(current_chunk),
                strategy=ChunkingStrategy.SEMANTIC,
                metadata={"type": "semantic_group"}
            )
            chunks.append(chunk)
        
        return chunks
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """计算语义相似度（简化版本）"""
        if not text1 or not text2:
            return 0.0
        
        # 提取关键词
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # 计算Jaccard相似度
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _optimize_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """优化块质量"""
        optimized = []
        
        for chunk in chunks:
            # 移除过短的块
            if len(chunk.content.strip()) < self.min_chunk_size:
                continue
            
            # 分割过长的块
            if len(chunk.content) > self.max_chunk_size:
                sub_chunks = await self._split_large_chunk(chunk)
                optimized.extend(sub_chunks)
            else:
                optimized.append(chunk)
        
        # 重新编号
        for i, chunk in enumerate(optimized):
            chunk.chunk_index = i
        
        return optimized
    
    async def _split_large_chunk(self, chunk: DocumentChunk) -> List[DocumentChunk]:
        """分割大块"""
        content = chunk.content
        target_size = self.default_chunk_size
        
        sub_chunks = []
        start = 0
        sub_index = 0
        
        while start < len(content):
            end = start + target_size
            
            # 尝试在句子边界分割
            if end < len(content):
                sentence_end = content.rfind('.', start, end)
                if sentence_end > start + target_size * 0.7:
                    end = sentence_end + 1
            
            sub_content = content[start:end].strip()
            
            sub_chunk = DocumentChunk(
                document_id=chunk.document_id,
                content=sub_content,
                chunk_index=chunk.chunk_index * 1000 + sub_index,  # 临时编号
                start_position=chunk.start_position + start,
                end_position=chunk.start_position + end,
                strategy=chunk.strategy,
                metadata={
                    **chunk.metadata,
                    "split_from_large_chunk": True,
                    "original_chunk_index": chunk.chunk_index
                }
            )
            
            sub_chunks.append(sub_chunk)
            sub_index += 1
            start = end
        
        return sub_chunks
    
    async def _score_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """为块评分"""
        for chunk in chunks:
            score = await self._calculate_chunk_quality_score(chunk)
            chunk.metadata["quality_score"] = score
        
        return chunks
    
    async def _calculate_chunk_quality_score(self, chunk: DocumentChunk) -> float:
        """计算块质量分数"""
        score = 1.0
        content = chunk.content
        
        # 长度分数
        length = len(content)
        if length < self.min_chunk_size:
            score *= 0.5
        elif length > self.max_chunk_size:
            score *= 0.7
        elif self.min_chunk_size * 2 <= length <= self.max_chunk_size * 0.8:
            score *= 1.0  # 理想长度
        
        # 内容完整性分数
        if content.strip().endswith(('.', '!', '?', '。', '！', '？')):
            score *= 1.1  # 完整句子
        elif content.strip().endswith(','):
            score *= 0.9  # 不完整
        
        # 内容密度分数
        words = content.split()
        if words:
            avg_word_length = sum(len(word) for word in words) / len(words)
            if 3 <= avg_word_length <= 8:
                score *= 1.0
            else:
                score *= 0.9
        
        return min(score, 1.0)
    
    async def _generate_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """生成嵌入向量（模拟）"""
        # 这里应该集成真实的向量化模型
        # 目前返回模拟向量
        
        for chunk in chunks:
            # 生成1536维的模拟向量（OpenAI embedding维度）
            import random
            chunk.embedding_vector = [random.random() for _ in range(1536)]
            chunk.metadata["has_embedding"] = True
        
        return chunks
    
    async def _calculate_quality_metrics(self, chunks: List[DocumentChunk], 
                                       analysis: Dict[str, Any]) -> Dict[str, Any]:
        """计算质量指标"""
        if not chunks:
            return {"overall_quality": 0.0}
        
        quality_scores = [chunk.metadata.get("quality_score", 0.5) for chunk in chunks]
        
        metrics = {
            "overall_quality": sum(quality_scores) / len(quality_scores),
            "high_quality_ratio": sum(1 for score in quality_scores if score >= self.quality_threshold) / len(quality_scores),
            "avg_chunk_size": sum(len(chunk.content) for chunk in chunks) / len(chunks),
            "size_variance": 0.0,
            "coverage_ratio": sum(len(chunk.content) for chunk in chunks) / analysis["length"]
        }
        
        # 计算大小方差
        avg_size = metrics["avg_chunk_size"]
        size_variance = sum((len(chunk.content) - avg_size) ** 2 for chunk in chunks) / len(chunks)
        metrics["size_variance"] = math.sqrt(size_variance)
        
        return metrics