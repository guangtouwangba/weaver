"""
RAG系统基础抽象接口

定义RAG管道中各个组件的抽象接口，实现模块化和可扩展的架构。
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4


class RAGComponentType(Enum):
    """RAG组件类型"""
    QUERY_PROCESSOR = "query_processor"
    RETRIEVER = "retriever"
    RERANKER = "reranker"
    CONTEXT_COMPRESSOR = "context_compressor"
    GENERATOR = "generator"
    EVALUATOR = "evaluator"


class QueryComplexity(Enum):
    """查询复杂度"""
    SIMPLE = "simple"           # 简单查询，单次检索即可
    MULTI_HOP = "multi_hop"     # 多跳查询，需要多次检索
    ANALYTICAL = "analytical"   # 分析性查询，需要推理
    COMPARATIVE = "comparative" # 比较性查询，需要对比多个来源


@dataclass
class QueryAnalysis:
    """查询分析结果"""
    original_query: str
    complexity: QueryComplexity
    intent: str
    entities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    rewritten_queries: List[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievedDocument:
    """检索到的文档"""
    id: str
    content: str
    score: float
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    rank: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class RAGContext:
    """RAG上下文信息"""
    query: str
    query_analysis: Optional[QueryAnalysis] = None
    retrieved_documents: List[RetrievedDocument] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    user_context: Dict[str, Any] = field(default_factory=dict)
    processing_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGResponse:
    """RAG响应结果"""
    query: str
    answer: str
    confidence: float
    retrieved_documents: List[RetrievedDocument] = field(default_factory=list)
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    citations: List[str] = field(default_factory=list)
    
    # 评估指标
    relevance_score: float = 0.0
    faithfulness_score: float = 0.0
    completeness_score: float = 0.0


class IRAGComponent(ABC):
    """RAG组件抽象基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.component_type = self._get_component_type()
        self.component_name = self.__class__.__name__
        self._initialized = False
    
    @abstractmethod
    def _get_component_type(self) -> RAGComponentType:
        """获取组件类型"""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化组件"""
        pass
    
    @abstractmethod
    async def process(self, context: RAGContext) -> RAGContext:
        """处理RAG上下文"""
        pass
    
    async def cleanup(self) -> None:
        """清理资源"""
        self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized


class IQueryProcessor(IRAGComponent):
    """查询处理器接口"""
    
    def _get_component_type(self) -> RAGComponentType:
        return RAGComponentType.QUERY_PROCESSOR
    
    @abstractmethod
    async def analyze_query(self, query: str) -> QueryAnalysis:
        """分析查询"""
        pass
    
    @abstractmethod
    async def rewrite_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """重写查询"""
        pass


class IRetriever(IRAGComponent):
    """检索器接口"""
    
    def _get_component_type(self) -> RAGComponentType:
        return RAGComponentType.RETRIEVER
    
    @abstractmethod
    async def retrieve(
        self, 
        query: str, 
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedDocument]:
        """检索相关文档"""
        pass
    
    @abstractmethod
    async def batch_retrieve(
        self, 
        queries: List[str], 
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[List[RetrievedDocument]]:
        """批量检索"""
        pass


class IReranker(IRAGComponent):
    """重排序器接口"""
    
    def _get_component_type(self) -> RAGComponentType:
        return RAGComponentType.RERANKER
    
    @abstractmethod
    async def rerank(
        self, 
        query: str, 
        documents: List[RetrievedDocument],
        top_k: Optional[int] = None
    ) -> List[RetrievedDocument]:
        """重新排序文档"""
        pass


class IContextCompressor(IRAGComponent):
    """上下文压缩器接口"""
    
    def _get_component_type(self) -> RAGComponentType:
        return RAGComponentType.CONTEXT_COMPRESSOR
    
    @abstractmethod
    async def compress(
        self, 
        query: str, 
        documents: List[RetrievedDocument],
        max_tokens: int = 4000
    ) -> List[RetrievedDocument]:
        """压缩上下文"""
        pass


class IResponseGenerator(IRAGComponent):
    """响应生成器接口"""
    
    def _get_component_type(self) -> RAGComponentType:
        return RAGComponentType.GENERATOR
    
    @abstractmethod
    async def generate(
        self, 
        query: str, 
        documents: List[RetrievedDocument],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """生成响应"""
        pass


class IRAGEvaluator(IRAGComponent):
    """RAG评估器接口"""
    
    def _get_component_type(self) -> RAGComponentType:
        return RAGComponentType.EVALUATOR
    
    @abstractmethod
    async def evaluate_retrieval(
        self, 
        query: str, 
        retrieved_docs: List[RetrievedDocument],
        ground_truth: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """评估检索质量"""
        pass
    
    @abstractmethod
    async def evaluate_generation(
        self, 
        query: str, 
        answer: str,
        retrieved_docs: List[RetrievedDocument],
        ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        """评估生成质量"""
        pass


class IRAGPipeline(ABC):
    """RAG管道接口"""
    
    @abstractmethod
    async def process(self, query: str, **kwargs) -> RAGResponse:
        """处理RAG请求"""
        pass
    
    @abstractmethod
    async def add_component(self, component: IRAGComponent) -> None:
        """添加组件"""
        pass
    
    @abstractmethod
    async def remove_component(self, component_type: RAGComponentType) -> None:
        """移除组件"""
        pass


class RAGPipelineError(Exception):
    """RAG管道错误"""
    
    def __init__(
        self, 
        message: str, 
        component_type: Optional[RAGComponentType] = None,
        error_code: Optional[str] = None
    ):
        self.component_type = component_type
        self.error_code = error_code
        super().__init__(message)


@dataclass
class RAGMetrics:
    """RAG性能指标"""
    total_processing_time_ms: float = 0.0
    query_processing_time_ms: float = 0.0
    retrieval_time_ms: float = 0.0
    reranking_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    
    # 质量指标
    retrieval_precision: float = 0.0
    retrieval_recall: float = 0.0
    answer_relevance: float = 0.0
    answer_faithfulness: float = 0.0
    answer_completeness: float = 0.0
    
    # 资源使用
    memory_usage_mb: float = 0.0
    tokens_used: int = 0
    api_calls: int = 0


class RAGStrategy(Enum):
    """RAG策略类型"""
    SIMPLE = "simple"                    # 简单RAG
    MULTI_HOP = "multi_hop"             # 多跳RAG
    ADAPTIVE = "adaptive"               # 自适应RAG
    CORRECTIVE = "corrective"           # 纠正性RAG
    SELF_REFLECTIVE = "self_reflective" # 自反思RAG
