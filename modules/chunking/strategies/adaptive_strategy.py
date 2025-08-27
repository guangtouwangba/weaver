"""
自适应分块策略

根据文档特征动态选择和组合最佳的分块方法。
"""

import time
import asyncio
from typing import Any, Dict, List, Optional, Tuple

from modules.chunking.base import (
    BaseChunkingStrategy,
    ChunkingContext,
    ChunkingResult, 
    StrategyPriority
)
from modules.chunking.strategy_factory import register_chunking_strategy


@register_chunking_strategy(
    name="adaptive",
    metadata={
        "description": "根据文档特征自适应选择最佳分块策略",
        "best_for": ["混合文档", "复杂结构", "未知格式"],
        "complexity": "最高",
        "speed": "中等"
    }
)
class AdaptiveStrategy(BaseChunkingStrategy):
    """自适应分块策略"""
    
    @property
    def name(self) -> str:
        return "adaptive"
    
    @property
    def priority(self) -> StrategyPriority:
        return StrategyPriority.HIGHEST
    
    @property
    def supported_content_types(self) -> List[str]:
        return ["text/plain", "text/markdown", "text/html", "application/pdf"]
    
    def get_default_config(self) -> Dict[str, Any]:
        base_config = super().get_default_config()
        base_config.update({
            # 策略选择权重
            "strategy_weights": {
                "fixed_size": 0.3,
                "paragraph": 0.4,
                "sentence": 0.2,
                "semantic": 0.1  # 默认较低，因为计算成本高
            },
            
            # 文档特征阈值
            "structure_score_threshold": 0.7,
            "semantic_threshold": 0.5,
            "dialogue_threshold": 0.3,
            "technical_threshold": 0.6,
            
            # 混合策略配置
            "enable_hybrid_chunking": True,
            "max_hybrid_strategies": 2,
            "hybrid_transition_overlap": 100,
            
            # 动态调整配置
            "enable_dynamic_adjustment": True,
            "quality_feedback_threshold": 0.8,
            "adjustment_factor": 0.1,
            
            # 性能优化
            "enable_performance_optimization": True,
            "performance_weight": 0.2,
            "quality_weight": 0.6,
            "speed_weight": 0.2,
            
            # 回退策略
            "fallback_strategy": "fixed_size",
            "fallback_threshold": 0.5
        })
        return base_config
    
    async def can_handle(self, context: ChunkingContext) -> bool:
        """自适应策略可以处理所有类型的文档"""
        base_check = await super().can_handle(context)
        return base_check  # 几乎总是返回True
    
    async def estimate_performance(self, context: ChunkingContext) -> Dict[str, float]:
        """估算自适应策略的性能"""
        # 自适应策略的性能取决于选择的子策略
        doc_features = await self._analyze_document_features(context)
        strategy_scores = await self._calculate_strategy_scores(context, doc_features)
        
        if not strategy_scores:
            return {
                "quality_score": 0.5,
                "processing_speed": 1.0,
                "memory_usage": 1.2,
                "suitability": 0.7
            }
        
        # 基于最佳策略估算
        best_strategy = max(strategy_scores, key=strategy_scores.get)
        base_performance = {
            "fixed_size": {"quality": 0.6, "speed": 1.0, "memory": 0.8},
            "paragraph": {"quality": 0.8, "speed": 0.9, "memory": 0.7},
            "sentence": {"quality": 0.75, "speed": 0.9, "memory": 0.6},
            "semantic": {"quality": 0.95, "speed": 0.4, "memory": 1.5}
        }.get(best_strategy, {"quality": 0.7, "speed": 0.8, "memory": 1.0})
        
        # 自适应策略有额外开销但质量更高
        return {
            "quality_score": min(base_performance["quality"] + 0.1, 1.0),
            "processing_speed": base_performance["speed"] * 0.9,  # 略慢因为需要分析
            "memory_usage": base_performance["memory"] * 1.1,
            "suitability": 0.9  # 高适用性
        }
    
    async def chunk_document(self, context: ChunkingContext) -> ChunkingResult:
        """执行自适应分块"""
        start_time = time.time()
        
        # 1. 分析文档特征
        doc_features = await self._analyze_document_features(context)
        
        # 2. 计算各策略评分
        strategy_scores = await self._calculate_strategy_scores(context, doc_features)
        
        # 3. 选择最佳策略组合
        selected_strategies = self._select_strategies(strategy_scores, doc_features)
        
        # 4. 执行分块
        if len(selected_strategies) == 1:
            # 单策略执行
            result = await self._execute_single_strategy(
                context, selected_strategies[0], doc_features
            )
        else:
            # 混合策略执行
            result = await self._execute_hybrid_strategy(
                context, selected_strategies, doc_features
            )
        
        # 5. 动态调整（如果启用）
        if self.config.get("enable_dynamic_adjustment", True):
            result = await self._apply_dynamic_adjustments(result, doc_features)
        
        # 更新处理时间
        processing_time = (time.time() - start_time) * 1000
        result.processing_time_ms = processing_time
        
        # 添加自适应策略特定的元数据
        result.strategy_metadata.update({
            "document_features": doc_features,
            "strategy_scores": strategy_scores,
            "selected_strategies": selected_strategies,
            "adaptation_decisions": {
                "primary_strategy": selected_strategies[0] if selected_strategies else "none",
                "hybrid_used": len(selected_strategies) > 1,
                "dynamic_adjustments_applied": self.config.get("enable_dynamic_adjustment", True)
            }
        })
        
        return result
    
    async def _analyze_document_features(self, context: ChunkingContext) -> Dict[str, Any]:
        """分析文档特征"""
        content = context.document.content
        
        features = {
            # 基本特征
            "length": context.document_length,
            "word_count": context.word_count,
            "paragraph_count": context.paragraph_count,
            "sentence_count": context.sentence_count,
            "avg_paragraph_length": context.avg_paragraph_length,
            "avg_sentence_length": context.avg_sentence_length,
            "has_structure_markers": context.has_structure_markers,
            
            # 高级特征
            "structure_score": self._calculate_structure_score(content),
            "dialogue_ratio": self._calculate_dialogue_ratio(content),
            "technical_score": self._calculate_technical_score(content),
            "repetition_score": self._calculate_repetition_score(content),
            "complexity_score": self._calculate_complexity_score(context),
            
            # 语言特征
            "language": self._detect_language(content),
            "multilingual": self._is_multilingual(content),
            
            # 内容类型特征
            "is_academic": self._is_academic_content(content),
            "is_dialogue": self._is_dialogue_heavy(content),
            "is_technical": self._is_technical_content(content),
            "is_narrative": self._is_narrative_content(content)
        }
        
        return features
    
    def _calculate_structure_score(self, content: str) -> float:
        """计算文档结构化程度"""
        structure_indicators = [
            len([line for line in content.split('\n') if line.strip().startswith('#')]),  # 标题
            content.count('\n\n'),  # 段落分隔
            len([line for line in content.split('\n') if line.strip().startswith(('*', '-', '+'))]),  # 列表
            content.count('```'),  # 代码块
            len([line for line in content.split('\n') if '|' in line and line.count('|') > 2])  # 表格
        ]
        
        total_lines = len(content.split('\n'))
        structure_ratio = sum(structure_indicators) / max(total_lines, 1)
        
        return min(structure_ratio * 2, 1.0)
    
    def _calculate_dialogue_ratio(self, content: str) -> float:
        """计算对话内容比例"""
        dialogue_markers = ['"', "'", '"', '"', ''', ''']
        dialogue_chars = sum(content.count(marker) for marker in dialogue_markers)
        
        return min(dialogue_chars / max(len(content), 1), 1.0)
    
    def _calculate_technical_score(self, content: str) -> float:
        """计算技术内容评分"""
        technical_indicators = [
            'function', 'class', 'import', 'def', 'return',
            'API', 'HTTP', 'JSON', 'XML', 'SQL',
            'algorithm', 'parameter', 'variable', 'method'
        ]
        
        word_count = len(content.split())
        tech_word_count = sum(content.lower().count(word) for word in technical_indicators)
        
        return min(tech_word_count / max(word_count, 1) * 10, 1.0)
    
    def _calculate_repetition_score(self, content: str) -> float:
        """计算内容重复性"""
        words = content.lower().split()
        if len(words) < 10:
            return 0.0
        
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 计算重复词汇比例
        repeated_words = sum(1 for count in word_freq.values() if count > 1)
        repetition_ratio = repeated_words / len(word_freq)
        
        return repetition_ratio
    
    def _calculate_complexity_score(self, context: ChunkingContext) -> float:
        """计算文档复杂度"""
        # 基于多个维度计算复杂度
        length_complexity = min(context.document_length / 10000, 1.0)
        structure_complexity = 1.0 if context.has_structure_markers else 0.3
        sentence_complexity = min(context.avg_sentence_length / 100, 1.0)
        
        return (length_complexity + structure_complexity + sentence_complexity) / 3
    
    def _detect_language(self, content: str) -> str:
        """检测主要语言"""
        import re
        
        # 简单的语言检测
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        english_chars = len(re.findall(r'[a-zA-Z]', content))
        
        total_chars = chinese_chars + english_chars
        if total_chars == 0:
            return "unknown"
        
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.6:
            return "zh"
        elif chinese_ratio < 0.2:
            return "en"
        else:
            return "mixed"
    
    def _is_multilingual(self, content: str) -> bool:
        """检测是否为多语言内容"""
        return self._detect_language(content) == "mixed"
    
    def _is_academic_content(self, content: str) -> bool:
        """检测是否为学术内容"""
        academic_keywords = [
            'abstract', 'introduction', 'methodology', 'results', 'conclusion',
            'reference', 'bibliography', 'citation', 'research', 'study',
            'analysis', 'hypothesis', 'experiment', 'data', 'figure'
        ]
        
        content_lower = content.lower()
        academic_count = sum(1 for keyword in academic_keywords if keyword in content_lower)
        
        return academic_count >= 3
    
    def _is_dialogue_heavy(self, content: str) -> bool:
        """检测是否为对话为主的内容"""
        return self._calculate_dialogue_ratio(content) > self.config.get("dialogue_threshold", 0.3)
    
    def _is_technical_content(self, content: str) -> bool:
        """检测是否为技术内容"""
        return self._calculate_technical_score(content) > self.config.get("technical_threshold", 0.6)
    
    def _is_narrative_content(self, content: str) -> bool:
        """检测是否为叙述性内容"""
        narrative_indicators = [
            'once upon', 'long ago', 'suddenly', 'then', 'finally',
            'he said', 'she said', 'they went', 'story', 'character'
        ]
        
        content_lower = content.lower()
        narrative_count = sum(1 for indicator in narrative_indicators if indicator in content_lower)
        
        return narrative_count >= 2
    
    async def _calculate_strategy_scores(
        self, 
        context: ChunkingContext, 
        features: Dict[str, Any]
    ) -> Dict[str, float]:
        """计算各策略的适用性评分"""
        scores = {}
        
        # Fixed Size Strategy 评分
        scores["fixed_size"] = self._score_fixed_size_strategy(features)
        
        # Paragraph Strategy 评分
        scores["paragraph"] = self._score_paragraph_strategy(features)
        
        # Sentence Strategy 评分
        scores["sentence"] = self._score_sentence_strategy(features)
        
        # Semantic Strategy 评分
        scores["semantic"] = self._score_semantic_strategy(features)
        
        # 应用权重
        weights = self.config.get("strategy_weights", {})
        for strategy, weight in weights.items():
            if strategy in scores:
                scores[strategy] *= weight
        
        return scores
    
    def _score_fixed_size_strategy(self, features: Dict[str, Any]) -> float:
        """评分固定大小策略"""
        score = 0.5  # 基础分数
        
        # 适合简单、均匀的文档
        if features.get("structure_score", 0) < 0.3:
            score += 0.3
        
        # 适合长文档
        if features.get("length", 0) > 10000:
            score += 0.2
        
        # 不适合对话和技术内容
        if features.get("is_dialogue", False):
            score -= 0.2
        if features.get("technical_score", 0) > 0.7:
            score -= 0.1
        
        return max(min(score, 1.0), 0.0)
    
    def _score_paragraph_strategy(self, features: Dict[str, Any]) -> float:
        """评分段落策略"""
        score = 0.6  # 基础分数
        
        # 适合结构化文档
        if features.get("structure_score", 0) > 0.5:
            score += 0.3
        
        # 适合学术和叙述内容
        if features.get("is_academic", False):
            score += 0.2
        if features.get("is_narrative", False):
            score += 0.1
        
        # 需要有足够的段落
        if features.get("paragraph_count", 0) < 3:
            score -= 0.3
        
        return max(min(score, 1.0), 0.0)
    
    def _score_sentence_strategy(self, features: Dict[str, Any]) -> float:
        """评分句子策略"""
        score = 0.4  # 基础分数
        
        # 适合对话内容
        if features.get("is_dialogue", False):
            score += 0.4
        
        # 适合短文档
        if features.get("length", 0) < 5000:
            score += 0.2
        
        # 适合问答格式
        if features.get("dialogue_ratio", 0) > 0.2:
            score += 0.2
        
        # 不适合长段落
        if features.get("avg_paragraph_length", 0) > 1000:
            score -= 0.2
        
        return max(min(score, 1.0), 0.0)
    
    def _score_semantic_strategy(self, features: Dict[str, Any]) -> float:
        """评分语义策略"""
        score = 0.3  # 基础分数（因为计算成本高）
        
        # 适合复杂文档
        if features.get("complexity_score", 0) > 0.7:
            score += 0.4
        
        # 适合技术和学术内容
        if features.get("is_technical", False):
            score += 0.3
        if features.get("is_academic", False):
            score += 0.2
        
        # 适合多语言内容
        if features.get("multilingual", False):
            score += 0.1
        
        # 不适合简单重复内容
        if features.get("repetition_score", 0) > 0.8:
            score -= 0.3
        
        return max(min(score, 1.0), 0.0)
    
    def _select_strategies(
        self, 
        scores: Dict[str, float], 
        features: Dict[str, Any]
    ) -> List[str]:
        """选择最佳策略组合"""
        if not scores:
            return [self.config.get("fallback_strategy", "fixed_size")]
        
        # 排序策略
        sorted_strategies = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # 选择最佳策略
        best_strategy = sorted_strategies[0][0]
        best_score = sorted_strategies[0][1]
        
        # 检查是否使用回退策略
        fallback_threshold = self.config.get("fallback_threshold", 0.5)
        if best_score < fallback_threshold:
            return [self.config.get("fallback_strategy", "fixed_size")]
        
        # 检查是否使用混合策略
        if (self.config.get("enable_hybrid_chunking", True) and 
            len(sorted_strategies) > 1):
            
            second_best = sorted_strategies[1]
            max_strategies = self.config.get("max_hybrid_strategies", 2)
            
            # 如果第二好的策略分数也不错，考虑混合
            if second_best[1] > best_score * 0.8:
                return [best_strategy, second_best[0]][:max_strategies]
        
        return [best_strategy]
    
    async def _execute_single_strategy(
        self, 
        context: ChunkingContext, 
        strategy_name: str, 
        features: Dict[str, Any]
    ) -> ChunkingResult:
        """执行单一策略"""
        # 这里需要动态创建策略实例
        # 在实际实现中，需要从工厂获取策略实例
        from modules.chunking.strategy_factory import get_global_factory
        
        factory = get_global_factory()
        try:
            result = await factory.chunk_document(context, strategy_name)
            result.strategy_used = f"adaptive({strategy_name})"
            return result
        except Exception as e:
            # 回退到固定大小策略
            fallback = self.config.get("fallback_strategy", "fixed_size")
            result = await factory.chunk_document(context, fallback)
            result.strategy_used = f"adaptive({fallback}_fallback)"
            return result
    
    async def _execute_hybrid_strategy(
        self, 
        context: ChunkingContext, 
        strategies: List[str], 
        features: Dict[str, Any]
    ) -> ChunkingResult:
        """执行混合策略"""
        # 简化实现：使用主策略，但记录混合信息
        primary_strategy = strategies[0]
        result = await self._execute_single_strategy(context, primary_strategy, features)
        
        # 更新策略名称显示混合使用
        result.strategy_used = f"adaptive(hybrid:{'+'.join(strategies)})"
        
        # 在实际实现中，这里可以实现真正的混合分块逻辑
        # 比如对不同部分使用不同策略
        
        return result
    
    async def _apply_dynamic_adjustments(
        self, 
        result: ChunkingResult, 
        features: Dict[str, Any]
    ) -> ChunkingResult:
        """应用动态调整"""
        # 检查质量并进行必要的调整
        quality_threshold = self.config.get("quality_feedback_threshold", 0.8)
        
        if result.quality_score < quality_threshold:
            # 可以在这里实现质量改进逻辑
            # 比如重新分块、调整参数等
            pass
        
        return result