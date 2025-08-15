"""
路由器基础接口
智能查询路由和服务选择
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from enum import Enum


class QueryType(Enum):
    """查询类型枚举"""
    FACTUAL = "factual"  # 事实性查询
    ANALYTICAL = "analytical"  # 分析性查询
    CREATIVE = "creative"  # 创作性查询
    CONVERSATIONAL = "conversational"  # 对话性查询
    SEARCH = "search"  # 搜索性查询


class ServiceType(Enum):
    """服务类型枚举"""
    SEMANTIC_RETRIEVAL = "semantic_retrieval"
    KEYWORD_RETRIEVAL = "keyword_retrieval"
    HYBRID_RETRIEVAL = "hybrid_retrieval"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    GENERATIVE = "generative"


class BaseRouter(ABC):
    """路由器基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化路由器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.services: Dict[str, Any] = {}
        self.service_weights: Dict[str, float] = self.config.get('service_weights', {})
    
    @abstractmethod
    async def route(self, 
                   query: str, 
                   context: Optional[Dict[str, Any]] = None) -> str:
        """
        决定使用哪个服务处理查询
        
        Args:
            query: 查询文本
            context: 查询上下文
            
        Returns:
            str: 选择的服务名称
        """
        pass
    
    def register_service(self, name: str, service: Any) -> None:
        """
        注册服务
        
        Args:
            name: 服务名称
            service: 服务实例
        """
        self.services[name] = service
    
    def unregister_service(self, name: str) -> bool:
        """
        注销服务
        
        Args:
            name: 服务名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self.services:
            del self.services[name]
            return True
        return False
    
    def get_available_services(self) -> List[str]:
        """
        获取可用服务列表
        
        Returns:
            List[str]: 服务名称列表
        """
        return list(self.services.keys())
    
    def get_service(self, name: str) -> Optional[Any]:
        """
        获取服务实例
        
        Args:
            name: 服务名称
            
        Returns:
            Optional[Any]: 服务实例
        """
        return self.services.get(name)
    
    def analyze_query_type(self, query: str) -> QueryType:
        """
        分析查询类型
        
        Args:
            query: 查询文本
            
        Returns:
            QueryType: 查询类型
        """
        query_lower = query.lower()
        
        # 简单的关键词匹配分类
        if any(word in query_lower for word in ['what', 'who', 'when', 'where', 'how many']):
            return QueryType.FACTUAL
        elif any(word in query_lower for word in ['why', 'how', 'analyze', 'compare', 'explain']):
            return QueryType.ANALYTICAL
        elif any(word in query_lower for word in ['create', 'generate', 'write', 'make']):
            return QueryType.CREATIVE
        elif any(word in query_lower for word in ['find', 'search', 'look for']):
            return QueryType.SEARCH
        else:
            return QueryType.CONVERSATIONAL
    
    def get_query_complexity(self, query: str) -> float:
        """
        评估查询复杂度
        
        Args:
            query: 查询文本
            
        Returns:
            float: 复杂度分数 (0-1)
        """
        # 简单的复杂度评估
        factors = []
        
        # 长度因子
        length_factor = min(len(query.split()) / 20, 1.0)
        factors.append(length_factor)
        
        # 复杂词汇因子
        complex_words = ['analyze', 'compare', 'synthesize', 'evaluate', 'relationship']
        complex_factor = sum(1 for word in complex_words if word in query.lower()) / len(complex_words)
        factors.append(complex_factor)
        
        # 问号数量（多问题）
        question_factor = min(query.count('?') / 3, 1.0)
        factors.append(question_factor)
        
        return sum(factors) / len(factors)


class RuleBasedRouter(BaseRouter):
    """基于规则的路由器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.routing_rules = self.config.get('routing_rules', self._default_routing_rules())
    
    async def route(self, 
                   query: str, 
                   context: Optional[Dict[str, Any]] = None) -> str:
        """基于规则的路由决策"""
        
        # 分析查询特征
        query_type = self.analyze_query_type(query)
        complexity = self.get_query_complexity(query)
        query_length = len(query.split())
        
        # 应用路由规则
        for rule in self.routing_rules:
            if self._match_rule(rule, query_type, complexity, query_length, context):
                service_name = rule['service']
                if service_name in self.services:
                    return service_name
        
        # 默认服务
        return self.routing_rules[-1]['service'] if self.routing_rules else 'semantic_retrieval'
    
    def _match_rule(self, 
                   rule: Dict[str, Any],
                   query_type: QueryType,
                   complexity: float,
                   query_length: int,
                   context: Optional[Dict[str, Any]]) -> bool:
        """检查规则是否匹配"""
        
        # 检查查询类型
        if 'query_types' in rule and query_type not in rule['query_types']:
            return False
        
        # 检查复杂度范围
        if 'complexity_range' in rule:
            min_complexity, max_complexity = rule['complexity_range']
            if not (min_complexity <= complexity <= max_complexity):
                return False
        
        # 检查查询长度
        if 'length_range' in rule:
            min_length, max_length = rule['length_range']
            if not (min_length <= query_length <= max_length):
                return False
        
        # 检查上下文条件
        if 'context_conditions' in rule and context:
            for key, expected_value in rule['context_conditions'].items():
                if context.get(key) != expected_value:
                    return False
        
        return True
    
    def _default_routing_rules(self) -> List[Dict[str, Any]]:
        """默认路由规则"""
        return [
            {
                'name': 'simple_factual',
                'query_types': [QueryType.FACTUAL, QueryType.SEARCH],
                'complexity_range': [0.0, 0.3],
                'service': 'semantic_retrieval'
            },
            {
                'name': 'complex_analytical',
                'query_types': [QueryType.ANALYTICAL],
                'complexity_range': [0.5, 1.0],
                'service': 'hybrid_retrieval'
            },
            {
                'name': 'creative_generative',
                'query_types': [QueryType.CREATIVE],
                'service': 'generative'
            },
            {
                'name': 'long_queries',
                'length_range': [15, 1000],
                'service': 'hybrid_retrieval'
            },
            {
                'name': 'default',
                'service': 'semantic_retrieval'
            }
        ]


class MLRouter(BaseRouter):
    """基于机器学习的路由器（预留实现）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.model = None  # 这里可以加载预训练的分类模型
        self.feature_extractor = None
    
    async def route(self, 
                   query: str, 
                   context: Optional[Dict[str, Any]] = None) -> str:
        """基于ML模型的路由决策"""
        
        # 目前回退到规则路由
        # 实际实现中可以：
        # 1. 提取查询特征向量
        # 2. 使用训练好的分类器预测最佳服务
        # 3. 考虑服务负载和性能指标
        
        fallback_router = RuleBasedRouter(self.config)
        return await fallback_router.route(query, context)
    
    def extract_features(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[float]:
        """提取查询特征向量"""
        features = []
        
        # 文本特征
        features.extend([
            len(query),
            len(query.split()),
            query.count('?'),
            query.count(','),
        ])
        
        # 语义特征（需要嵌入模型）
        # features.extend(self.get_query_embedding(query))
        
        # 上下文特征
        if context:
            features.append(len(context))
        else:
            features.append(0)
        
        return features


class LoadBalancingRouter(BaseRouter):
    """负载均衡路由器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.service_loads: Dict[str, int] = {}
        self.max_load_per_service = self.config.get('max_load_per_service', 100)
    
    async def route(self, 
                   query: str, 
                   context: Optional[Dict[str, Any]] = None) -> str:
        """考虑负载均衡的路由决策"""
        
        # 获取基础路由决策
        base_router = RuleBasedRouter(self.config)
        preferred_service = await base_router.route(query, context)
        
        # 检查首选服务的负载
        current_load = self.service_loads.get(preferred_service, 0)
        
        if current_load < self.max_load_per_service:
            self._increment_load(preferred_service)
            return preferred_service
        
        # 寻找负载较低的替代服务
        available_services = [
            service for service, load in self.service_loads.items()
            if load < self.max_load_per_service
        ]
        
        if available_services:
            # 选择负载最低的服务
            selected_service = min(available_services, 
                                 key=lambda s: self.service_loads.get(s, 0))
            self._increment_load(selected_service)
            return selected_service
        
        # 如果所有服务都满载，仍选择首选服务
        return preferred_service
    
    def _increment_load(self, service_name: str) -> None:
        """增加服务负载计数"""
        self.service_loads[service_name] = self.service_loads.get(service_name, 0) + 1
    
    def decrease_load(self, service_name: str) -> None:
        """减少服务负载计数"""
        if service_name in self.service_loads and self.service_loads[service_name] > 0:
            self.service_loads[service_name] -= 1
    
    def get_service_loads(self) -> Dict[str, int]:
        """获取所有服务的负载状态"""
        return self.service_loads.copy()