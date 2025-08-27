"""
Keyword Configuration Loader

关键词配置加载器，支持从YAML文件加载关键词路由规则。
"""

import yaml
import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class KeywordPattern:
    """关键词模式配置"""
    exact_keywords: List[str] = field(default_factory=list)
    prefix_keywords: List[str] = field(default_factory=list)
    suffix_keywords: List[str] = field(default_factory=list)
    regex_patterns: List[str] = field(default_factory=list)
    command_patterns: List[str] = field(default_factory=list)
    emotional_keywords: List[str] = field(default_factory=list)
    greeting_patterns: List[str] = field(default_factory=list)
    
    def get_all_keywords(self) -> List[str]:
        """获取所有关键词"""
        return (
            self.exact_keywords + 
            self.prefix_keywords + 
            self.suffix_keywords +
            self.emotional_keywords +
            self.greeting_patterns
        )
    
    def get_pattern_count(self) -> int:
        """获取模式总数"""
        return (
            len(self.exact_keywords) +
            len(self.prefix_keywords) +
            len(self.suffix_keywords) +
            len(self.regex_patterns) +
            len(self.command_patterns) +
            len(self.emotional_keywords) +
            len(self.greeting_patterns)
        )


@dataclass
class HandlerConfig:
    """处理器配置"""
    name: str
    description: str
    weight: float
    patterns: KeywordPattern
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "weight": self.weight,
            "pattern_count": self.patterns.get_pattern_count(),
            "keywords_count": len(self.patterns.get_all_keywords())
        }


class KeywordConfigLoader:
    """关键词配置加载器"""
    
    def __init__(self, config_dir: str = "config/routing"):
        self.config_dir = Path(config_dir)
        self.handlers_config: Dict[str, HandlerConfig] = {}
        self.global_settings: Dict[str, Any] = {}
        self.domain_config: Dict[str, Any] = {}
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"KeywordConfigLoader initialized with config_dir: {self.config_dir}")
        
    async def load_config(self, config_file: str = "keywords.yaml") -> None:
        """
        加载关键词配置文件
        
        Args:
            config_file: 配置文件名
        """
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}, 将使用默认配置")
            await self._create_default_config(config_path)
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            if not config:
                logger.warning(f"配置文件为空: {config_path}")
                return
                
            # 加载全局设置
            self.global_settings = config.get('global_settings', {})
            logger.info(f"全局设置已加载: {self.global_settings}")
            
            # 加载处理器配置
            routing_keywords = config.get('routing_keywords', {})
            self.handlers_config.clear()
            
            for handler_name, handler_config in routing_keywords.items():
                patterns_data = handler_config.get('patterns', {})
                
                # 创建KeywordPattern对象
                patterns = KeywordPattern(
                    exact_keywords=patterns_data.get('exact_keywords', []),
                    prefix_keywords=patterns_data.get('prefix_keywords', []),
                    suffix_keywords=patterns_data.get('suffix_keywords', []),
                    regex_patterns=patterns_data.get('regex_patterns', []),
                    command_patterns=patterns_data.get('command_patterns', []),
                    emotional_keywords=patterns_data.get('emotional_keywords', []),
                    greeting_patterns=patterns_data.get('greeting_patterns', [])
                )
                
                self.handlers_config[handler_name] = HandlerConfig(
                    name=handler_config.get('name', handler_name),
                    description=handler_config.get('description', ''),
                    weight=handler_config.get('weight', 1.0),
                    patterns=patterns
                )
                
            logger.info(f"已加载 {len(self.handlers_config)} 个处理器配置")
            
        except yaml.YAMLError as e:
            logger.error(f"YAML解析错误: {e}")
            raise ValueError(f"配置文件格式错误: {config_file}")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise
            
    async def load_domain_config(self, domain_file: str = "domain_keywords.yaml") -> None:
        """
        加载领域特定配置
        
        Args:
            domain_file: 领域配置文件名
        """
        domain_path = self.config_dir / domain_file
        
        if not domain_path.exists():
            logger.info(f"领域配置文件不存在: {domain_path}")
            return
            
        try:
            with open(domain_path, 'r', encoding='utf-8') as f:
                self.domain_config = yaml.safe_load(f) or {}
                
            logger.info(f"已加载领域配置，包含 {len(self.domain_config.get('domain_keywords', {}))} 个领域")
            
        except Exception as e:
            logger.error(f"加载领域配置失败: {e}")
            
    async def load_multilang_config(self, multilang_file: str = "keywords_multilang.yaml") -> Dict[str, Any]:
        """
        加载多语言配置
        
        Args:
            multilang_file: 多语言配置文件名
            
        Returns:
            Dict[str, Any]: 多语言配置数据
        """
        multilang_path = self.config_dir / multilang_file
        
        if not multilang_path.exists():
            logger.info(f"多语言配置文件不存在: {multilang_path}")
            return {}
            
        try:
            with open(multilang_path, 'r', encoding='utf-8') as f:
                multilang_config = yaml.safe_load(f) or {}
                
            logger.info(f"已加载多语言配置")
            return multilang_config
            
        except Exception as e:
            logger.error(f"加载多语言配置失败: {e}")
            return {}
            
    async def reload_config(self) -> None:
        """热重载配置"""
        try:
            await self.load_config()
            await self.load_domain_config()
            logger.info("配置已成功重新加载")
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            raise
            
    async def _create_default_config(self, config_path: Path) -> None:
        """创建默认配置文件"""
        default_config = {
            'global_settings': {
                'case_sensitive': False,
                'enable_fuzzy_matching': True,
                'fuzzy_threshold': 0.8,
                'min_confidence': 0.3,
                'default_handler': 'chat_handler'
            },
            'routing_keywords': {
                'rag_handler': {
                    'name': 'RAG知识查询',
                    'description': '需要从知识库检索信息的查询',
                    'weight': 1.0,
                    'patterns': {
                        'exact_keywords': ['什么是', '介绍一下', '解释', '查找', '搜索', '关于'],
                        'prefix_keywords': ['如何', '怎么', '为什么'],
                        'suffix_keywords': ['是什么', '怎么样', '的定义', '的概念'],
                        'regex_patterns': ['.*的定义$', '.*的概念$', '.*的原理$']
                    }
                },
                'tool_handler': {
                    'name': '工具调用',
                    'description': '需要调用外部工具或API的请求',
                    'weight': 0.9,
                    'patterns': {
                        'exact_keywords': ['计算', '天气', '提醒', '翻译', '打开', '播放'],
                        'prefix_keywords': ['帮我计算', '查询天气', '设置提醒'],
                        'command_patterns': ['/calc', '/weather', '/remind']
                    }
                },
                'system_handler': {
                    'name': '系统命令',
                    'description': '系统配置和管理命令',
                    'weight': 0.8,
                    'patterns': {
                        'exact_keywords': ['清除历史', '重置对话', '设置', '配置', '帮助', '退出'],
                        'prefix_keywords': ['清除', '重置', '删除'],
                        'command_patterns': ['/clear', '/reset', '/help', '/settings']
                    }
                },
                'chat_handler': {
                    'name': '闲聊对话',
                    'description': '普通对话和闲聊',
                    'weight': 0.7,
                    'patterns': {
                        'exact_keywords': ['你好', '再见', '谢谢', '不客气'],
                        'emotional_keywords': ['开心', '难过', '生气', '无聊'],
                        'greeting_patterns': ['早上好', '下午好', '晚上好']
                    }
                }
            }
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, ensure_ascii=False, indent=2)
            logger.info(f"已创建默认配置文件: {config_path}")
        except Exception as e:
            logger.error(f"创建默认配置文件失败: {e}")
            
    def validate_config(self) -> Dict[str, Any]:
        """
        验证当前配置
        
        Returns:
            Dict[str, Any]: 验证结果
        """
        issues = []
        warnings = []
        
        # 检查处理器配置
        if not self.handlers_config:
            issues.append("没有配置任何处理器")
            
        for handler_name, config in self.handlers_config.items():
            if config.patterns.get_pattern_count() == 0:
                warnings.append(f"处理器 {handler_name} 没有配置任何模式")
                
            if config.weight <= 0:
                issues.append(f"处理器 {handler_name} 的权重必须大于0")
                
        # 检查全局设置
        default_handler = self.global_settings.get('default_handler')
        if default_handler and default_handler not in self.handlers_config:
            issues.append(f"默认处理器 {default_handler} 不存在")
            
        # 检查正则表达式
        for handler_name, config in self.handlers_config.items():
            for pattern in config.patterns.regex_patterns:
                try:
                    re.compile(pattern)
                except re.error as e:
                    issues.append(f"处理器 {handler_name} 的正则表达式无效: {pattern} - {e}")
                    
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "handlers_count": len(self.handlers_config),
            "global_settings": self.global_settings
        }
        
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "handlers": {
                name: config.to_dict() 
                for name, config in self.handlers_config.items()
            },
            "global_settings": self.global_settings,
            "total_keywords": sum(
                len(config.patterns.get_all_keywords()) 
                for config in self.handlers_config.values()
            ),
            "total_patterns": sum(
                config.patterns.get_pattern_count() 
                for config in self.handlers_config.values()
            )
        }