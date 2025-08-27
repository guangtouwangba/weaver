"""
Base Interfaces for Routing Strategies and Query Handlers

路由策略和查询处理器的基础接口定义。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from modules.routing.engine import RouteDecision


class IRoutingStrategy(ABC):
    """路由策略接口"""
    
    @abstractmethod
    async def decide_route(self, query: str, context: Dict[str, Any]) -> RouteDecision:
        """
        决定查询的路由目标
        
        Args:
            query: 用户查询文本
            context: 上下文信息（对话历史、用户信息等）
            
        Returns:
            RouteDecision: 路由决策结果
        """
        pass
        
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """策略名称"""
        pass
        
    async def initialize(self) -> None:
        """初始化策略（可选实现）"""
        pass
        
    async def cleanup(self) -> None:
        """清理资源（可选实现）"""
        pass


class IQueryHandler(ABC):
    """查询处理器接口"""
    
    @abstractmethod
    async def handle(
        self,
        query: str,
        context: Dict[str, Any],
        route_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        处理查询请求
        
        Args:
            query: 用户查询文本
            context: 上下文信息
            route_metadata: 路由决策的元数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        pass
        
    @property
    @abstractmethod
    def handler_name(self) -> str:
        """处理器名称"""
        pass
        
    async def initialize(self) -> None:
        """初始化处理器（可选实现）"""
        pass
        
    async def cleanup(self) -> None:
        """清理资源（可选实现）"""
        pass
        
    async def health_check(self) -> Dict[str, Any]:
        """健康检查（可选实现）"""
        return {"status": "healthy", "handler": self.handler_name}