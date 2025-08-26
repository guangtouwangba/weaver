"""
Chunking系统集成工具

提供与现有RAG系统的集成接口和工具函数。
"""

import logging
from typing import Dict, Any, Optional

from modules.rag.chunking.config import (
    get_config_manager,
    load_chunking_config_from_global,
    RuntimeChunkingConfig,
    ChunkingMode,
    DocumentType
)
from modules.rag.chunking.strategy_factory import get_global_factory
from modules.schemas import Document

logger = logging.getLogger(__name__)


class ChunkingIntegration:
    """Chunking系统集成类"""
    
    def __init__(self):
        self.factory = get_global_factory()
        self.config_manager = get_config_manager()
        self._initialized = False
    
    async def initialize(self):
        """初始化集成系统"""
        if self._initialized:
            return
        
        try:
            # 显式导入所有策略以触发自动注册
            import modules.rag.chunking.strategies
            
            # 发现并注册所有可用策略
            from modules.rag.chunking.strategy_factory import discover_and_register_strategies
            discovered_count = discover_and_register_strategies()
            logger.info(f"发现并注册了 {discovered_count} 个分块策略")
            
            # 确保所有策略都已注册
            strategies = self.factory.registry.list_strategies()
            logger.info(f"已注册的分块策略: {strategies}")
            
            # 加载全局配置
            try:
                global_config = load_chunking_config_from_global()
                self.config_manager.set_global_config(global_config)
                logger.info("成功加载全局chunking配置")
            except Exception as e:
                logger.warning(f"加载全局配置失败: {e}, 使用默认配置")
            
            self._initialized = True
            logger.info("Chunking系统集成初始化完成")
            
        except Exception as e:
            logger.error(f"Chunking系统集成初始化失败: {e}")
            raise
    
    def recommend_strategy_for_document(
        self, 
        document: Document,
        content_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """为文档推荐分块策略"""
        
        if not content_analysis:
            # 简单分析
            content = document.content
            content_analysis = {
                "length": len(content),
                "has_structure": any(marker in content for marker in ['#', '*', '-', '1.']),
                "avg_line_length": sum(len(line) for line in content.split('\n')) / max(len(content.split('\n')), 1),
                "dialogue_markers": content.count('"') + content.count("'"),
            }
        
        # 获取推荐
        recommendations = self.factory.get_strategy_recommendations(content_analysis)
        
        if recommendations:
            best_rec = recommendations[0]
            return {
                "recommended_strategy": best_rec["strategy_name"],
                "confidence": best_rec["estimated_performance"].get("suitability", 0.7),
                "reasons": self._generate_recommendation_reasons(content_analysis, best_rec),
                "all_recommendations": recommendations[:3]  # 返回前3个推荐
            }
        else:
            return {
                "recommended_strategy": "fixed_size",
                "confidence": 0.5,
                "reasons": ["无法分析文档特征，使用默认策略"],
                "all_recommendations": []
            }
    
    def _generate_recommendation_reasons(
        self, 
        analysis: Dict[str, Any], 
        recommendation: Dict[str, Any]
    ) -> list[str]:
        """生成推荐理由"""
        reasons = []
        strategy = recommendation["strategy_name"]
        
        if strategy == "paragraph":
            if analysis.get("has_structure", False):
                reasons.append("文档具有良好的段落结构")
            if analysis.get("length", 0) > 5000:
                reasons.append("较长文档适合按段落分块")
        
        elif strategy == "sentence":
            if analysis.get("dialogue_markers", 0) > 10:
                reasons.append("检测到对话内容，适合句子级分块")
            if analysis.get("avg_line_length", 0) < 100:
                reasons.append("短句较多，适合句子分块")
        
        elif strategy == "semantic":
            if analysis.get("length", 0) > 10000:
                reasons.append("长文档适合语义分块以保持内容相关性")
            reasons.append("内容复杂度较高，语义分块质量更好")
        
        elif strategy == "adaptive":
            reasons.append("文档特征复杂，自适应策略最优")
            if analysis.get("has_structure") and analysis.get("length", 0) > 5000:
                reasons.append("结构化长文档适合自适应处理")
        
        else:  # fixed_size
            if analysis.get("length", 0) < 2000:
                reasons.append("较短文档使用固定大小分块效率更高")
            reasons.append("通用分块策略，适合大多数场景")
        
        return reasons or ["基于文档特征分析的最佳选择"]
    
    def create_optimized_config_for_document(
        self, 
        document: Document,
        base_config: Optional[RuntimeChunkingConfig] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> RuntimeChunkingConfig:
        """为特定文档创建优化配置"""
        
        if base_config is None:
            try:
                base_config = load_chunking_config_from_global()
            except:
                base_config = RuntimeChunkingConfig()
        
        # 分析文档
        content = document.content
        doc_features = {
            "length": len(content),
            "word_count": len(content.split()),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "sentence_count": content.count('.') + content.count('!') + content.count('?'),
            "has_structure_markers": any(m in content for m in ['#', '*', '-', '```']),
            "content_type": document.content_type.value if hasattr(document.content_type, 'value') else str(document.content_type),
        }
        
        # 计算特征
        if doc_features["paragraph_count"] > 0:
            doc_features["avg_paragraph_length"] = doc_features["length"] / doc_features["paragraph_count"]
        else:
            doc_features["avg_paragraph_length"] = doc_features["length"]
        
        if doc_features["sentence_count"] > 0:
            doc_features["avg_sentence_length"] = doc_features["length"] / doc_features["sentence_count"]
        else:
            doc_features["avg_sentence_length"] = doc_features["length"]
        
        # 创建上下文配置
        contextual_config = self.config_manager.create_contextual_config(
            base_config, 
            doc_features
        )
        
        # 应用用户偏好
        if user_preferences:
            if "chunk_size" in user_preferences:
                contextual_config.target_chunk_size = user_preferences["chunk_size"]
            if "overlap" in user_preferences:
                contextual_config.overlap_size = user_preferences["overlap"]
            if "strategy" in user_preferences:
                strategy_name = user_preferences["strategy"]
                if strategy_name in ["fixed_size", "paragraph", "sentence", "semantic", "adaptive"]:
                    contextual_config.mode = ChunkingMode(strategy_name)
        
        return contextual_config
    
    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态"""
        strategies = self.factory.registry.list_strategies()
        presets = self.config_manager.list_presets()
        
        return {
            "initialized": self._initialized,
            "available_strategies": strategies,
            "strategy_count": len(strategies),
            "available_presets": presets,
            "preset_count": len(presets),
            "factory_ready": bool(self.factory),
            "config_manager_ready": bool(self.config_manager)
        }


# 全局集成实例
_integration_instance: Optional[ChunkingIntegration] = None


def get_chunking_integration() -> ChunkingIntegration:
    """获取全局Chunking集成实例"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = ChunkingIntegration()
    return _integration_instance


async def initialize_chunking_integration():
    """初始化Chunking集成"""
    integration = get_chunking_integration()
    await integration.initialize()
    logger.info("Chunking集成系统已初始化")


def get_document_chunking_recommendation(
    document: Document,
    content_analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """获取文档分块推荐（便捷函数）"""
    integration = get_chunking_integration()
    return integration.recommend_strategy_for_document(document, content_analysis)


def create_document_chunking_config(
    document: Document,
    user_preferences: Optional[Dict[str, Any]] = None
) -> RuntimeChunkingConfig:
    """为文档创建分块配置（便捷函数）"""
    integration = get_chunking_integration()
    return integration.create_optimized_config_for_document(
        document, 
        user_preferences=user_preferences
    )