"""
RAG (Retrieval-Augmented Generation) 模块

提供模块化、可扩展的RAG系统实现，支持多种检索策略和生成模式。
"""

from .base import (
    # 枚举类型
    RAGComponentType,
    QueryComplexity,
    RAGStrategy,
    
    # 数据类
    QueryAnalysis,
    RetrievedDocument,
    RAGContext,
    RAGResponse,
    RAGMetrics,
    
    # 抽象接口
    IRAGComponent,
    IQueryProcessor,
    IRetriever,
    IReranker,
    IContextCompressor,
    IResponseGenerator,
    IRAGEvaluator,
    IRAGPipeline,
    
    # 异常类
    RAGPipelineError,
)

__all__ = [
    # 枚举类型
    "RAGComponentType",
    "QueryComplexity", 
    "RAGStrategy",
    
    # 数据类
    "QueryAnalysis",
    "RetrievedDocument",
    "RAGContext",
    "RAGResponse",
    "RAGMetrics",
    
    # 抽象接口
    "IRAGComponent",
    "IQueryProcessor",
    "IRetriever",
    "IReranker",
    "IContextCompressor",
    "IResponseGenerator",
    "IRAGEvaluator",
    "IRAGPipeline",
    
    # 异常类
    "RAGPipelineError",
]
