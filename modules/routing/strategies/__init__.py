"""
Routing Strategies

各种查询路由策略的实现。
"""

from .base import IRoutingStrategy, IQueryHandler

try:
    from .semantic_router_strategy import SemanticRouterStrategy
    SEMANTIC_ROUTER_AVAILABLE = True
except ImportError:
    SEMANTIC_ROUTER_AVAILABLE = False

__all__ = [
    "IRoutingStrategy",
    "IQueryHandler",
]

if SEMANTIC_ROUTER_AVAILABLE:
    __all__.append("SemanticRouterStrategy")