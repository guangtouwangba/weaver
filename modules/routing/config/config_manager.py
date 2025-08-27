"""
Keyword Configuration Manager

关键词配置管理器，提供配置热重载和验证功能。
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .keyword_config import KeywordConfigLoader

logger = logging.getLogger(__name__)


class KeywordConfigManager:
    """关键词配置管理器"""
    
    def __init__(self, routing_engine: Optional['QueryRoutingEngine'] = None):
        self.routing_engine = routing_engine
        self.config_loader = KeywordConfigLoader()
        self.last_reload_time: Optional[datetime] = None
        self.reload_count = 0
        
    async def initialize(self) -> Dict[str, Any]:
        """初始化配置管理器"""
        try:
            await self.config_loader.load_config()
            await self.config_loader.load_domain_config()
            
            self.last_reload_time = datetime.now()
            
            return {
                "success": True,
                "message": "配置管理器初始化成功",
                "handlers_count": len(self.config_loader.handlers_config),
                "initialization_time": self.last_reload_time.isoformat()
            }
        except Exception as e:
            logger.error(f"配置管理器初始化失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def reload_keyword_config(self) -> Dict[str, Any]:
        """重新加载关键词配置"""
        try:
            # 重新加载配置
            await self.config_loader.reload_config()
            
            # 如果有路由引擎，通知相关策略重新加载
            if self.routing_engine:
                configurable_strategy = self.routing_engine.strategies.get("configurable_keyword")
                if configurable_strategy and hasattr(configurable_strategy, 'reload_config'):
                    await configurable_strategy.reload_config()
            
            self.last_reload_time = datetime.now()
            self.reload_count += 1
            
            logger.info(f"关键词配置重新加载成功 (第{self.reload_count}次)")
            
            return {
                "success": True,
                "message": "关键词配置重新加载成功",
                "handlers_count": len(self.config_loader.handlers_config),
                "reload_count": self.reload_count,
                "reload_time": self.last_reload_time.isoformat()
            }
        except Exception as e:
            logger.error(f"关键词配置重新加载失败: {e}")
            return {
                "success": False,
                "message": f"配置重新加载失败: {str(e)}",
                "error": str(e)
            }
    
    async def validate_config(self, config_file: str = None) -> Dict[str, Any]:
        """
        验证配置文件
        
        Args:
            config_file: 指定配置文件，如果为None则验证当前配置
        """
        try:
            if config_file:
                # 验证指定的配置文件
                temp_loader = KeywordConfigLoader(self.config_loader.config_dir)
                await temp_loader.load_config(config_file)
                validation_result = temp_loader.validate_config()
            else:
                # 验证当前配置
                validation_result = self.config_loader.validate_config()
                
            return {
                "success": True,
                "validation": validation_result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    async def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置详情"""
        try:
            config_summary = self.config_loader.get_config_summary()
            
            return {
                "success": True,
                "config": config_summary,
                "metadata": {
                    "last_reload_time": self.last_reload_time.isoformat() if self.last_reload_time else None,
                    "reload_count": self.reload_count,
                    "config_dir": str(self.config_loader.config_dir)
                }
            }
        except Exception as e:
            logger.error(f"获取当前配置失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def get_handler_details(self, handler_name: str) -> Dict[str, Any]:
        """获取特定处理器的详细配置"""
        if handler_name not in self.config_loader.handlers_config:
            return {
                "success": False,
                "error": f"处理器不存在: {handler_name}"
            }
            
        config = self.config_loader.handlers_config[handler_name]
        
        return {
            "success": True,
            "handler": {
                "name": config.name,
                "description": config.description,
                "weight": config.weight,
                "patterns": {
                    "exact_keywords": config.patterns.exact_keywords,
                    "prefix_keywords": config.patterns.prefix_keywords,
                    "suffix_keywords": config.patterns.suffix_keywords,
                    "regex_patterns": config.patterns.regex_patterns,
                    "command_patterns": config.patterns.command_patterns,
                    "emotional_keywords": config.patterns.emotional_keywords,
                    "greeting_patterns": config.patterns.greeting_patterns
                },
                "statistics": {
                    "total_keywords": len(config.patterns.get_all_keywords()),
                    "total_patterns": config.patterns.get_pattern_count(),
                    "pattern_breakdown": {
                        "exact": len(config.patterns.exact_keywords),
                        "prefix": len(config.patterns.prefix_keywords),
                        "suffix": len(config.patterns.suffix_keywords),
                        "regex": len(config.patterns.regex_patterns),
                        "command": len(config.patterns.command_patterns),
                        "emotional": len(config.patterns.emotional_keywords),
                        "greeting": len(config.patterns.greeting_patterns)
                    }
                }
            }
        }
    
    async def test_query_matching(self, query: str) -> Dict[str, Any]:
        """
        测试查询匹配
        
        Args:
            query: 测试查询文本
            
        Returns:
            Dict[str, Any]: 匹配结果
        """
        try:
            if not self.routing_engine:
                return {
                    "success": False,
                    "error": "路由引擎未设置，无法进行匹配测试"
                }
                
            # 获取配置化关键词策略
            strategy = self.routing_engine.strategies.get("configurable_keyword")
            if not strategy:
                return {
                    "success": False,
                    "error": "配置化关键词策略未找到"
                }
            
            # 执行路由决策
            decision = await strategy.decide_route(query, {})
            
            return {
                "success": True,
                "query": query,
                "decision": decision.to_dict(),
                "test_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"查询匹配测试失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def update_handler_weight(self, handler_name: str, new_weight: float) -> Dict[str, Any]:
        """
        更新处理器权重
        
        Args:
            handler_name: 处理器名称
            new_weight: 新权重值
        """
        if handler_name not in self.config_loader.handlers_config:
            return {
                "success": False,
                "error": f"处理器不存在: {handler_name}"
            }
            
        if new_weight <= 0:
            return {
                "success": False,
                "error": "权重值必须大于0"
            }
        
        try:
            old_weight = self.config_loader.handlers_config[handler_name].weight
            self.config_loader.handlers_config[handler_name].weight = new_weight
            
            # 如果有路由引擎，通知策略更新
            if self.routing_engine:
                configurable_strategy = self.routing_engine.strategies.get("configurable_keyword")
                if configurable_strategy and hasattr(configurable_strategy, 'reload_config'):
                    await configurable_strategy.reload_config()
            
            logger.info(f"处理器 {handler_name} 权重从 {old_weight} 更新为 {new_weight}")
            
            return {
                "success": True,
                "message": f"处理器权重已更新",
                "handler_name": handler_name,
                "old_weight": old_weight,
                "new_weight": new_weight,
                "update_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"更新处理器权重失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def get_statistics(self) -> Dict[str, Any]:
        """获取配置管理器统计信息"""
        return {
            "success": True,
            "statistics": {
                "total_handlers": len(self.config_loader.handlers_config),
                "total_keywords": sum(
                    len(config.patterns.get_all_keywords()) 
                    for config in self.config_loader.handlers_config.values()
                ),
                "total_patterns": sum(
                    config.patterns.get_pattern_count() 
                    for config in self.config_loader.handlers_config.values()
                ),
                "reload_count": self.reload_count,
                "last_reload_time": self.last_reload_time.isoformat() if self.last_reload_time else None,
                "handlers_breakdown": {
                    name: {
                        "weight": config.weight,
                        "keywords_count": len(config.patterns.get_all_keywords()),
                        "patterns_count": config.patterns.get_pattern_count()
                    }
                    for name, config in self.config_loader.handlers_config.items()
                },
                "global_settings": self.config_loader.global_settings
            }
        }