"""
Configurable Keyword Routing Strategy

基于配置文件的关键词路由策略，支持多种匹配模式和热重载。
"""

import re
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

from .base import IRoutingStrategy
from ..engine import RouteDecision
from ..config.keyword_config import KeywordConfigLoader, HandlerConfig

# 尝试导入模糊匹配库
try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    fuzz = None

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """匹配结果"""
    score: float
    match_type: str
    matched_text: str
    confidence: float


class ConfigurableKeywordStrategy(IRoutingStrategy):
    """基于配置文件的关键词路由策略"""
    
    def __init__(self, config_loader: KeywordConfigLoader):
        self.config_loader = config_loader
        self.compiled_regexes: Dict[str, List[re.Pattern]] = {}
        self._initialized = False
        
        if not FUZZY_AVAILABLE:
            logger.warning("模糊匹配库未安装，模糊匹配功能将被禁用")
        
    async def initialize(self) -> None:
        """初始化策略"""
        if self._initialized:
            return
            
        try:
            await self.config_loader.load_config()
            await self._compile_regex_patterns()
            self._initialized = True
            logger.info("ConfigurableKeywordStrategy 初始化完成")
        except Exception as e:
            logger.error(f"ConfigurableKeywordStrategy 初始化失败: {e}")
            raise
            
    async def _compile_regex_patterns(self) -> None:
        """预编译正则表达式"""
        self.compiled_regexes.clear()
        
        for handler_name, config in self.config_loader.handlers_config.items():
            if config.patterns.regex_patterns:
                compiled_patterns = []
                for pattern in config.patterns.regex_patterns:
                    try:
                        flags = re.IGNORECASE if not self.config_loader.global_settings.get('case_sensitive', False) else 0
                        compiled = re.compile(pattern, flags)
                        compiled_patterns.append(compiled)
                    except re.error as e:
                        logger.error(f"正则表达式编译失败: {pattern}, 错误: {e}")
                        
                if compiled_patterns:
                    self.compiled_regexes[handler_name] = compiled_patterns
                    
    async def decide_route(self, query: str, context: Dict[str, Any]) -> RouteDecision:
        """基于配置的关键词匹配路由决策"""
        if not self._initialized:
            await self.initialize()
            
        query_processed = self._preprocess_query(query)
        
        handler_scores = {}
        match_details = {}
        
        # 为每个处理器计算得分
        for handler_name, config in self.config_loader.handlers_config.items():
            score, details = await self._calculate_handler_score(
                query_processed, query, config
            )
            
            if score > 0:
                # 应用权重
                final_score = score * config.weight
                handler_scores[handler_name] = final_score
                match_details[handler_name] = details
        
        # 选择最高分的处理器
        if handler_scores:
            best_handler_item = max(handler_scores.items(), key=lambda x: x[1])
            best_handler, best_score = best_handler_item
            
            # 归一化置信度
            confidence = min(best_score, 1.0)
            
            # 检查最小置信度阈值
            min_confidence = self.config_loader.global_settings.get('min_confidence', 0.3)
            if confidence < min_confidence:
                return self._create_fallback_decision(query, match_details, "low_confidence")
                
            return RouteDecision(
                handler_name=best_handler,
                confidence=confidence,
                metadata={
                    "matched_patterns": match_details[best_handler],
                    "all_scores": handler_scores,
                    "strategy": "configurable_keyword",
                    "query_processed": query_processed
                }
            )
        
        return self._create_fallback_decision(query, match_details, "no_matches")
    
    async def _calculate_handler_score(
        self, 
        query_processed: str, 
        original_query: str,
        config: HandlerConfig
    ) -> Tuple[float, Dict[str, Any]]:
        """计算处理器得分"""
        patterns = config.patterns
        total_score = 0.0
        match_details = {
            "matches": [],
            "match_types": [],
            "match_scores": {}
        }
        
        # 1. 精确关键词匹配 (权重最高)
        exact_matches = self._match_keywords(
            patterns.exact_keywords, query_processed, "exact"
        )
        for match in exact_matches:
            total_score += 1.0
            match_details["matches"].append(match.matched_text)
            match_details["match_types"].append("exact")
            match_details["match_scores"]["exact"] = match_details["match_scores"].get("exact", 0) + match.score
        
        # 2. 前缀匹配
        prefix_matches = self._match_prefixes(patterns.prefix_keywords, query_processed)
        for match in prefix_matches:
            total_score += 0.8
            match_details["matches"].append(match.matched_text)
            match_details["match_types"].append("prefix")
            match_details["match_scores"]["prefix"] = match_details["match_scores"].get("prefix", 0) + match.score
        
        # 3. 后缀匹配
        suffix_matches = self._match_suffixes(patterns.suffix_keywords, query_processed)
        for match in suffix_matches:
            total_score += 0.8
            match_details["matches"].append(match.matched_text)
            match_details["match_types"].append("suffix")
            match_details["match_scores"]["suffix"] = match_details["match_scores"].get("suffix", 0) + match.score
        
        # 4. 正则表达式匹配
        if config.name in self.compiled_regexes:
            regex_matches = self._match_regex_patterns(
                self.compiled_regexes[config.name], original_query
            )
            for match in regex_matches:
                total_score += 0.9
                match_details["matches"].append(match.matched_text)
                match_details["match_types"].append("regex")
                match_details["match_scores"]["regex"] = match_details["match_scores"].get("regex", 0) + match.score
        
        # 5. 命令模式匹配 (权重最高)
        command_matches = self._match_commands(patterns.command_patterns, original_query)
        for match in command_matches:
            total_score += 1.2
            match_details["matches"].append(match.matched_text)
            match_details["match_types"].append("command")
            match_details["match_scores"]["command"] = match_details["match_scores"].get("command", 0) + match.score
        
        # 6. 情感关键词匹配
        emotional_matches = self._match_keywords(
            patterns.emotional_keywords, query_processed, "emotional"
        )
        for match in emotional_matches:
            total_score += 0.7
            match_details["matches"].append(match.matched_text)
            match_details["match_types"].append("emotional")
            match_details["match_scores"]["emotional"] = match_details["match_scores"].get("emotional", 0) + match.score
        
        # 7. 问候语匹配
        greeting_matches = self._match_keywords(
            patterns.greeting_patterns, query_processed, "greeting"
        )
        for match in greeting_matches:
            total_score += 0.9
            match_details["matches"].append(match.matched_text)
            match_details["match_types"].append("greeting")
            match_details["match_scores"]["greeting"] = match_details["match_scores"].get("greeting", 0) + match.score
        
        # 8. 模糊匹配（如果启用且可用）
        if (FUZZY_AVAILABLE and 
            self.config_loader.global_settings.get('enable_fuzzy_matching', False)):
            fuzzy_score = self._fuzzy_match(query_processed, patterns)
            if fuzzy_score > 0:
                total_score += fuzzy_score * 0.6
                match_details["fuzzy_score"] = fuzzy_score
        
        # 归一化得分
        max_possible_score = self._calculate_max_score(patterns)
        if max_possible_score > 0:
            normalized_score = min(total_score / max_possible_score, 1.0)
        else:
            normalized_score = 0.0
            
        return normalized_score, match_details
    
    def _match_keywords(
        self, 
        keywords: List[str], 
        query: str, 
        match_type: str
    ) -> List[MatchResult]:
        """匹配关键词列表"""
        matches = []
        case_sensitive = self.config_loader.global_settings.get('case_sensitive', False)
        
        for keyword in keywords:
            if self._keyword_matches(keyword, query, case_sensitive):
                matches.append(MatchResult(
                    score=1.0,
                    match_type=match_type,
                    matched_text=keyword,
                    confidence=1.0
                ))
                
        return matches
    
    def _match_prefixes(self, prefixes: List[str], query: str) -> List[MatchResult]:
        """匹配前缀"""
        matches = []
        case_sensitive = self.config_loader.global_settings.get('case_sensitive', False)
        
        for prefix in prefixes:
            prefix_to_match = prefix if case_sensitive else prefix.lower()
            query_to_match = query if case_sensitive else query.lower()
            
            if query_to_match.startswith(prefix_to_match):
                matches.append(MatchResult(
                    score=0.8,
                    match_type="prefix",
                    matched_text=prefix,
                    confidence=0.8
                ))
                
        return matches
    
    def _match_suffixes(self, suffixes: List[str], query: str) -> List[MatchResult]:
        """匹配后缀"""
        matches = []
        case_sensitive = self.config_loader.global_settings.get('case_sensitive', False)
        
        for suffix in suffixes:
            suffix_to_match = suffix if case_sensitive else suffix.lower()
            query_to_match = query if case_sensitive else query.lower()
            
            if query_to_match.endswith(suffix_to_match):
                matches.append(MatchResult(
                    score=0.8,
                    match_type="suffix",
                    matched_text=suffix,
                    confidence=0.8
                ))
                
        return matches
    
    def _match_regex_patterns(
        self, 
        patterns: List[re.Pattern], 
        query: str
    ) -> List[MatchResult]:
        """匹配正则表达式模式"""
        matches = []
        
        for pattern in patterns:
            match = pattern.search(query)
            if match:
                matches.append(MatchResult(
                    score=0.9,
                    match_type="regex",
                    matched_text=match.group(0),
                    confidence=0.9
                ))
                
        return matches
    
    def _match_commands(self, commands: List[str], query: str) -> List[MatchResult]:
        """匹配命令模式"""
        matches = []
        query_stripped = query.strip()
        case_sensitive = self.config_loader.global_settings.get('case_sensitive', False)
        
        for command in commands:
            command_to_match = command if case_sensitive else command.lower()
            query_to_match = query_stripped if case_sensitive else query_stripped.lower()
            
            if query_to_match == command_to_match:
                matches.append(MatchResult(
                    score=1.2,
                    match_type="command",
                    matched_text=command,
                    confidence=1.0
                ))
                
        return matches
    
    def _keyword_matches(self, keyword: str, query: str, case_sensitive: bool) -> bool:
        """检查关键词是否匹配"""
        if case_sensitive:
            return keyword in query
        else:
            return keyword.lower() in query.lower()
    
    def _fuzzy_match(self, query: str, patterns) -> float:
        """模糊匹配"""
        if not FUZZY_AVAILABLE:
            return 0.0
            
        threshold = self.config_loader.global_settings.get('fuzzy_threshold', 80)
        best_score = 0.0
        
        all_keywords = patterns.get_all_keywords()
        
        for keyword in all_keywords:
            score = fuzz.partial_ratio(keyword.lower(), query.lower())
            if score >= threshold:
                best_score = max(best_score, score / 100.0)
                
        return best_score
    
    def _calculate_max_score(self, patterns) -> float:
        """计算最大可能得分"""
        return (
            len(patterns.exact_keywords) * 1.0 +
            len(patterns.prefix_keywords) * 0.8 +
            len(patterns.suffix_keywords) * 0.8 +
            len(patterns.regex_patterns) * 0.9 +
            len(patterns.command_patterns) * 1.2 +
            len(patterns.emotional_keywords) * 0.7 +
            len(patterns.greeting_patterns) * 0.9
        )
    
    def _preprocess_query(self, query: str) -> str:
        """查询预处理"""
        # 移除多余的空白字符
        processed = ' '.join(query.split())
        
        # 移除标点符号（除了斜杠，因为命令可能使用斜杠）
        if not self.config_loader.global_settings.get('case_sensitive', False):
            processed = processed.lower()
            
        return processed
    
    def _create_fallback_decision(
        self, 
        query: str,
        match_details: Dict, 
        reason: str
    ) -> RouteDecision:
        """创建回退决策"""
        default_handler = self.config_loader.global_settings.get('default_handler', 'chat_handler')
        
        return RouteDecision(
            handler_name=default_handler,
            confidence=0.1,
            metadata={
                "fallback": True,
                "reason": reason,
                "attempted_matches": match_details,
                "strategy": "configurable_keyword",
                "query": query[:100]  # 限制长度避免日志过长
            }
        )
        
    @property
    def strategy_name(self) -> str:
        return "configurable_keyword"
    
    async def reload_config(self) -> None:
        """热重载配置"""
        try:
            await self.config_loader.reload_config()
            await self._compile_regex_patterns()
            logger.info("ConfigurableKeywordStrategy 配置已重新加载")
        except Exception as e:
            logger.error(f"ConfigurableKeywordStrategy 配置重新加载失败: {e}")
            raise
            
    async def cleanup(self) -> None:
        """清理资源"""
        self.compiled_regexes.clear()
        self._initialized = False
        logger.info("ConfigurableKeywordStrategy 已清理")
        
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "strategy_name": self.strategy_name,
            "initialized": self._initialized,
            "fuzzy_available": FUZZY_AVAILABLE,
            "handlers_count": len(self.config_loader.handlers_config),
            "regex_patterns_count": sum(
                len(patterns) for patterns in self.compiled_regexes.values()
            ),
            "global_settings": self.config_loader.global_settings
        }