"""
Chunking策略接口定义

定义标准化的分块策略接口，支持策略的统一管理和动态选择。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from enum import Enum

from modules.schemas import Document
from modules.models import DocumentChunk, ChunkingStrategy


@dataclass
class ChunkingContext:
    """分块上下文，包含文档特征和配置信息"""
    
    # 文档基本信息
    document: Document
    
    # 文档特征分析
    document_length: int
    word_count: int
    paragraph_count: int
    sentence_count: int
    avg_paragraph_length: float
    avg_sentence_length: float
    has_structure_markers: bool
    content_type: str
    language: Optional[str] = None
    
    # 分块参数配置
    target_chunk_size: int = 1000
    overlap_size: int = 200
    min_chunk_size: int = 50
    max_chunk_size: int = 4000
    
    # 质量要求
    quality_threshold: float = 0.7
    preserve_structure: bool = True
    maintain_context: bool = True
    
    # 其他配置
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChunkingResult:
    """分块结果，包含块列表和元数据"""
    
    chunks: List[DocumentChunk]
    strategy_used: str
    processing_time_ms: float
    
    # 质量指标
    avg_chunk_size: float
    size_variance: float
    quality_score: float
    coverage_ratio: float
    
    # 策略特定元数据
    strategy_metadata: Dict[str, Any]
    
    @property
    def chunk_count(self) -> int:
        """块数量"""
        return len(self.chunks)
    
    @property
    def high_quality_chunks(self) -> int:
        """高质量块数量"""
        return sum(1 for chunk in self.chunks 
                  if chunk.metadata.get("quality_score", 0) >= 0.8)


class StrategyPriority(Enum):
    """策略优先级"""
    LOWEST = 1
    LOW = 2
    MEDIUM = 3  
    HIGH = 4
    HIGHEST = 5


@runtime_checkable
class IChunkingStrategy(Protocol):
    """分块策略接口协议"""
    
    @property
    def name(self) -> str:
        """策略名称"""
        ...
    
    @property
    def priority(self) -> StrategyPriority:
        """策略优先级，用于自动选择时的排序"""
        ...
    
    @property
    def supported_content_types(self) -> List[str]:
        """支持的内容类型"""
        ...
    
    async def can_handle(self, context: ChunkingContext) -> bool:
        """判断是否能处理给定的分块上下文"""
        ...
    
    async def estimate_performance(self, context: ChunkingContext) -> Dict[str, float]:
        """估算性能指标（质量、速度等）"""
        ...
    
    async def chunk_document(self, context: ChunkingContext) -> ChunkingResult:
        """执行文档分块"""
        ...
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        ...
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置有效性"""
        ...


class BaseChunkingStrategy(ABC):
    """分块策略基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self.get_default_config()
        self._validate_and_setup_config()
    
    def _validate_and_setup_config(self):
        """验证和设置配置"""
        if not self.validate_config(self.config):
            raise ValueError(f"Invalid configuration for strategy {self.name}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> StrategyPriority:
        """策略优先级"""
        pass
    
    @property
    @abstractmethod
    def supported_content_types(self) -> List[str]:
        """支持的内容类型"""
        pass
    
    async def can_handle(self, context: ChunkingContext) -> bool:
        """默认的处理能力判断"""
        # 检查内容类型
        if context.content_type not in self.supported_content_types:
            return False
        
        # 检查文档长度
        min_length = self.config.get("min_document_length", 100)
        max_length = self.config.get("max_document_length", 1000000)
        
        return min_length <= context.document_length <= max_length
    
    async def estimate_performance(self, context: ChunkingContext) -> Dict[str, float]:
        """默认的性能估算"""
        return {
            "quality_score": 0.7,
            "processing_speed": 1.0,
            "memory_usage": 1.0,
            "suitability": 0.7
        }
    
    @abstractmethod
    async def chunk_document(self, context: ChunkingContext) -> ChunkingResult:
        """执行文档分块"""
        pass
    
    def get_default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "min_document_length": 100,
            "max_document_length": 1000000,
            "preserve_formatting": True,
            "enable_optimization": True
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        required_keys = ["min_document_length", "max_document_length"]
        return all(key in config for key in required_keys)
    
    def _create_chunk(
        self, 
        context: ChunkingContext,
        content: str,
        chunk_index: int,
        start_pos: int,
        end_pos: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentChunk:
        """创建文档块的辅助方法"""
        chunk_metadata = {
            "strategy": self.name,
            "chunk_size": len(content),
            "original_start": start_pos,
            "original_end": end_pos,
            **(metadata or {})
        }
        
        return DocumentChunk(
            id=f"{context.document.id}_chunk_{chunk_index}",
            document_id=context.document.id,
            content=content.strip(),
            chunk_index=chunk_index,
            start_char=start_pos,
            end_char=end_pos,
            metadata=chunk_metadata
        )
    
    def _calculate_quality_score(self, chunk: DocumentChunk) -> float:
        """计算块质量分数"""
        content = chunk.content
        score = 1.0
        
        # 长度评分
        length = len(content)
        if length < 50:
            score *= 0.5
        elif length > 4000:
            score *= 0.7
        elif 500 <= length <= 2000:
            score *= 1.0  # 理想长度
        
        # 完整性评分
        if content.strip().endswith(('.', '!', '?', '。', '！', '？')):
            score *= 1.1  # 完整句子
        elif content.strip().endswith(','):
            score *= 0.9  # 不完整
        
        # 内容密度评分
        words = content.split()
        if words and 3 <= sum(len(w) for w in words) / len(words) <= 8:
            score *= 1.0
        else:
            score *= 0.9
        
        return min(max(score, 0.0), 1.0)


class ChunkingStrategyError(Exception):
    """分块策略错误"""
    
    def __init__(
        self, 
        message: str, 
        strategy_name: Optional[str] = None,
        document_id: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        self.strategy_name = strategy_name
        self.document_id = document_id
        self.error_code = error_code
        super().__init__(message)