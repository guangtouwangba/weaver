"""
查询处理器实现

负责查询分析、意图识别、查询重写等功能。
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

from modules.rag.base import (
    IQueryProcessor,
    QueryAnalysis,
    QueryComplexity,
    RAGContext,
    RAGPipelineError,
)

logger = logging.getLogger(__name__)


class BasicQueryProcessor(IQueryProcessor):
    """基础查询处理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 配置参数
        self.enable_query_expansion = config.get("enable_query_expansion", True)
        self.enable_entity_extraction = config.get("enable_entity_extraction", True)
        self.max_rewritten_queries = config.get("max_rewritten_queries", 3)
        
        # 复杂度判断关键词
        self.multi_hop_keywords = {
            "比较", "对比", "区别", "相同", "不同", "优缺点", "vs", "versus",
            "compare", "difference", "similarity", "pros and cons"
        }
        
        self.analytical_keywords = {
            "为什么", "如何", "怎样", "原因", "分析", "解释", "机制", "原理",
            "why", "how", "analyze", "explain", "mechanism", "principle"
        }
        
        logger.info("BasicQueryProcessor 初始化完成")
    
    async def initialize(self) -> None:
        """初始化查询处理器"""
        if self._initialized:
            return
        
        try:
            # 这里可以初始化NLP模型、实体识别器等
            # 目前使用基础的规则方法
            self._initialized = True
            logger.info("BasicQueryProcessor 初始化成功")
            
        except Exception as e:
            logger.error(f"BasicQueryProcessor 初始化失败: {e}")
            raise RAGPipelineError(
                f"查询处理器初始化失败: {e}",
                component_type=self.component_type
            )
    
    async def process(self, context: RAGContext) -> RAGContext:
        """处理RAG上下文"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 分析查询
            query_analysis = await self.analyze_query(context.query)
            context.query_analysis = query_analysis
            
            # 记录处理元数据
            context.processing_metadata["query_processor"] = {
                "complexity": query_analysis.complexity.value,
                "intent": query_analysis.intent,
                "entities_count": len(query_analysis.entities),
                "rewritten_queries_count": len(query_analysis.rewritten_queries)
            }
            
            logger.info(f"查询处理完成: 复杂度={query_analysis.complexity.value}, "
                       f"意图={query_analysis.intent}")
            
            return context
            
        except Exception as e:
            logger.error(f"查询处理失败: {e}")
            raise RAGPipelineError(
                f"查询处理失败: {e}",
                component_type=self.component_type
            )
    
    async def analyze_query(self, query: str) -> QueryAnalysis:
        """分析查询"""
        try:
            # 1. 基础清理
            cleaned_query = self._clean_query(query)
            
            # 2. 判断复杂度
            complexity = self._determine_complexity(cleaned_query)
            
            # 3. 识别意图
            intent = self._identify_intent(cleaned_query)
            
            # 4. 提取实体和关键词
            entities = await self._extract_entities(cleaned_query)
            keywords = self._extract_keywords(cleaned_query)
            
            # 5. 生成重写查询
            rewritten_queries = await self.rewrite_query(cleaned_query)
            
            # 6. 计算置信度
            confidence = self._calculate_confidence(cleaned_query, complexity, intent)
            
            return QueryAnalysis(
                original_query=query,
                complexity=complexity,
                intent=intent,
                entities=entities,
                keywords=keywords,
                rewritten_queries=rewritten_queries,
                confidence=confidence,
                metadata={
                    "cleaned_query": cleaned_query,
                    "processing_method": "rule_based"
                }
            )
            
        except Exception as e:
            logger.error(f"查询分析失败: {e}")
            raise RAGPipelineError(f"查询分析失败: {e}")
    
    async def rewrite_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """重写查询"""
        if not self.enable_query_expansion:
            return []
        
        try:
            rewritten = []
            
            # 1. 同义词扩展
            synonym_query = self._expand_with_synonyms(query)
            if synonym_query != query:
                rewritten.append(synonym_query)
            
            # 2. 关键词提取重写
            keywords = self._extract_keywords(query)
            if len(keywords) > 1:
                keyword_query = " ".join(keywords[:3])  # 取前3个关键词
                if keyword_query != query:
                    rewritten.append(keyword_query)
            
            # 3. 问题转陈述句
            if query.strip().endswith('?') or any(q in query for q in ['什么', '如何', '为什么', 'what', 'how', 'why']):
                statement_query = self._question_to_statement(query)
                if statement_query != query:
                    rewritten.append(statement_query)
            
            # 限制重写查询数量
            return rewritten[:self.max_rewritten_queries]
            
        except Exception as e:
            logger.warning(f"查询重写失败: {e}")
            return []
    
    def _clean_query(self, query: str) -> str:
        """清理查询文本"""
        # 去除多余空格和特殊字符
        cleaned = re.sub(r'\s+', ' ', query.strip())
        # 去除HTML标签
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        return cleaned
    
    def _determine_complexity(self, query: str) -> QueryComplexity:
        """判断查询复杂度"""
        query_lower = query.lower()
        
        # 检查多跳关键词
        if any(keyword in query_lower for keyword in self.multi_hop_keywords):
            return QueryComplexity.COMPARATIVE
        
        # 检查分析性关键词
        if any(keyword in query_lower for keyword in self.analytical_keywords):
            return QueryComplexity.ANALYTICAL
        
        # 检查是否包含多个问题
        question_count = query.count('?') + len(re.findall(r'[什么|如何|为什么|哪个|哪些]', query))
        if question_count > 1:
            return QueryComplexity.MULTI_HOP
        
        # 检查查询长度和复杂性
        if len(query.split()) > 10 or len(re.findall(r'[，。；]', query)) > 2:
            return QueryComplexity.ANALYTICAL
        
        return QueryComplexity.SIMPLE
    
    def _identify_intent(self, query: str) -> str:
        """识别查询意图"""
        query_lower = query.lower()
        
        # 定义意图模式
        intent_patterns = {
            "factual": ["什么是", "定义", "介绍", "what is", "define", "definition"],
            "procedural": ["如何", "怎样", "步骤", "方法", "how to", "how do", "steps"],
            "causal": ["为什么", "原因", "导致", "why", "cause", "reason"],
            "comparative": ["比较", "对比", "区别", "优缺点", "compare", "difference", "vs"],
            "numerical": ["多少", "数量", "统计", "how many", "how much", "statistics"],
            "temporal": ["什么时候", "时间", "历史", "when", "time", "history"],
            "locational": ["哪里", "位置", "地点", "where", "location", "place"]
        }
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return intent
        
        return "general"
    
    async def _extract_entities(self, query: str) -> List[str]:
        """提取实体（简化版本）"""
        if not self.enable_entity_extraction:
            return []
        
        # 简单的实体提取规则
        entities = []
        
        # 提取可能的专有名词（大写开头的词）
        words = query.split()
        for word in words:
            if word and word[0].isupper() and len(word) > 1:
                entities.append(word)
        
        # 提取数字
        numbers = re.findall(r'\d+', query)
        entities.extend(numbers)
        
        return list(set(entities))  # 去重
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 停用词列表（简化版）
        stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'as', 'are', 'was', 'were',
            '什么', '如何', '为什么', '怎样', '哪个', '哪些', '什么时候', '哪里',
            'what', 'how', 'why', 'when', 'where', 'which', 'who'
        }
        
        # 分词并过滤
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        return keywords[:10]  # 返回前10个关键词
    
    def _expand_with_synonyms(self, query: str) -> str:
        """使用同义词扩展查询（简化版）"""
        # 简单的同义词映射
        synonyms = {
            "机器学习": "人工智能 深度学习 ML AI",
            "深度学习": "神经网络 机器学习 DL",
            "人工智能": "机器学习 AI 智能系统",
            "数据库": "数据存储 DB database",
            "算法": "方法 algorithm 计算方法"
        }
        
        expanded_query = query
        for term, expansion in synonyms.items():
            if term in query:
                expanded_query = query.replace(term, f"{term} {expansion}")
                break
        
        return expanded_query
    
    def _question_to_statement(self, query: str) -> str:
        """将问题转换为陈述句"""
        # 简单的问题转陈述规则
        transformations = {
            "什么是": "",
            "如何": "",
            "为什么": "",
            "怎样": "",
            "what is": "",
            "how to": "",
            "how do": "",
            "why": ""
        }
        
        statement = query.rstrip('?')
        for question_word, replacement in transformations.items():
            if statement.lower().startswith(question_word):
                statement = statement[len(question_word):].strip()
                break
        
        return statement
    
    def _calculate_confidence(self, query: str, complexity: QueryComplexity, intent: str) -> float:
        """计算分析置信度"""
        confidence = 0.5  # 基础置信度
        
        # 根据查询长度调整
        if 5 <= len(query.split()) <= 15:
            confidence += 0.2
        
        # 根据复杂度调整
        if complexity != QueryComplexity.SIMPLE:
            confidence += 0.1
        
        # 根据意图识别调整
        if intent != "general":
            confidence += 0.2
        
        return min(confidence, 1.0)


class EnhancedQueryProcessor(BasicQueryProcessor):
    """增强查询处理器（支持AI模型）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # AI模型配置
        self.use_ai_analysis = config.get("use_ai_analysis", False)
        self.ai_model = config.get("ai_model", "gpt-3.5-turbo")
        self.ai_client = None
        
        logger.info("EnhancedQueryProcessor 初始化完成")
    
    async def initialize(self) -> None:
        """初始化增强查询处理器"""
        await super().initialize()
        
        if self.use_ai_analysis:
            try:
                # 初始化AI客户端
                from openai import AsyncOpenAI
                import os
                
                self.ai_client = AsyncOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY")
                )
                
                logger.info("AI查询分析客户端初始化成功")
                
            except Exception as e:
                logger.warning(f"AI客户端初始化失败，回退到基础模式: {e}")
                self.use_ai_analysis = False
    
    async def analyze_query(self, query: str) -> QueryAnalysis:
        """使用AI增强的查询分析"""
        if self.use_ai_analysis and self.ai_client:
            try:
                return await self._ai_analyze_query(query)
            except Exception as e:
                logger.warning(f"AI查询分析失败，回退到基础分析: {e}")
        
        # 回退到基础分析
        return await super().analyze_query(query)
    
    async def _ai_analyze_query(self, query: str) -> QueryAnalysis:
        """使用AI模型分析查询"""
        prompt = f"""
        分析以下查询，返回JSON格式的结果：
        
        查询: "{query}"
        
        请分析：
        1. 查询复杂度 (simple/multi_hop/analytical/comparative)
        2. 查询意图 (factual/procedural/causal/comparative/numerical/temporal/locational/general)
        3. 关键实体
        4. 关键词
        5. 可能的重写查询（最多3个）
        
        返回格式：
        {{
            "complexity": "simple|multi_hop|analytical|comparative",
            "intent": "意图类型",
            "entities": ["实体1", "实体2"],
            "keywords": ["关键词1", "关键词2"],
            "rewritten_queries": ["重写1", "重写2"],
            "confidence": 0.8
        }}
        """
        
        response = await self.ai_client.chat.completions.create(
            model=self.ai_model,
            messages=[
                {"role": "system", "content": "你是一个专业的查询分析助手，擅长分析用户查询的意图和复杂度。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        # 解析AI响应
        import json
        try:
            result = json.loads(response.choices[0].message.content)
            
            # 转换复杂度枚举
            complexity_map = {
                "simple": QueryComplexity.SIMPLE,
                "multi_hop": QueryComplexity.MULTI_HOP,
                "analytical": QueryComplexity.ANALYTICAL,
                "comparative": QueryComplexity.COMPARATIVE
            }
            
            return QueryAnalysis(
                original_query=query,
                complexity=complexity_map.get(result.get("complexity", "simple"), QueryComplexity.SIMPLE),
                intent=result.get("intent", "general"),
                entities=result.get("entities", []),
                keywords=result.get("keywords", []),
                rewritten_queries=result.get("rewritten_queries", []),
                confidence=result.get("confidence", 0.5),
                metadata={
                    "processing_method": "ai_enhanced",
                    "ai_model": self.ai_model
                }
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"AI响应解析失败: {e}")
            # 回退到基础分析
            return await super().analyze_query(query)
