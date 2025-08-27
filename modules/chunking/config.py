"""
Chunking配置系统

提供策略选择、参数调优和智能配置的统一管理。
基于全局配置系统构建。
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

# 从全局配置导入基础配置类
from config.settings import (
    ChunkingConfig as GlobalChunkingConfig,
    ChunkingMode,
    DocumentType,
    ChunkingStrategyConfig,
    AppConfig
)

logger = logging.getLogger(__name__)


@dataclass 
class ContextualConfig:
    """上下文相关配置"""
    
    # 文档特征阈值
    min_paragraphs_for_paragraph_strategy: int = 3
    min_sentences_for_sentence_strategy: int = 5
    min_length_for_semantic_strategy: int = 2000
    
    # 内容类型检测阈值
    dialogue_ratio_threshold: float = 0.3
    technical_score_threshold: float = 0.6
    structure_score_threshold: float = 0.5
    
    # 语言检测配置
    chinese_char_threshold: float = 0.3
    mixed_language_threshold: float = 0.1
    
    # 自适应策略权重
    adaptive_weights: Dict[str, float] = field(default_factory=lambda: {
        "quality": 0.6,
        "speed": 0.2,
        "memory": 0.1,
        "suitability": 0.1
    })


@dataclass
class RuntimeChunkingConfig:
    """运行时分块配置"""
    
    # 基本配置
    mode: ChunkingMode = ChunkingMode.AUTO
    target_chunk_size: int = 1000
    overlap_size: int = 200
    min_chunk_size: int = 50
    max_chunk_size: int = 4000
    
    # 质量配置
    quality_threshold: float = 0.7
    preserve_structure: bool = True
    maintain_context: bool = True
    
    # 策略特定配置
    strategy_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 文档类型提示
    document_type: Optional[DocumentType] = None
    content_language: Optional[str] = None
    
    # 高级配置
    enable_auto_optimization: bool = True
    enable_quality_feedback: bool = True
    enable_performance_monitoring: bool = True
    
    # 混合策略配置
    hybrid_strategies: List[str] = field(default_factory=list)
    hybrid_weights: Dict[str, float] = field(default_factory=dict)
    
    # 性能配置
    max_processing_time_ms: Optional[int] = None
    memory_limit_mb: Optional[int] = None
    parallel_processing: bool = False
    
    @classmethod
    def from_global_config(cls, global_config: GlobalChunkingConfig) -> "RuntimeChunkingConfig":
        """从全局配置创建运行时配置"""
        strategy_configs = {}
        for name, strategy_config in global_config.strategy_configs.items():
            strategy_configs[name] = strategy_config.config
        
        return cls(
            mode=global_config.default_mode,
            target_chunk_size=global_config.target_chunk_size,
            overlap_size=global_config.overlap_size,
            min_chunk_size=global_config.min_chunk_size,
            max_chunk_size=global_config.max_chunk_size,
            quality_threshold=global_config.quality_threshold,
            preserve_structure=global_config.preserve_structure,
            maintain_context=global_config.maintain_context,
            strategy_configs=strategy_configs,
            enable_auto_optimization=global_config.enable_auto_optimization,
            enable_quality_feedback=global_config.enable_quality_feedback,
            enable_performance_monitoring=global_config.enable_performance_monitoring,
            hybrid_strategies=global_config.hybrid_strategies,
            hybrid_weights=global_config.hybrid_weights,
            max_processing_time_ms=global_config.max_processing_time_ms,
            memory_limit_mb=global_config.memory_limit_mb,
            parallel_processing=global_config.parallel_processing
        )


class ChunkingConfigManager:
    """分块配置管理器"""
    
    def __init__(self, global_config: Optional[GlobalChunkingConfig] = None):
        self._global_config = global_config
        self._presets: Dict[str, RuntimeChunkingConfig] = {}
        self._contextual_config = ContextualConfig()
        self._setup_default_presets()
    
    def set_global_config(self, global_config: GlobalChunkingConfig):
        """设置全局配置"""
        self._global_config = global_config
    
    def get_global_config(self) -> Optional[GlobalChunkingConfig]:
        """获取全局配置"""
        return self._global_config
    
    def _setup_default_presets(self):
        """设置默认预设"""
        
        # 通用预设
        self._presets["default"] = RuntimeChunkingConfig(
            mode=ChunkingMode.AUTO,
            target_chunk_size=1000,
            overlap_size=200
        )
        
        # 学术文档预设
        self._presets["academic"] = RuntimeChunkingConfig(
            mode=ChunkingMode.PARAGRAPH,
            document_type=DocumentType.ACADEMIC,
            target_chunk_size=1500,
            overlap_size=300,
            preserve_structure=True,
            strategy_configs={
                "paragraph": {
                    "merge_short_paragraphs": True,
                    "handle_citations": True,
                    "preserve_headers": True
                },
                "semantic": {
                    "similarity_threshold": 0.4,
                    "academic_boost": True
                }
            }
        )
        
        # 技术文档预设
        self._presets["technical"] = RuntimeChunkingConfig(
            mode=ChunkingMode.ADAPTIVE,
            document_type=DocumentType.TECHNICAL,
            target_chunk_size=1200,
            overlap_size=150,
            strategy_configs={
                "semantic": {
                    "technical_terms_boost": True,
                    "code_block_preservation": True
                },
                "paragraph": {
                    "handle_code_blocks": True,
                    "preserve_formatting": True
                }
            }
        )
        
        # 对话文档预设
        self._presets["dialogue"] = RuntimeChunkingConfig(
            mode=ChunkingMode.SENTENCE,
            document_type=DocumentType.DIALOGUE,
            target_chunk_size=800,
            overlap_size=100,
            strategy_configs={
                "sentence": {
                    "preserve_dialogue": True,
                    "merge_short_sentences": False,
                    "context_window": 3
                }
            }
        )
        
        # 长文档预设
        self._presets["long_document"] = RuntimeChunkingConfig(
            mode=ChunkingMode.HYBRID,
            target_chunk_size=2000,
            overlap_size=400,
            hybrid_strategies=["paragraph", "semantic"],
            hybrid_weights={"paragraph": 0.7, "semantic": 0.3},
            parallel_processing=True
        )
        
        # 快速处理预设
        self._presets["fast"] = RuntimeChunkingConfig(
            mode=ChunkingMode.FIXED_SIZE,
            target_chunk_size=1000,
            overlap_size=100,
            enable_auto_optimization=False,
            strategy_configs={
                "fixed_size": {
                    "split_on_word_boundary": True,
                    "word_boundary_threshold": 0.9
                }
            }
        )
        
        # 高质量预设
        self._presets["high_quality"] = RuntimeChunkingConfig(
            mode=ChunkingMode.SEMANTIC,
            target_chunk_size=1500,
            overlap_size=300,
            quality_threshold=0.9,
            enable_quality_feedback=True,
            strategy_configs={
                "semantic": {
                    "similarity_threshold": 0.25,
                    "quality_optimization": True,
                    "multi_pass_refinement": True
                }
            }
        )
    
    def get_preset(self, preset_name: str) -> Optional[RuntimeChunkingConfig]:
        """获取预设配置"""
        return self._presets.get(preset_name)
    
    def list_presets(self) -> List[str]:
        """列出所有预设"""
        return list(self._presets.keys())
    
    def register_preset(self, name: str, config: RuntimeChunkingConfig):
        """注册新的预设配置"""
        self._presets[name] = config
        logger.info(f"Registered chunking preset: {name}")
    
    def create_contextual_config(
        self,
        base_config: RuntimeChunkingConfig,
        document_features: Dict[str, Any]
    ) -> RuntimeChunkingConfig:
        """基于文档特征创建上下文相关的配置"""
        
        # 复制基础配置
        contextual_config = RuntimeChunkingConfig(
            mode=base_config.mode,
            target_chunk_size=base_config.target_chunk_size,
            overlap_size=base_config.overlap_size,
            min_chunk_size=base_config.min_chunk_size,
            max_chunk_size=base_config.max_chunk_size,
            quality_threshold=base_config.quality_threshold,
            preserve_structure=base_config.preserve_structure,
            maintain_context=base_config.maintain_context,
            strategy_configs=base_config.strategy_configs.copy(),
            document_type=base_config.document_type,
            content_language=base_config.content_language,
            enable_auto_optimization=base_config.enable_auto_optimization,
            enable_quality_feedback=base_config.enable_quality_feedback,
            enable_performance_monitoring=base_config.enable_performance_monitoring,
            hybrid_strategies=base_config.hybrid_strategies.copy(),
            hybrid_weights=base_config.hybrid_weights.copy(),
            max_processing_time_ms=base_config.max_processing_time_ms,
            memory_limit_mb=base_config.memory_limit_mb,
            parallel_processing=base_config.parallel_processing
        )
        
        # 根据文档特征调整配置
        self._adjust_for_document_features(contextual_config, document_features)
        
        # 自动模式下的策略选择
        if contextual_config.mode == ChunkingMode.AUTO:
            recommended_mode = self._recommend_strategy(document_features)
            contextual_config.mode = recommended_mode
        
        return contextual_config
    
    def _adjust_for_document_features(
        self, 
        config: RuntimeChunkingConfig, 
        features: Dict[str, Any]
    ):
        """根据文档特征调整配置"""
        
        # 根据文档长度调整块大小
        doc_length = features.get("length", 0)
        if doc_length < 2000:
            config.target_chunk_size = min(config.target_chunk_size, 600)
        elif doc_length > 50000:
            config.target_chunk_size = max(config.target_chunk_size, 1500)
        
        # 根据平均段落长度调整重叠
        avg_para_length = features.get("avg_paragraph_length", 0)
        if avg_para_length > 1000:
            config.overlap_size = max(config.overlap_size, 300)
        elif avg_para_length < 200:
            config.overlap_size = min(config.overlap_size, 100)
        
        # 根据结构化程度调整策略配置
        structure_score = features.get("structure_score", 0)
        if structure_score > self._contextual_config.structure_score_threshold:
            config.preserve_structure = True
            
            # 增强段落策略配置
            if "paragraph" not in config.strategy_configs:
                config.strategy_configs["paragraph"] = {}
            config.strategy_configs["paragraph"]["preserve_headers"] = True
        
        # 根据对话内容调整
        dialogue_ratio = features.get("dialogue_ratio", 0)
        if dialogue_ratio > self._contextual_config.dialogue_ratio_threshold:
            if "sentence" not in config.strategy_configs:
                config.strategy_configs["sentence"] = {}
            config.strategy_configs["sentence"]["preserve_dialogue"] = True
            config.strategy_configs["sentence"]["merge_short_sentences"] = False
        
        # 根据技术内容调整
        technical_score = features.get("technical_score", 0)
        if technical_score > self._contextual_config.technical_score_threshold:
            config.preserve_structure = True
            
            if "paragraph" not in config.strategy_configs:
                config.strategy_configs["paragraph"] = {}
            config.strategy_configs["paragraph"]["handle_code_blocks"] = True
        
        # 根据语言调整
        language = features.get("language", "en")
        config.content_language = language
        
        if language == "zh":
            # 中文文档调整
            if "sentence" not in config.strategy_configs:
                config.strategy_configs["sentence"] = {}
            config.strategy_configs["sentence"]["sentence_endings"] = ['。', '！', '？', '；']
        elif language == "mixed":
            # 混合语言调整
            if "semantic" not in config.strategy_configs:
                config.strategy_configs["semantic"] = {}
            config.strategy_configs["semantic"]["multilingual_support"] = True
    
    def _recommend_strategy(self, features: Dict[str, Any]) -> ChunkingMode:
        """根据文档特征推荐策略"""
        
        # 基于特征评分的策略推荐
        scores = {
            ChunkingMode.FIXED_SIZE: 0.3,
            ChunkingMode.PARAGRAPH: 0.4,
            ChunkingMode.SENTENCE: 0.3,
            ChunkingMode.SEMANTIC: 0.2,
            ChunkingMode.ADAPTIVE: 0.5
        }
        
        # 根据结构化程度
        structure_score = features.get("structure_score", 0)
        if structure_score > 0.7:
            scores[ChunkingMode.PARAGRAPH] += 0.3
            scores[ChunkingMode.ADAPTIVE] += 0.2
        elif structure_score < 0.3:
            scores[ChunkingMode.FIXED_SIZE] += 0.3
        
        # 根据对话内容
        dialogue_ratio = features.get("dialogue_ratio", 0)
        if dialogue_ratio > 0.3:
            scores[ChunkingMode.SENTENCE] += 0.4
            scores[ChunkingMode.PARAGRAPH] -= 0.2
        
        # 根据技术内容
        technical_score = features.get("technical_score", 0)
        if technical_score > 0.6:
            scores[ChunkingMode.SEMANTIC] += 0.3
            scores[ChunkingMode.ADAPTIVE] += 0.2
        
        # 根据复杂度
        complexity_score = features.get("complexity_score", 0)
        if complexity_score > 0.8:
            scores[ChunkingMode.ADAPTIVE] += 0.3
            scores[ChunkingMode.SEMANTIC] += 0.2
        elif complexity_score < 0.3:
            scores[ChunkingMode.FIXED_SIZE] += 0.2
        
        # 根据文档长度
        doc_length = features.get("length", 0)
        if doc_length > 20000:
            scores[ChunkingMode.ADAPTIVE] += 0.2
            scores[ChunkingMode.SEMANTIC] -= 0.1  # 大文档语义分析慢
        elif doc_length < 2000:
            scores[ChunkingMode.SENTENCE] += 0.2
        
        # 选择得分最高的策略
        best_strategy = max(scores, key=scores.get)
        
        logger.info(f"Recommended strategy: {best_strategy.value} (score: {scores[best_strategy]:.3f})")
        return best_strategy
    
    def optimize_config(
        self, 
        config: RuntimeChunkingConfig, 
        performance_feedback: Dict[str, Any]
    ) -> RuntimeChunkingConfig:
        """基于性能反馈优化配置"""
        
        optimized = RuntimeChunkingConfig(
            mode=config.mode,
            target_chunk_size=config.target_chunk_size,
            overlap_size=config.overlap_size,
            min_chunk_size=config.min_chunk_size,
            max_chunk_size=config.max_chunk_size,
            quality_threshold=config.quality_threshold,
            preserve_structure=config.preserve_structure,
            maintain_context=config.maintain_context,
            strategy_configs=config.strategy_configs.copy(),
            document_type=config.document_type,
            content_language=config.content_language,
            enable_auto_optimization=config.enable_auto_optimization,
            enable_quality_feedback=config.enable_quality_feedback,
            enable_performance_monitoring=config.enable_performance_monitoring,
            hybrid_strategies=config.hybrid_strategies.copy(),
            hybrid_weights=config.hybrid_weights.copy(),
            max_processing_time_ms=config.max_processing_time_ms,
            memory_limit_mb=config.memory_limit_mb,
            parallel_processing=config.parallel_processing
        )
        
        # 根据质量反馈调整
        quality_score = performance_feedback.get("quality_score", 0.7)
        if quality_score < 0.6:
            # 质量不够，增加重叠或改变策略
            optimized.overlap_size = min(int(optimized.overlap_size * 1.2), 500)
            if optimized.mode == ChunkingMode.FIXED_SIZE:
                optimized.mode = ChunkingMode.PARAGRAPH
        
        # 根据速度反馈调整
        processing_time = performance_feedback.get("processing_time_ms", 0)
        if processing_time > 10000:  # 超过10秒认为太慢
            if optimized.mode == ChunkingMode.SEMANTIC:
                optimized.mode = ChunkingMode.PARAGRAPH
            elif optimized.mode == ChunkingMode.ADAPTIVE:
                optimized.mode = ChunkingMode.PARAGRAPH
        
        # 根据内存使用调整
        memory_usage = performance_feedback.get("memory_usage_mb", 0)
        if memory_usage > 500:  # 超过500MB认为太多
            optimized.target_chunk_size = max(int(optimized.target_chunk_size * 0.8), 500)
            optimized.parallel_processing = False
        
        return optimized
    
    def validate_config(self, config: RuntimeChunkingConfig) -> bool:
        """验证配置的有效性"""
        
        # 基本参数验证
        if config.target_chunk_size <= 0:
            return False
        if config.overlap_size < 0:
            return False
        if config.min_chunk_size <= 0:
            return False
        if config.max_chunk_size <= config.min_chunk_size:
            return False
        if not (0 <= config.quality_threshold <= 1):
            return False
        
        # 重叠大小不能超过目标大小
        if config.overlap_size >= config.target_chunk_size:
            return False
        
        # 混合策略验证
        if config.mode == ChunkingMode.HYBRID:
            if not config.hybrid_strategies:
                return False
            if config.hybrid_weights and len(config.hybrid_weights) != len(config.hybrid_strategies):
                return False
        
        return True
    
    def get_contextual_config(self) -> ContextualConfig:
        """获取上下文配置"""
        return self._contextual_config
    
    def update_contextual_config(self, **kwargs):
        """更新上下文配置"""
        for key, value in kwargs.items():
            if hasattr(self._contextual_config, key):
                setattr(self._contextual_config, key, value)


# 全局配置管理器实例
_config_manager: Optional[ChunkingConfigManager] = None


def get_config_manager() -> ChunkingConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ChunkingConfigManager()
    return _config_manager


def create_config_from_dict(config_dict: Dict[str, Any]) -> RuntimeChunkingConfig:
    """从字典创建配置"""
    # 处理枚举类型
    if "mode" in config_dict and isinstance(config_dict["mode"], str):
        config_dict["mode"] = ChunkingMode(config_dict["mode"])
    
    if "document_type" in config_dict and isinstance(config_dict["document_type"], str):
        config_dict["document_type"] = DocumentType(config_dict["document_type"])
    
    return RuntimeChunkingConfig(**config_dict)


def config_to_dict(config: RuntimeChunkingConfig) -> Dict[str, Any]:
    """将配置转换为字典"""
    result = {}
    
    for key, value in config.__dict__.items():
        if isinstance(value, Enum):
            result[key] = value.value
        elif isinstance(value, (list, dict)):
            result[key] = value.copy() if hasattr(value, 'copy') else value
        else:
            result[key] = value
    
    return result


def load_chunking_config_from_global() -> RuntimeChunkingConfig:
    """从全局配置加载分块配置"""
    from config import AppConfig
    
    try:
        app_config = AppConfig()
        return RuntimeChunkingConfig.from_global_config(app_config.chunking)
    except Exception as e:
        logger.warning(f"Failed to load global chunking config: {e}")
        return RuntimeChunkingConfig()  # 返回默认配置