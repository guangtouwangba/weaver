"""
文档处理管道模块

为RAG系统提供端到端文档处理管道，协调各个组件完成：
- 文件加载和解析
- 文本分块处理
- 嵌入向量生成
- 向量存储和索引
- 处理状态跟踪
"""

from .base import (
    BatchProcessingResult,
    DocumentProcessingRequest,
    DocumentProcessingResult,
    IDocumentPipeline,
    PipelineConfig,
    PipelineError,
    PipelineStatus,
    ProcessingProgress,
    ProcessingStage,
    ProcessingStageResult,
)

__all__ = [
    "IDocumentPipeline",
    "PipelineConfig",
    "DocumentProcessingRequest",
    "DocumentProcessingResult",
    "ProcessingStageResult",
    "ProcessingProgress",
    "BatchProcessingResult",
    "PipelineError",
    "PipelineStatus",
    "ProcessingStage",
]
