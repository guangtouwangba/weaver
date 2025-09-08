"""
RAG配置管理

管理新的模块化RAG架构的配置。
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class RAGPipelineType(Enum):
    """RAG管道类型"""
    SIMPLE = "simple"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"
    MULTI_HOP = "multi_hop"


class RAGComponentType(Enum):
    """RAG组件类型"""
    QUERY_PROCESSOR = "query_processor"
    VECTOR_RETRIEVER = "vector_retriever"
    BM25_RETRIEVER = "bm25_retriever"
    HYBRID_RETRIEVER = "hybrid_retriever"
    RERANKER = "reranker"
    GENERATOR = "generator"


@dataclass
class QueryProcessorConfig:
    """查询处理器配置"""
    type: str = "enhanced"  # basic, enhanced
    enable_query_expansion: bool = True
    enable_entity_extraction: bool = True
    use_ai_analysis: bool = True
    max_rewritten_queries: int = 3
    ai_model: str = "gpt-3.5-turbo"


@dataclass
class VectorRetrieverConfig:
    """向量检索器配置"""
    default_top_k: int = 10
    default_score_threshold: float = 0.0
    collection_name: str = "documents"
    enable_summary_retrieval: bool = True
    summary_score_threshold: float = 0.75


@dataclass
class BM25RetrieverConfig:
    """BM25检索器配置"""
    enabled: bool = True
    k1: float = 1.5
    b: float = 0.75
    min_word_length: int = 2
    max_word_length: int = 20
    stop_words: Optional[list] = None


@dataclass
class HybridRetrieverConfig:
    """混合检索器配置"""
    fusion_method: str = "rrf"  # rrf, weighted, simple_merge
    rrf_k: int = 60
    weights: list = field(default_factory=lambda: [0.7, 0.3])  # vector, bm25
    enable_parallel: bool = True


@dataclass
class RerankerConfig:
    """重排序器配置"""
    enabled: bool = True
    type: str = "score_based"  # score_based, cross_encoder, hybrid
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    batch_size: int = 32
    score_weights: Dict[str, float] = field(default_factory=lambda: {
        "vector_score": 0.7,
        "bm25_score": 0.3
    })
    diversity_factor: float = 0.1
    enable_diversity: bool = True


@dataclass
class GeneratorConfig:
    """响应生成器配置"""
    type: str = "openai"  # openai, streaming, template
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000
    temperature: float = 0.3
    max_context_tokens: int = 4000
    enable_streaming: bool = False
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None


@dataclass
class RAGPipelineConfig:
    """RAG管道配置"""
    pipeline_type: RAGPipelineType = RAGPipelineType.ADAPTIVE
    pipeline_name: str = "default"
    
    # 组件配置
    query_processor: QueryProcessorConfig = field(default_factory=QueryProcessorConfig)
    vector_retriever: VectorRetrieverConfig = field(default_factory=VectorRetrieverConfig)
    bm25_retriever: BM25RetrieverConfig = field(default_factory=BM25RetrieverConfig)
    hybrid_retriever: HybridRetrieverConfig = field(default_factory=HybridRetrieverConfig)
    reranker: RerankerConfig = field(default_factory=RerankerConfig)
    generator: GeneratorConfig = field(default_factory=GeneratorConfig)
    
    # 全局配置
    enable_routing: bool = True
    enable_caching: bool = True
    enable_monitoring: bool = True
    
    # 性能配置
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "pipeline_type": self.pipeline_type.value,
            "pipeline_name": self.pipeline_name,
            "query_processor": {
                "type": self.query_processor.type,
                "enable_query_expansion": self.query_processor.enable_query_expansion,
                "enable_entity_extraction": self.query_processor.enable_entity_extraction,
                "use_ai_analysis": self.query_processor.use_ai_analysis,
                "max_rewritten_queries": self.query_processor.max_rewritten_queries,
                "ai_model": self.query_processor.ai_model
            },
            "vector_retriever": {
                "default_top_k": self.vector_retriever.default_top_k,
                "default_score_threshold": self.vector_retriever.default_score_threshold,
                "collection_name": self.vector_retriever.collection_name,
                "enable_summary_retrieval": self.vector_retriever.enable_summary_retrieval,
                "summary_score_threshold": self.vector_retriever.summary_score_threshold
            },
            "bm25_retriever": {
                "enabled": self.bm25_retriever.enabled,
                "k1": self.bm25_retriever.k1,
                "b": self.bm25_retriever.b,
                "min_word_length": self.bm25_retriever.min_word_length,
                "max_word_length": self.bm25_retriever.max_word_length,
                "stop_words": self.bm25_retriever.stop_words
            },
            "hybrid_retriever": {
                "fusion_method": self.hybrid_retriever.fusion_method,
                "rrf_k": self.hybrid_retriever.rrf_k,
                "weights": self.hybrid_retriever.weights,
                "enable_parallel": self.hybrid_retriever.enable_parallel
            },
            "reranker": {
                "enabled": self.reranker.enabled,
                "type": self.reranker.type,
                "model_name": self.reranker.model_name,
                "batch_size": self.reranker.batch_size,
                "score_weights": self.reranker.score_weights,
                "diversity_factor": self.reranker.diversity_factor,
                "enable_diversity": self.reranker.enable_diversity
            },
            "generator": {
                "type": self.generator.type,
                "model": self.generator.model,
                "max_tokens": self.generator.max_tokens,
                "temperature": self.generator.temperature,
                "max_context_tokens": self.generator.max_context_tokens,
                "enable_streaming": self.generator.enable_streaming,
                "system_prompt": self.generator.system_prompt,
                "user_prompt_template": self.generator.user_prompt_template
            },
            "enable_routing": self.enable_routing,
            "enable_caching": self.enable_caching,
            "enable_monitoring": self.enable_monitoring,
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_timeout": self.request_timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RAGPipelineConfig':
        """从字典创建配置"""
        config = cls()
        
        # 更新管道类型
        if "pipeline_type" in data:
            config.pipeline_type = RAGPipelineType(data["pipeline_type"])
        
        if "pipeline_name" in data:
            config.pipeline_name = data["pipeline_name"]
        
        # 更新组件配置
        if "query_processor" in data:
            qp_data = data["query_processor"]
            config.query_processor = QueryProcessorConfig(
                type=qp_data.get("type", "enhanced"),
                enable_query_expansion=qp_data.get("enable_query_expansion", True),
                enable_entity_extraction=qp_data.get("enable_entity_extraction", True),
                use_ai_analysis=qp_data.get("use_ai_analysis", True),
                max_rewritten_queries=qp_data.get("max_rewritten_queries", 3),
                ai_model=qp_data.get("ai_model", "gpt-3.5-turbo")
            )
        
        if "vector_retriever" in data:
            vr_data = data["vector_retriever"]
            config.vector_retriever = VectorRetrieverConfig(
                default_top_k=vr_data.get("default_top_k", 10),
                default_score_threshold=vr_data.get("default_score_threshold", 0.0),
                collection_name=vr_data.get("collection_name", "documents"),
                enable_summary_retrieval=vr_data.get("enable_summary_retrieval", True),
                summary_score_threshold=vr_data.get("summary_score_threshold", 0.75)
            )
        
        if "bm25_retriever" in data:
            bm25_data = data["bm25_retriever"]
            config.bm25_retriever = BM25RetrieverConfig(
                enabled=bm25_data.get("enabled", True),
                k1=bm25_data.get("k1", 1.5),
                b=bm25_data.get("b", 0.75),
                min_word_length=bm25_data.get("min_word_length", 2),
                max_word_length=bm25_data.get("max_word_length", 20),
                stop_words=bm25_data.get("stop_words")
            )
        
        if "hybrid_retriever" in data:
            hr_data = data["hybrid_retriever"]
            config.hybrid_retriever = HybridRetrieverConfig(
                fusion_method=hr_data.get("fusion_method", "rrf"),
                rrf_k=hr_data.get("rrf_k", 60),
                weights=hr_data.get("weights", [0.7, 0.3]),
                enable_parallel=hr_data.get("enable_parallel", True)
            )
        
        if "reranker" in data:
            rr_data = data["reranker"]
            config.reranker = RerankerConfig(
                enabled=rr_data.get("enabled", True),
                type=rr_data.get("type", "score_based"),
                model_name=rr_data.get("model_name", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
                batch_size=rr_data.get("batch_size", 32),
                score_weights=rr_data.get("score_weights", {"vector_score": 0.7, "bm25_score": 0.3}),
                diversity_factor=rr_data.get("diversity_factor", 0.1),
                enable_diversity=rr_data.get("enable_diversity", True)
            )
        
        if "generator" in data:
            gen_data = data["generator"]
            config.generator = GeneratorConfig(
                type=gen_data.get("type", "openai"),
                model=gen_data.get("model", "gpt-3.5-turbo"),
                max_tokens=gen_data.get("max_tokens", 1000),
                temperature=gen_data.get("temperature", 0.3),
                max_context_tokens=gen_data.get("max_context_tokens", 4000),
                enable_streaming=gen_data.get("enable_streaming", False),
                system_prompt=gen_data.get("system_prompt"),
                user_prompt_template=gen_data.get("user_prompt_template")
            )
        
        # 更新全局配置
        config.enable_routing = data.get("enable_routing", True)
        config.enable_caching = data.get("enable_caching", True)
        config.enable_monitoring = data.get("enable_monitoring", True)
        config.max_concurrent_requests = data.get("max_concurrent_requests", 10)
        config.request_timeout = data.get("request_timeout", 30)
        
        return config


class RAGConfigManager:
    """RAG配置管理器"""
    
    def __init__(self):
        self._configs: Dict[str, RAGPipelineConfig] = {}
        self._default_config_name = "default"
        
        # 加载预设配置
        self._load_preset_configs()
    
    def _load_preset_configs(self):
        """加载预设配置"""
        # 简单RAG配置
        simple_config = RAGPipelineConfig(
            pipeline_type=RAGPipelineType.SIMPLE,
            pipeline_name="simple"
        )
        simple_config.bm25_retriever.enabled = False
        simple_config.reranker.enabled = False
        simple_config.query_processor.use_ai_analysis = False
        
        # 混合RAG配置
        hybrid_config = RAGPipelineConfig(
            pipeline_type=RAGPipelineType.HYBRID,
            pipeline_name="hybrid"
        )
        hybrid_config.bm25_retriever.enabled = True
        hybrid_config.reranker.enabled = True
        hybrid_config.reranker.type = "cross_encoder"
        
        # 自适应RAG配置
        adaptive_config = RAGPipelineConfig(
            pipeline_type=RAGPipelineType.ADAPTIVE,
            pipeline_name="adaptive"
        )
        adaptive_config.bm25_retriever.enabled = True
        adaptive_config.reranker.enabled = True
        adaptive_config.reranker.type = "hybrid"
        adaptive_config.generator.model = "gpt-4"
        adaptive_config.generator.enable_streaming = True
        
        # 多跳RAG配置
        multi_hop_config = RAGPipelineConfig(
            pipeline_type=RAGPipelineType.MULTI_HOP,
            pipeline_name="multi_hop"
        )
        multi_hop_config.query_processor.max_rewritten_queries = 5
        multi_hop_config.vector_retriever.default_top_k = 15
        
        # 注册配置
        self._configs["simple"] = simple_config
        self._configs["hybrid"] = hybrid_config
        self._configs["adaptive"] = adaptive_config
        self._configs["multi_hop"] = multi_hop_config
        self._configs[self._default_config_name] = adaptive_config
    
    def get_config(self, name: str = None) -> RAGPipelineConfig:
        """获取配置"""
        if name is None:
            name = self._default_config_name
        
        if name not in self._configs:
            raise ValueError(f"配置 '{name}' 不存在")
        
        return self._configs[name]
    
    def set_config(self, name: str, config: RAGPipelineConfig):
        """设置配置"""
        self._configs[name] = config
    
    def list_configs(self) -> List[str]:
        """列出所有配置名称"""
        return list(self._configs.keys())
    
    def get_config_dict(self, name: str = None) -> Dict[str, Any]:
        """获取配置字典"""
        config = self.get_config(name)
        return config.to_dict()
    
    def load_from_env(self) -> RAGPipelineConfig:
        """从环境变量加载配置"""
        config = RAGPipelineConfig()
        
        # 管道类型
        pipeline_type = os.getenv("RAG_PIPELINE_TYPE", "adaptive")
        try:
            config.pipeline_type = RAGPipelineType(pipeline_type)
        except ValueError:
            config.pipeline_type = RAGPipelineType.ADAPTIVE
        
        # 查询处理器
        config.query_processor.use_ai_analysis = os.getenv("RAG_USE_AI_ANALYSIS", "true").lower() == "true"
        config.query_processor.ai_model = os.getenv("RAG_AI_MODEL", "gpt-3.5-turbo")
        
        # 向量检索器
        config.vector_retriever.default_top_k = int(os.getenv("RAG_TOP_K", "10"))
        config.vector_retriever.collection_name = os.getenv("RAG_COLLECTION_NAME", "documents")
        
        # BM25检索器
        config.bm25_retriever.enabled = os.getenv("RAG_ENABLE_BM25", "true").lower() == "true"
        config.bm25_retriever.k1 = float(os.getenv("RAG_BM25_K1", "1.5"))
        config.bm25_retriever.b = float(os.getenv("RAG_BM25_B", "0.75"))
        
        # 重排序器
        config.reranker.enabled = os.getenv("RAG_ENABLE_RERANKING", "true").lower() == "true"
        config.reranker.type = os.getenv("RAG_RERANKER_TYPE", "score_based")
        
        # 生成器
        config.generator.model = os.getenv("RAG_GENERATOR_MODEL", "gpt-3.5-turbo")
        config.generator.max_tokens = int(os.getenv("RAG_MAX_TOKENS", "1000"))
        config.generator.temperature = float(os.getenv("RAG_TEMPERATURE", "0.3"))
        config.generator.enable_streaming = os.getenv("RAG_ENABLE_STREAMING", "false").lower() == "true"
        
        # 全局配置
        config.enable_routing = os.getenv("RAG_ENABLE_ROUTING", "true").lower() == "true"
        config.enable_caching = os.getenv("RAG_ENABLE_CACHING", "true").lower() == "true"
        config.enable_monitoring = os.getenv("RAG_ENABLE_MONITORING", "true").lower() == "true"
        
        return config


# 全局配置管理器实例
rag_config_manager = RAGConfigManager()


def get_rag_config(name: str = None) -> RAGPipelineConfig:
    """获取RAG配置"""
    return rag_config_manager.get_config(name)


def get_rag_config_dict(name: str = None) -> Dict[str, Any]:
    """获取RAG配置字典"""
    return rag_config_manager.get_config_dict(name)
