"""
Query Routing Engine Core

查询路由引擎核心实现，支持多种路由策略和规则系统。
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class RouteDecision:
    """路由决策结果"""
    
    def __init__(
        self,
        handler_name: str,
        confidence: float,
        metadata: Dict[str, Any] = None
    ):
        self.handler_name = handler_name
        self.confidence = confidence
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "handler_name": self.handler_name,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class RoutingResult:
    """路由执行结果"""
    
    def __init__(
        self,
        decision: RouteDecision,
        handler: Any,
        execution_time_ms: float = 0.0,
        success: bool = True,
        error: Optional[str] = None
    ):
        self.decision = decision
        self.handler = handler
        self.execution_time_ms = execution_time_ms
        self.success = success
        self.error = error
        

class RoutingRule:
    """路由规则"""
    
    def __init__(
        self,
        name: str,
        condition: Callable[[str, Dict[str, Any]], bool],
        handler_name: str,
        priority: int = 0,
        description: str = ""
    ):
        self.name = name
        self.condition = condition
        self.handler_name = handler_name
        self.priority = priority
        self.description = description
        self.created_at = datetime.now()
        
    async def matches(self, query: str, context: Dict[str, Any]) -> bool:
        """检查规则是否匹配"""
        try:
            if asyncio.iscoroutinefunction(self.condition):
                return await self.condition(query, context)
            else:
                return self.condition(query, context)
        except Exception as e:
            logger.warning(f"路由规则 {self.name} 匹配时发生错误: {e}")
            return False


class QueryRoutingEngine:
    """查询路由引擎主类"""
    
    def __init__(self):
        # 路由策略注册表
        self.strategies: Dict[str, 'IRoutingStrategy'] = {}
        
        # 查询处理器注册表
        self.handlers: Dict[str, 'IQueryHandler'] = {}
        
        # 路由规则列表（按优先级排序）
        self.rules: List[RoutingRule] = []
        
        # 配置
        self.default_strategy = "llm_intent"
        self.fallback_handler = "chat_handler"
        self.enable_rules = True
        self.enable_monitoring = True
        
        # 监控数据
        self.routing_stats = {
            "total_routes": 0,
            "strategy_usage": {},
            "handler_usage": {},
            "rule_matches": {},
            "average_confidence": 0.0,
            "last_reset": datetime.now()
        }
        
        logger.info("QueryRoutingEngine initialized")
        
    def register_strategy(self, name: str, strategy: 'IRoutingStrategy') -> None:
        """注册路由策略"""
        if not hasattr(strategy, 'decide_route'):
            raise ValueError(f"策略 {name} 必须实现 decide_route 方法")
            
        self.strategies[name] = strategy
        logger.info(f"路由策略已注册: {name}")
        
    def register_handler(self, name: str, handler: 'IQueryHandler') -> None:
        """注册查询处理器"""
        if not hasattr(handler, 'handle'):
            raise ValueError(f"处理器 {name} 必须实现 handle 方法")
            
        self.handlers[name] = handler
        logger.info(f"查询处理器已注册: {name}")
        
    def add_rule(self, rule: RoutingRule) -> None:
        """添加路由规则"""
        self.rules.append(rule)
        # 按优先级重新排序（优先级高的在前）
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info(f"路由规则已添加: {rule.name} (priority: {rule.priority})")
        
    def remove_rule(self, rule_name: str) -> bool:
        """移除路由规则"""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                logger.info(f"路由规则已移除: {rule_name}")
                return True
        return False
        
    async def route(self, query: str, context: Dict[str, Any] = None) -> RoutingResult:
        """主路由逻辑"""
        start_time = asyncio.get_event_loop().time()
        context = context or {}
        
        try:
            self._update_stats("total_routes")
            
            # 1. 规则匹配（最高优先级）
            if self.enable_rules:
                for rule in self.rules:
                    if await rule.matches(query, context):
                        decision = RouteDecision(
                            handler_name=rule.handler_name,
                            confidence=1.0,  # 规则匹配给最高置信度
                            metadata={
                                "route_type": "rule",
                                "rule_name": rule.name,
                                "rule_description": rule.description
                            }
                        )
                        
                        self._update_stats("rule_matches", rule.name)
                        return await self._execute_route(decision, query, context, start_time)
            
            # 2. 策略路由
            strategy = self.strategies.get(self.default_strategy)
            if strategy:
                try:
                    route_decision = await strategy.decide_route(query, context)
                    if route_decision.confidence > 0.1:  # 最低置信度阈值
                        route_decision.metadata["route_type"] = "strategy"
                        route_decision.metadata["strategy_name"] = strategy.strategy_name
                        
                        self._update_stats("strategy_usage", strategy.strategy_name)
                        return await self._execute_route(route_decision, query, context, start_time)
                        
                except Exception as e:
                    logger.error(f"策略路由失败: {e}")
            
            # 3. 回退处理
            fallback_decision = RouteDecision(
                handler_name=self.fallback_handler,
                confidence=0.1,
                metadata={
                    "route_type": "fallback",
                    "reason": "no_strategy_match"
                }
            )
            
            return await self._execute_route(fallback_decision, query, context, start_time)
            
        except Exception as e:
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error(f"路由处理失败: {e}")
            
            # 返回错误结果
            error_decision = RouteDecision(
                handler_name=self.fallback_handler,
                confidence=0.0,
                metadata={"route_type": "error", "error": str(e)}
            )
            
            return RoutingResult(
                decision=error_decision,
                handler=self.handlers.get(self.fallback_handler),
                execution_time_ms=execution_time,
                success=False,
                error=str(e)
            )
            
    async def _execute_route(
        self,
        decision: RouteDecision,
        query: str,
        context: Dict[str, Any],
        start_time: float
    ) -> RoutingResult:
        """执行路由决策"""
        handler = self.handlers.get(decision.handler_name)
        
        if not handler:
            logger.warning(f"处理器未找到: {decision.handler_name}, 使用回退处理器")
            handler = self.handlers.get(self.fallback_handler)
            decision.handler_name = self.fallback_handler
            decision.metadata["fallback_reason"] = "handler_not_found"
            
        execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # 更新统计信息
        self._update_stats("handler_usage", decision.handler_name)
        if self.enable_monitoring:
            self._update_confidence_stats(decision.confidence)
            
        logger.debug(
            f"路由决策: query='{query[:50]}...', "
            f"handler={decision.handler_name}, "
            f"confidence={decision.confidence:.3f}, "
            f"time={execution_time:.1f}ms"
        )
        
        return RoutingResult(
            decision=decision,
            handler=handler,
            execution_time_ms=execution_time,
            success=True
        )
        
    def _update_stats(self, stat_type: str, key: str = None) -> None:
        """更新统计信息"""
        if not self.enable_monitoring:
            return
            
        if stat_type == "total_routes":
            self.routing_stats["total_routes"] += 1
        elif key:
            if stat_type not in self.routing_stats:
                self.routing_stats[stat_type] = {}
            self.routing_stats[stat_type][key] = self.routing_stats[stat_type].get(key, 0) + 1
            
    def _update_confidence_stats(self, confidence: float) -> None:
        """更新置信度统计"""
        total_routes = self.routing_stats["total_routes"]
        current_avg = self.routing_stats["average_confidence"]
        
        # 计算新的平均置信度
        self.routing_stats["average_confidence"] = (
            (current_avg * (total_routes - 1) + confidence) / total_routes
        )
        
    def get_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        return {
            **self.routing_stats,
            "registered_strategies": list(self.strategies.keys()),
            "registered_handlers": list(self.handlers.keys()),
            "active_rules": [
                {
                    "name": rule.name,
                    "priority": rule.priority,
                    "description": rule.description
                }
                for rule in self.rules
            ],
            "configuration": {
                "default_strategy": self.default_strategy,
                "fallback_handler": self.fallback_handler,
                "enable_rules": self.enable_rules,
                "enable_monitoring": self.enable_monitoring
            }
        }
        
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.routing_stats = {
            "total_routes": 0,
            "strategy_usage": {},
            "handler_usage": {},
            "rule_matches": {},
            "average_confidence": 0.0,
            "last_reset": datetime.now()
        }
        logger.info("路由统计信息已重置")
        
    def set_default_strategy(self, strategy_name: str) -> bool:
        """设置默认路由策略"""
        if strategy_name in self.strategies:
            self.default_strategy = strategy_name
            logger.info(f"默认策略已设置为: {strategy_name}")
            return True
        else:
            logger.warning(f"策略不存在: {strategy_name}")
            return False
            
    def set_fallback_handler(self, handler_name: str) -> bool:
        """设置回退处理器"""
        if handler_name in self.handlers:
            self.fallback_handler = handler_name
            logger.info(f"回退处理器已设置为: {handler_name}")
            return True
        else:
            logger.warning(f"处理器不存在: {handler_name}")
            return False
            
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "engine_status": "healthy",
            "strategies_count": len(self.strategies),
            "handlers_count": len(self.handlers),
            "rules_count": len(self.rules),
            "total_routes_processed": self.routing_stats["total_routes"]
        }
        
        # 检查关键组件
        if self.default_strategy not in self.strategies:
            health_status["engine_status"] = "degraded"
            health_status["issues"] = health_status.get("issues", [])
            health_status["issues"].append(f"默认策略不存在: {self.default_strategy}")
            
        if self.fallback_handler not in self.handlers:
            health_status["engine_status"] = "degraded"
            health_status["issues"] = health_status.get("issues", [])
            health_status["issues"].append(f"回退处理器不存在: {self.fallback_handler}")
            
        return health_status