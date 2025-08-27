"""
Enhanced Chunking Processor

集成新的策略工厂系统的高级分块处理器，用于替换原有的简单分块实现。
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from modules.models import (
    ChunkingStrategy,
    DocumentChunk,
    ProcessingRequest,
    ProcessingResult,
)
from modules.schemas.enums import ProcessingStatus
from modules.processors.base import DocumentProcessorError, IDocumentProcessor
from modules.schemas import Document

# 导入新的chunking系统
from modules.chunking.strategy_factory import get_global_factory, ChunkingStrategyError
from modules.chunking.base import ChunkingContext
from modules.chunking.config import (
    get_config_manager, 
    load_chunking_config_from_global,
    RuntimeChunkingConfig,
    ChunkingMode,
    DocumentType
)

logger = logging.getLogger(__name__)


class EnhancedChunkingProcessor(IDocumentProcessor):
    """增强的分块处理器，使用新的策略工厂系统"""

    def __init__(
        self,
        config: Optional[RuntimeChunkingConfig] = None,
        **kwargs
    ):
        """
        初始化增强分块处理器

        Args:
            config: 分块配置，如果为None则从全局配置加载
            **kwargs: 兼容原有接口的参数
        """
        # 加载配置
        if config is None:
            try:
                self.config = load_chunking_config_from_global()
                logger.info("从全局配置加载分块配置")
            except Exception as e:
                logger.warning(f"加载全局配置失败: {e}, 使用默认配置")
                self.config = RuntimeChunkingConfig()
        else:
            self.config = config

        # 为兼容性设置属性
        self.default_chunk_size = kwargs.get('default_chunk_size', self.config.target_chunk_size)
        self.default_overlap = kwargs.get('default_overlap', self.config.overlap_size)
        self.min_chunk_size = kwargs.get('min_chunk_size', self.config.min_chunk_size)
        self.max_chunk_size = kwargs.get('max_chunk_size', self.config.max_chunk_size)
        self.quality_threshold = kwargs.get('quality_threshold', self.config.quality_threshold)

        # 获取策略工厂和配置管理器
        self.factory = get_global_factory()
        self.config_manager = get_config_manager()

    async def initialize(self):
        """初始化处理器"""
        logger.info("初始化增强分块处理器")
        logger.info(f"默认模式: {self.config.mode.value}")
        logger.info(f"目标块大小: {self.config.target_chunk_size}")
        logger.info(f"重叠大小: {self.config.overlap_size}")

    @property
    def processor_name(self) -> str:
        """获取处理器名称"""
        return "EnhancedChunkingProcessor"

    @property
    def supported_strategies(self) -> List[str]:
        """获取支持的处理策略"""
        return self.factory.registry.list_strategies()

    async def validate_document(self, document: Document) -> bool:
        """验证文档是否可以处理"""
        if not document or not document.content:
            return False
        
        # 基本长度检查
        if len(document.content.strip()) < self.min_chunk_size:
            return False
        
        return True

    async def clean_content(self, content: str) -> str:
        """清理文档内容"""
        # 基础清理
        content = content.strip()
        
        # 移除多余空白行
        lines = content.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            is_empty = not line.strip()
            if not (is_empty and prev_empty):  # 避免连续空行
                cleaned_lines.append(line)
            prev_empty = is_empty
        
        return '\n'.join(cleaned_lines)

    async def create_chunks(self, document: Document, **kwargs) -> List[DocumentChunk]:
        """创建文档块（使用新的策略系统）"""
        try:
            # 清理内容
            cleaned_content = await self.clean_content(document.content)
            
            # 创建带清理内容的文档副本
            clean_document = Document(
                id=document.id,
                title=document.title,
                content=cleaned_content,
                content_type=document.content_type,
                metadata=document.metadata
            )

            # 分析文档特征
            doc_features = await self._analyze_document_features(clean_document)
            
            # 确定最佳配置
            contextual_config = await self._create_contextual_config(doc_features, **kwargs)
            
            # 创建分块上下文
            context = self._create_chunking_context(clean_document, contextual_config, doc_features)
            
            # 执行分块
            try:
                if contextual_config.mode == ChunkingMode.AUTO:
                    # 自动选择最佳策略
                    result = await self.factory.chunk_document(context)
                else:
                    # 使用指定策略
                    strategy_name = self._convert_mode_to_strategy_name(contextual_config.mode)
                    result = await self.factory.chunk_document(context, strategy_name)
                
                logger.info(
                    f"分块完成: {result.chunk_count}块, "
                    f"策略={result.strategy_used}, "
                    f"质量={result.quality_score:.3f}, "
                    f"时间={result.processing_time_ms:.1f}ms"
                )
                
                # 转换为DocumentChunk对象
                chunks = await self._convert_to_document_chunks(
                    result.chunks, clean_document, result
                )
                
                return chunks

            except ChunkingStrategyError as e:
                logger.error(f"策略分块失败: {e}")
                # 回退到简单分块
                return await self._fallback_chunking(clean_document, contextual_config)

        except Exception as e:
            logger.error(f"创建文档块失败 {document.id}: {e}")
            raise DocumentProcessorError(
                f"增强分块失败: {str(e)}",
                document_id=document.id,
                error_code="ENHANCED_CHUNKING_FAILED",
            )

    async def process_document(self, request: ProcessingRequest) -> ProcessingResult:
        """处理文档（增强版本）"""
        start_time = time.time()
        document = request.document

        try:
            # 验证文档
            if not await self.validate_document(document):
                raise DocumentProcessorError(
                    f"文档验证失败: {document.id}",
                    document_id=document.id,
                    error_code="VALIDATION_FAILED",
                )

            # 创建文档块
            chunks = await self.create_chunks(
                document,
                strategy=request.chunking_strategy,
                chunk_size=request.chunk_size,
                overlap=request.chunk_overlap,
            )

            # 生成嵌入向量（如果需要）
            if request.generate_embeddings:
                chunks = await self._generate_embeddings(chunks)

            # 计算处理时间
            processing_time = (time.time() - start_time) * 1000

            # 计算质量指标
            quality_metrics = await self._calculate_quality_metrics(chunks)

            # 创建处理结果
            result = ProcessingResult(
                document_id=document.id,
                status=ProcessingStatus.COMPLETED,
                chunks_created=len(chunks),
                chunks=chunks,
                processing_time_ms=processing_time,
                metadata={
                    "processor_name": self.processor_name,
                    "chunking_config": {
                        "mode": self.config.mode.value,
                        "target_size": self.config.target_chunk_size,
                        "overlap": self.config.overlap_size
                    },
                    "quality_metrics": quality_metrics,
                    "high_quality_chunks": sum(
                        1 for c in chunks 
                        if c.metadata.get("quality_score", 0) >= self.quality_threshold
                    ),
                    "enhanced_chunking": True
                },
            )

            logger.info(
                f"增强文档处理完成 {document.id}: {len(chunks)} 块, {processing_time:.2f}ms"
            )
            return result

        except DocumentProcessorError:
            raise
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"增强文档处理失败 {document.id}: {e}")

            return ProcessingResult(
                document_id=document.id,
                status=ProcessingStatus.FAILED,
                chunks_created=0,
                chunks=[],
                processing_time_ms=processing_time,
                error_message=str(e),
                metadata={"processor_name": self.processor_name, "enhanced_chunking": True},
            )

    async def _analyze_document_features(self, document: Document) -> Dict[str, Any]:
        """分析文档特征"""
        content = document.content

        # 基础统计
        words = content.split()
        lines = content.split('\n')
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        sentences = content.count('.') + content.count('!') + content.count('?') + \
                   content.count('。') + content.count('！') + content.count('？')

        features = {
            "length": len(content),
            "word_count": len(words),
            "paragraph_count": len(paragraphs),
            "sentence_count": max(sentences, 1),
            "avg_paragraph_length": sum(len(p) for p in paragraphs) / max(len(paragraphs), 1),
            "avg_sentence_length": len(content) / max(sentences, 1),
            "has_structure_markers": self._detect_structure_markers(content),
            "content_type": document.content_type.value if hasattr(document.content_type, 'value') else str(document.content_type),
            "language": self._detect_language(content),
            "complexity_score": self._calculate_complexity_score(content, words),
            "dialogue_ratio": self._calculate_dialogue_ratio(content),
            "technical_score": self._calculate_technical_score(content, words),
        }

        return features

    def _detect_structure_markers(self, content: str) -> bool:
        """检测结构化标记"""
        markers = [
            '#',        # Markdown标题
            '*',        # Markdown列表
            '-',        # Markdown列表
            '```',      # 代码块
            '<h',       # HTML标题
            '<p>',      # HTML段落
            '<div>',    # HTML div
            '1.',       # 数字列表
            '•',        # 项目符号
        ]
        
        return any(marker in content for marker in markers)

    def _detect_language(self, content: str) -> str:
        """简单语言检测"""
        import re
        
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        total_chars = len(content.replace(' ', '').replace('\n', ''))
        
        if total_chars == 0:
            return "unknown"
        
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.3:
            return "zh"
        elif chinese_ratio > 0.1:
            return "mixed"
        else:
            return "en"

    def _calculate_complexity_score(self, content: str, words: List[str]) -> float:
        """计算文档复杂度"""
        if not words:
            return 0.0
        
        # 基于词汇多样性和平均词长
        unique_words = len(set(w.lower() for w in words))
        vocab_diversity = unique_words / len(words)
        
        avg_word_length = sum(len(w) for w in words) / len(words)
        
        # 归一化到0-1范围
        complexity = (vocab_diversity * 0.7 + min(avg_word_length / 10, 1.0) * 0.3)
        
        return min(complexity, 1.0)

    def _calculate_dialogue_ratio(self, content: str) -> float:
        """计算对话内容比例"""
        dialogue_markers = ['"', "'", '"', '"', ''', ''']
        dialogue_chars = sum(content.count(marker) for marker in dialogue_markers)
        
        return min(dialogue_chars / max(len(content), 1), 1.0)

    def _calculate_technical_score(self, content: str, words: List[str]) -> float:
        """计算技术内容评分"""
        technical_terms = [
            'function', 'class', 'import', 'def', 'return', 'api', 'http', 'json',
            'database', 'server', 'client', 'algorithm', 'data', 'system',
            '函数', '类', '方法', '接口', '数据库', '算法', '系统'
        ]
        
        if not words:
            return 0.0
        
        tech_word_count = sum(1 for word in words if word.lower() in technical_terms)
        
        return min(tech_word_count / len(words) * 10, 1.0)

    async def _create_contextual_config(
        self, 
        doc_features: Dict[str, Any], 
        **kwargs
    ) -> RuntimeChunkingConfig:
        """创建上下文相关配置"""
        
        # 从kwargs获取用户指定的参数
        user_strategy = kwargs.get('strategy')
        user_chunk_size = kwargs.get('chunk_size')
        user_overlap = kwargs.get('overlap')

        # 复制基础配置
        config = RuntimeChunkingConfig(
            mode=self.config.mode,
            target_chunk_size=self.config.target_chunk_size,
            overlap_size=self.config.overlap_size,
            min_chunk_size=self.config.min_chunk_size,
            max_chunk_size=self.config.max_chunk_size,
            quality_threshold=self.config.quality_threshold,
            preserve_structure=self.config.preserve_structure,
            maintain_context=self.config.maintain_context,
            strategy_configs=self.config.strategy_configs.copy(),
            enable_auto_optimization=self.config.enable_auto_optimization,
            enable_quality_feedback=self.config.enable_quality_feedback
        )

        # 应用用户指定的参数
        if user_chunk_size:
            config.target_chunk_size = user_chunk_size
        if user_overlap:
            config.overlap_size = user_overlap
        if user_strategy:
            config.mode = self._convert_strategy_to_mode(user_strategy)

        # 使用配置管理器进行上下文自适应
        if config.enable_auto_optimization:
            try:
                config = self.config_manager.create_contextual_config(config, doc_features)
                logger.info(f"应用上下文自适应配置: mode={config.mode.value}, size={config.target_chunk_size}")
            except Exception as e:
                logger.warning(f"上下文自适应失败: {e}, 使用原配置")

        return config

    def _convert_strategy_to_mode(self, strategy) -> ChunkingMode:
        """转换ChunkingStrategy枚举到ChunkingMode"""
        mapping = {
            ChunkingStrategy.FIXED_SIZE: ChunkingMode.FIXED_SIZE,
            ChunkingStrategy.SEMANTIC: ChunkingMode.SEMANTIC,
            ChunkingStrategy.PARAGRAPH: ChunkingMode.PARAGRAPH,
            ChunkingStrategy.SENTENCE: ChunkingMode.SENTENCE,
        }
        
        if hasattr(strategy, 'value'):
            # 处理枚举值
            for old_enum, new_mode in mapping.items():
                if old_enum.value == strategy.value:
                    return new_mode
        elif isinstance(strategy, str):
            # 处理字符串
            for old_enum, new_mode in mapping.items():
                if old_enum.value == strategy:
                    return new_mode
        
        # 默认返回AUTO模式
        return ChunkingMode.AUTO

    def _convert_mode_to_strategy_name(self, mode: ChunkingMode) -> str:
        """转换ChunkingMode到策略名称"""
        mapping = {
            ChunkingMode.FIXED_SIZE: "fixed_size",
            ChunkingMode.SEMANTIC: "semantic", 
            ChunkingMode.PARAGRAPH: "paragraph",
            ChunkingMode.SENTENCE: "sentence",
            ChunkingMode.ADAPTIVE: "adaptive"
        }
        
        return mapping.get(mode, "fixed_size")

    def _create_chunking_context(
        self, 
        document: Document, 
        config: RuntimeChunkingConfig,
        features: Dict[str, Any]
    ) -> ChunkingContext:
        """创建分块上下文"""
        return ChunkingContext(
            document=document,
            document_length=features["length"],
            word_count=features["word_count"],
            paragraph_count=features["paragraph_count"],
            sentence_count=features["sentence_count"],
            avg_paragraph_length=features["avg_paragraph_length"],
            avg_sentence_length=features["avg_sentence_length"],
            has_structure_markers=features["has_structure_markers"],
            content_type=features["content_type"],
            language=features.get("language"),
            target_chunk_size=config.target_chunk_size,
            overlap_size=config.overlap_size,
            min_chunk_size=config.min_chunk_size,
            max_chunk_size=config.max_chunk_size,
            quality_threshold=config.quality_threshold,
            preserve_structure=config.preserve_structure,
            maintain_context=config.maintain_context
        )

    async def _convert_to_document_chunks(
        self, 
        strategy_chunks, 
        document: Document,
        result
    ) -> List[DocumentChunk]:
        """转换策略系统的块到DocumentChunk对象"""
        doc_chunks = []
        
        for i, chunk in enumerate(strategy_chunks):
            # 创建DocumentChunk对象
            doc_chunk = DocumentChunk(
                id=getattr(chunk, 'id', f"{document.id}_chunk_{i}"),
                document_id=document.id,
                content=chunk.content,
                chunk_index=getattr(chunk, 'chunk_index', i),
                start_char=getattr(chunk, 'start_char', 0),
                end_char=getattr(chunk, 'end_char', len(chunk.content)),
                strategy=self._map_strategy_name_to_enum(result.strategy_used),
                metadata={
                    **(getattr(chunk, 'metadata', {})),
                    "enhanced_chunking": True,
                    "strategy_used": result.strategy_used,
                    "processing_time_ms": result.processing_time_ms,
                    "overall_quality_score": result.quality_score,
                }
            )
            
            doc_chunks.append(doc_chunk)
        
        return doc_chunks

    def _map_strategy_name_to_enum(self, strategy_name: str) -> ChunkingStrategy:
        """映射策略名称到枚举"""
        mapping = {
            "fixed_size": ChunkingStrategy.FIXED_SIZE,
            "semantic": ChunkingStrategy.SEMANTIC,
            "paragraph": ChunkingStrategy.PARAGRAPH,
            "sentence": ChunkingStrategy.SENTENCE,
        }
        
        # 处理复合策略名（如"adaptive(paragraph)"）
        base_strategy = strategy_name.split('(')[0]
        if '(' in strategy_name and ')' in strategy_name:
            inner_strategy = strategy_name.split('(')[1].split(')')[0]
            return mapping.get(inner_strategy, ChunkingStrategy.FIXED_SIZE)
        
        return mapping.get(base_strategy, ChunkingStrategy.FIXED_SIZE)

    async def _fallback_chunking(
        self, 
        document: Document, 
        config: RuntimeChunkingConfig
    ) -> List[DocumentChunk]:
        """回退分块方法"""
        logger.warning("使用回退分块方法")
        
        content = document.content
        chunks = []
        chunk_size = config.target_chunk_size
        overlap = config.overlap_size
        
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = min(start + chunk_size, len(content))
            
            # 尝试在词边界分割
            if end < len(content) and not content[end].isspace():
                last_space = content.rfind(' ', start, end)
                if last_space > start + chunk_size * 0.7:
                    end = last_space
            
            chunk_content = content[start:end].strip()
            
            if len(chunk_content) >= config.min_chunk_size:
                chunk = DocumentChunk(
                    id=f"{document.id}_fallback_{chunk_index}",
                    document_id=document.id,
                    content=chunk_content,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    metadata={
                        "fallback_chunking": True,
                        "strategy_used": "fixed_size",  # 存储在元数据中
                        "quality_score": 0.5  # 回退分块质量较低
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
            
            start = max(start + 1, end - overlap)
        
        return chunks

    async def _generate_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """生成嵌入向量（占位符实现）"""
        # TODO: 集成实际的向量化模型
        for chunk in chunks:
            # 模拟向量生成
            import random
            chunk.embedding_vector = [random.random() for _ in range(1536)]
            chunk.metadata["has_embedding"] = True
        
        return chunks

    async def _calculate_quality_metrics(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """计算质量指标"""
        if not chunks:
            return {"overall_quality": 0.0}

        quality_scores = [chunk.metadata.get("quality_score", 0.5) for chunk in chunks]
        chunk_sizes = [len(chunk.content) for chunk in chunks]
        
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        size_variance = sum((size - avg_size) ** 2 for size in chunk_sizes) / len(chunk_sizes)

        return {
            "overall_quality": sum(quality_scores) / len(quality_scores),
            "high_quality_ratio": sum(
                1 for score in quality_scores if score >= self.quality_threshold
            ) / len(quality_scores),
            "avg_chunk_size": avg_size,
            "size_variance": size_variance ** 0.5,  # 标准差
            "total_chunks": len(chunks),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
        }