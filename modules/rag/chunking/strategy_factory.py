"""
Chunking策略工厂

实现策略的自动注册、发现和智能选择机制。
"""

import logging
import asyncio
import importlib
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, Union
from collections import defaultdict

from modules.rag.chunking.base import (
    IChunkingStrategy, 
    ChunkingContext, 
    ChunkingResult,
    StrategyPriority,
    ChunkingStrategyError
)
from modules.schemas.enums import ChunkingStrategy as ChunkingStrategyEnum

logger = logging.getLogger(__name__)


class ChunkingStrategyRegistry:
    """分块策略注册表"""
    
    def __init__(self):
        self._strategies: Dict[str, Type[IChunkingStrategy]] = {}
        self._strategy_instances: Dict[str, IChunkingStrategy] = {}
        self._strategy_metadata: Dict[str, Dict[str, Any]] = {}
        self._auto_discovery_paths: Set[str] = set()
    
    def register_strategy(
        self, 
        name: str, 
        strategy_class: Type[IChunkingStrategy],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """注册分块策略"""
        if name in self._strategies:
            logger.warning(f"Strategy '{name}' already registered, overriding")
        
        self._strategies[name] = strategy_class
        self._strategy_metadata[name] = metadata or {}
        
        # 清除缓存的实例
        if name in self._strategy_instances:
            del self._strategy_instances[name]
        
        logger.info(f"Registered chunking strategy: {name}")
    
    def unregister_strategy(self, name: str) -> bool:
        """注销分块策略"""
        if name not in self._strategies:
            return False
        
        del self._strategies[name]
        del self._strategy_metadata[name]
        
        if name in self._strategy_instances:
            del self._strategy_instances[name]
        
        logger.info(f"Unregistered chunking strategy: {name}")
        return True
    
    def get_strategy(self, name: str, config: Optional[Dict[str, Any]] = None) -> IChunkingStrategy:
        """获取策略实例"""
        if name not in self._strategies:
            raise ChunkingStrategyError(f"Strategy '{name}' not registered")
        
        # 如果配置发生变化，重新创建实例
        cache_key = f"{name}_{hash(str(sorted((config or {}).items())))}"
        
        if cache_key not in self._strategy_instances:
            strategy_class = self._strategies[name]
            try:
                instance = strategy_class(config=config)
                self._strategy_instances[cache_key] = instance
            except Exception as e:
                raise ChunkingStrategyError(
                    f"Failed to instantiate strategy '{name}': {e}",
                    strategy_name=name
                )
        
        return self._strategy_instances[cache_key]
    
    def list_strategies(self) -> List[str]:
        """列出所有注册的策略"""
        return list(self._strategies.keys())
    
    def get_strategy_metadata(self, name: str) -> Dict[str, Any]:
        """获取策略元数据"""
        return self._strategy_metadata.get(name, {})
    
    def add_auto_discovery_path(self, path: str) -> None:
        """添加自动发现路径"""
        self._auto_discovery_paths.add(path)
    
    def discover_strategies(self) -> int:
        """自动发现并注册策略"""
        discovered_count = 0
        
        for path in self._auto_discovery_paths:
            try:
                discovered_count += self._discover_in_path(path)
            except Exception as e:
                logger.warning(f"Failed to discover strategies in {path}: {e}")
        
        return discovered_count
    
    def _discover_in_path(self, path: str) -> int:
        """在指定路径中发现策略"""
        discovered = 0
        
        try:
            # 动态导入模块
            module = importlib.import_module(path)
            
            # 检查模块中的所有属性
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # 检查是否是策略类
                if (
                    isinstance(attr, type) 
                    and hasattr(attr, '__annotations__')
                    and issubclass(attr, IChunkingStrategy)
                    and attr != IChunkingStrategy
                ):
                    # 自动注册
                    strategy_name = getattr(attr, 'STRATEGY_NAME', attr.__name__.lower())
                    self.register_strategy(strategy_name, attr)
                    discovered += 1
                    
        except Exception as e:
            logger.warning(f"Failed to discover in {path}: {e}")
        
        return discovered


class ChunkingStrategyFactory:
    """分块策略工厂"""
    
    def __init__(self, registry: Optional[ChunkingStrategyRegistry] = None):
        self.registry = registry or ChunkingStrategyRegistry()
        self._selection_rules: List[callable] = []
        self._performance_cache: Dict[str, Dict[str, float]] = {}
    
    async def select_best_strategy(
        self, 
        context: ChunkingContext,
        candidate_strategies: Optional[List[str]] = None
    ) -> IChunkingStrategy:
        """智能选择最佳策略"""
        
        # 获取候选策略
        candidates = candidate_strategies or self.registry.list_strategies()
        if not candidates:
            raise ChunkingStrategyError("No strategies available")
        
        # 评估所有候选策略
        strategy_scores = {}
        
        for strategy_name in candidates:
            try:
                strategy = self.registry.get_strategy(strategy_name)
                
                # 检查是否能处理
                if not await strategy.can_handle(context):
                    continue
                
                # 计算综合评分
                score = await self._calculate_strategy_score(strategy, context)
                strategy_scores[strategy_name] = score
                
            except Exception as e:
                logger.warning(f"Failed to evaluate strategy {strategy_name}: {e}")
                continue
        
        if not strategy_scores:
            raise ChunkingStrategyError("No suitable strategy found")
        
        # 选择得分最高的策略
        best_strategy_name = max(strategy_scores, key=strategy_scores.get)
        logger.info(f"Selected strategy '{best_strategy_name}' with score {strategy_scores[best_strategy_name]:.3f}")
        
        return self.registry.get_strategy(best_strategy_name)
    
    async def _calculate_strategy_score(
        self, 
        strategy: IChunkingStrategy, 
        context: ChunkingContext
    ) -> float:
        """计算策略综合评分"""
        
        # 获取性能估算
        performance = await strategy.estimate_performance(context)
        
        # 基础评分权重
        weights = {
            "quality_score": 0.4,
            "processing_speed": 0.2, 
            "memory_usage": 0.1,
            "suitability": 0.3
        }
        
        # 计算加权平均分
        score = sum(
            performance.get(metric, 0.5) * weight 
            for metric, weight in weights.items()
        )
        
        # 根据策略优先级调整
        priority_bonus = {
            StrategyPriority.LOWEST: 0.0,
            StrategyPriority.LOW: 0.02,
            StrategyPriority.MEDIUM: 0.05,
            StrategyPriority.HIGH: 0.08,
            StrategyPriority.HIGHEST: 0.1
        }
        
        score += priority_bonus.get(strategy.priority, 0.0)
        
        # 应用自定义选择规则
        for rule in self._selection_rules:
            try:
                score = rule(strategy, context, score)
            except Exception as e:
                logger.warning(f"Selection rule failed: {e}")
        
        return min(max(score, 0.0), 1.0)
    
    def add_selection_rule(self, rule: callable) -> None:
        """添加策略选择规则"""
        self._selection_rules.append(rule)
    
    async def chunk_document(
        self, 
        context: ChunkingContext,
        strategy_name: Optional[str] = None
    ) -> ChunkingResult:
        """执行文档分块"""
        
        if strategy_name:
            # 使用指定策略
            strategy = self.registry.get_strategy(strategy_name)
            if not await strategy.can_handle(context):
                raise ChunkingStrategyError(
                    f"Strategy '{strategy_name}' cannot handle the document",
                    strategy_name=strategy_name,
                    document_id=context.document.id
                )
        else:
            # 自动选择最佳策略
            strategy = await self.select_best_strategy(context)
        
        # 执行分块
        try:
            result = await strategy.chunk_document(context)
            logger.info(
                f"Document {context.document.id} chunked with {strategy.name}: "
                f"{result.chunk_count} chunks, quality={result.quality_score:.3f}"
            )
            return result
            
        except Exception as e:
            raise ChunkingStrategyError(
                f"Chunking failed with strategy '{strategy.name}': {e}",
                strategy_name=strategy.name,
                document_id=context.document.id
            )
    
    def get_strategy_recommendations(
        self, 
        context: ChunkingContext
    ) -> List[Dict[str, Any]]:
        """获取策略推荐列表"""
        recommendations = []
        
        for strategy_name in self.registry.list_strategies():
            try:
                strategy = self.registry.get_strategy(strategy_name)
                
                # 异步评估改为同步（简化版本）
                can_handle = True  # 简化判断
                performance = {
                    "quality_score": 0.7,
                    "processing_speed": 1.0,
                    "suitability": 0.7
                }
                
                if can_handle:
                    recommendations.append({
                        "strategy_name": strategy_name,
                        "priority": strategy.priority.value,
                        "supported_types": strategy.supported_content_types,
                        "estimated_performance": performance,
                        "metadata": self.registry.get_strategy_metadata(strategy_name)
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to evaluate strategy {strategy_name}: {e}")
        
        # 按优先级排序
        recommendations.sort(key=lambda x: x["priority"], reverse=True)
        return recommendations


def register_chunking_strategy(
    name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """装饰器：自动注册分块策略"""
    
    def decorator(strategy_class: Type[IChunkingStrategy]):
        strategy_name = name or getattr(strategy_class, 'STRATEGY_NAME', strategy_class.__name__.lower())
        
        # 注册到全局注册表
        get_global_registry().register_strategy(strategy_name, strategy_class, metadata)
        
        # 为策略类添加名称属性
        strategy_class.STRATEGY_NAME = strategy_name
        
        logger.info(f"Auto-registered chunking strategy: {strategy_name}")
        return strategy_class
    
    return decorator


# 全局策略注册表和工厂
_global_registry: Optional[ChunkingStrategyRegistry] = None
_global_factory: Optional[ChunkingStrategyFactory] = None


def get_global_registry() -> ChunkingStrategyRegistry:
    """获取全局策略注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ChunkingStrategyRegistry()
        # 添加默认发现路径
        _global_registry.add_auto_discovery_path("modules.rag.chunking.strategies")
    return _global_registry


def get_global_factory() -> ChunkingStrategyFactory:
    """获取全局策略工厂"""
    global _global_factory
    if _global_factory is None:
        _global_factory = ChunkingStrategyFactory(get_global_registry())
    return _global_factory


def discover_and_register_strategies() -> int:
    """发现并注册所有策略"""
    registry = get_global_registry()
    return registry.discover_strategies()