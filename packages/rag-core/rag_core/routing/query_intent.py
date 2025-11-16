"""
Query Intent Recognition and Routing

识别用户问题的意图类型，决定使用哪种信息源回答。
"""
from enum import Enum
from typing import Optional
from dataclasses import dataclass
import re


class QueryIntent(Enum):
    """问题意图类型"""
    
    META = "meta"
    """元问题：关于对话本身的问题，如"我刚才问了什么"、"上一个问题是什么" """
    
    DOCUMENT = "document"
    """文档问题：需要从知识库检索信息，如"什么是量价分析"、"如何使用MACD" """
    
    HYBRID = "hybrid"
    """混合问题：需要结合对话历史和文档，如"继续深入讲讲刚才那个概念" """
    
    GENERAL = "general"
    """通用问题：不需要特定知识的问候、闲聊等，如"你好"、"谢谢" """


@dataclass
class IntentRecognitionResult:
    """意图识别结果"""
    intent: QueryIntent
    confidence: float
    reasoning: str
    matched_patterns: list[str]


class QueryIntentClassifier:
    """基于规则的问题意图分类器"""
    
    # ========== 元问题模式（Meta Question Patterns）==========
    META_PATTERNS = {
        # 询问之前的问题
        "ask_previous_question": [
            r'(我|我的|你|咱们|我们).*(上|前|之前|刚才|刚刚|最近|第一个|最后一个).*(问|问题|提问|询问)',
            r'(上|前|之前|刚才|刚刚|最近|第一个|最后一个).*(问|问题|提问|询问).*(是什么|是啥|内容)',
            r'(what|which).*(previous|first|last|earlier|recent).*(question|ask|query)',
            r'(my|your|our).*(previous|first|last).*(question|ask)',
        ],
        
        # 询问之前的回答
        "ask_previous_answer": [
            r'(你|您).*(刚才|刚刚|之前|上次).*(说|讲|提到|回答|解释)',
            r'(刚才|刚刚|之前|上次).*(说|讲|提到|回答|解释).*(什么|啥|内容)',
            r'(what|which).*(you|we).*(said|mentioned|explained|answered)',
            r'(your|the).*(previous|earlier|last).*(answer|response|reply)',
        ],
        
        # 询问对话内容
        "ask_conversation_content": [
            r'(我们|咱们|我俩).*(讨论|聊|说|谈).*(什么|啥|内容|话题)',
            r'(对话|交流|沟通).*(内容|话题|主题)',
            r'(conversation|discussion|chat).*(about|content|topic)',
            r'(what).*(we).*(discuss|talk|chat)',
        ],
        
        # 引用之前内容
        "reference_previous": [
            r'刚才.*说的',
            r'之前.*提到的',
            r'上面.*讲的',
            r'你说的.*(那个|这个)',
            r'(that|this).*(you|we).*(mentioned|said)',
            r'as (you|we) (said|mentioned|discussed)',
        ],
    }
    
    # ========== 文档问题模式（Document Question Patterns）==========
    DOCUMENT_PATTERNS = {
        # 定义解释类
        "definition_explanation": [
            r'^(什么是|啥是|何为)',
            r'(的)?定义',
            r'(解释|介绍|说明).*(一下|下)',
            r'^(what is|what are|what\'s)',
            r'^(define|explain|describe)',
            r'(definition|explanation|description) of',
        ],
        
        # 方法指导类
        "how_to": [
            r'^(如何|怎么|怎样|咋)',
            r'(的)?(方法|步骤|流程|过程)',
            r'^(how to|how do|how can)',
            r'(steps|process|procedure) (to|for)',
        ],
        
        # 原因分析类
        "why_reason": [
            r'^(为什么|为啥|咋回事)',
            r'(的)?(原因|理由)',
            r'^(why|how come)',
            r'(reason|cause) (for|of|why)',
        ],
        
        # 比较对比类
        "comparison": [
            r'(区别|差别|不同|对比|比较)',
            r'(和|与|跟).*(相比|对比)',
            r'(difference|comparison|compare) between',
            r'(vs|versus)',
        ],
        
        # 列举类
        "listing": [
            r'(有哪些|都有啥|包括)',
            r'(列举|罗列)',
            r'(what are the|list|enumerate)',
            r'(types|kinds|categories) of',
        ],
    }
    
    # ========== 混合问题模式（Hybrid Question Patterns）==========
    HYBRID_PATTERNS = {
        # 继续深入
        "continue_deeper": [
            r'(继续|再|还|进一步).*(讲|说|谈|聊|深入)',
            r'(详细|具体).*(说|讲|解释)',
            r'(continue|more|further|deeper)',
            r'(elaborate|expand) on',
        ],
        
        # 关联对比
        "relate_to_previous": [
            r'(这|那).*(和|与|跟).*(刚才|之前|上面)',
            r'(关系|联系|区别)',
            r'(how|what).*(relate|related|connection)',
            r'(relationship|connection) between',
        ],
        
        # 基于上文提问
        "based_on_previous": [
            r'(那|这).*(意味着|说明|代表)',
            r'(所以|因此|那么)',
            r'(in that case|then|so)',
            r'(does that mean|does this mean)',
        ],
    }
    
    # ========== 通用问题模式（General Question Patterns）==========
    GENERAL_PATTERNS = {
        # 问候
        "greeting": [
            r'^(你好|您好|嗨|hi|hello|hey)$',
            r'^(早上好|下午好|晚上好|good morning|good afternoon|good evening)$',
        ],
        
        # 感谢
        "thanks": [
            r'^(谢谢|多谢|感谢|thanks|thank you)$',
            r'^(好的|ok|okay|got it)$',
        ],
    }
    
    @classmethod
    def classify(
        cls,
        question: str,
        has_conversation_history: bool = False
    ) -> IntentRecognitionResult:
        """
        分类问题意图
        
        Args:
            question: 用户问题
            has_conversation_history: 是否有对话历史（影响元问题判断）
            
        Returns:
            IntentRecognitionResult: 意图识别结果
        """
        question_lower = question.lower().strip()
        matched_patterns = []
        scores = {
            QueryIntent.META: 0.0,
            QueryIntent.DOCUMENT: 0.0,
            QueryIntent.HYBRID: 0.0,
            QueryIntent.GENERAL: 0.0,
        }
        
        # 1. 检查通用问题（优先级最高，避免误判）
        for category, patterns in cls.GENERAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    matched_patterns.append(f"general.{category}")
                    scores[QueryIntent.GENERAL] += 1.0
        
        if scores[QueryIntent.GENERAL] > 0:
            return IntentRecognitionResult(
                intent=QueryIntent.GENERAL,
                confidence=1.0,
                reasoning=f"匹配通用问题模式: {matched_patterns[0]}",
                matched_patterns=matched_patterns
            )
        
        # 2. 检查元问题（只有在有对话历史时才可能）
        if has_conversation_history:
            for category, patterns in cls.META_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, question, re.IGNORECASE):
                        matched_patterns.append(f"meta.{category}")
                        scores[QueryIntent.META] += 1.0
        
        # 3. 检查混合问题
        for category, patterns in cls.HYBRID_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    matched_patterns.append(f"hybrid.{category}")
                    scores[QueryIntent.HYBRID] += 1.0
        
        # 4. 检查文档问题
        for category, patterns in cls.DOCUMENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    matched_patterns.append(f"document.{category}")
                    scores[QueryIntent.DOCUMENT] += 1.0
        
        # 5. 决策逻辑
        # 如果元问题得分高，且有对话历史，优先判为元问题
        if scores[QueryIntent.META] > 0 and has_conversation_history:
            return IntentRecognitionResult(
                intent=QueryIntent.META,
                confidence=min(scores[QueryIntent.META] * 0.3 + 0.7, 1.0),
                reasoning=f"检测到元问题特征: {', '.join(matched_patterns[:2])}",
                matched_patterns=matched_patterns
            )
        
        # 如果混合问题得分高
        if scores[QueryIntent.HYBRID] > 0:
            # 如果同时有文档问题特征，且有对话历史，判为混合
            if scores[QueryIntent.DOCUMENT] > 0 and has_conversation_history:
                return IntentRecognitionResult(
                    intent=QueryIntent.HYBRID,
                    confidence=min(scores[QueryIntent.HYBRID] * 0.25 + 0.7, 1.0),
                    reasoning=f"需要结合对话历史和文档: {', '.join(matched_patterns[:2])}",
                    matched_patterns=matched_patterns
                )
        
        # 如果有明确的文档问题特征
        if scores[QueryIntent.DOCUMENT] > 0:
            return IntentRecognitionResult(
                intent=QueryIntent.DOCUMENT,
                confidence=min(scores[QueryIntent.DOCUMENT] * 0.25 + 0.7, 1.0),
                reasoning=f"需要从文档检索知识: {', '.join(matched_patterns[:2])}",
                matched_patterns=matched_patterns
            )
        
        # 6. 默认策略
        # 如果没有匹配任何模式，根据长度和复杂度判断
        if len(question) < 10 and not has_conversation_history:
            # 短问题且无历史，可能是通用问题
            return IntentRecognitionResult(
                intent=QueryIntent.GENERAL,
                confidence=0.5,
                reasoning="短问题且无对话历史，默认为通用问题",
                matched_patterns=[]
            )
        elif has_conversation_history:
            # 有对话历史，默认为混合（可能需要上下文）
            return IntentRecognitionResult(
                intent=QueryIntent.HYBRID,
                confidence=0.6,
                reasoning="未匹配明确模式，但有对话历史，默认为混合问题",
                matched_patterns=[]
            )
        else:
            # 其他情况，默认为文档问题
            return IntentRecognitionResult(
                intent=QueryIntent.DOCUMENT,
                confidence=0.6,
                reasoning="未匹配明确模式，默认为文档问题",
                matched_patterns=[]
            )


class QueryRouter:
    """问题路由器：根据意图决定信息检索策略"""
    
    @staticmethod
    def should_retrieve_documents(intent: QueryIntent) -> bool:
        """是否需要检索文档"""
        return intent in [QueryIntent.DOCUMENT, QueryIntent.HYBRID]
    
    @staticmethod
    def should_use_short_term_memory(intent: QueryIntent) -> bool:
        """是否需要使用短期记忆"""
        return intent in [QueryIntent.META, QueryIntent.HYBRID]
    
    @staticmethod
    def should_use_long_term_memory(intent: QueryIntent) -> bool:
        """是否需要使用长期记忆（相似历史检索）"""
        return intent in [QueryIntent.DOCUMENT, QueryIntent.HYBRID]
    
    @staticmethod
    def get_retrieval_strategy(intent: QueryIntent) -> dict:
        """
        获取检索策略配置
        
        Returns:
            dict: {
                'retrieve_documents': bool,
                'use_short_term_memory': bool,
                'use_long_term_memory': bool,
                'document_priority': float,  # 文档权重
                'memory_priority': float,     # 记忆权重
            }
        """
        strategies = {
            QueryIntent.META: {
                'retrieve_documents': False,
                'use_short_term_memory': True,
                'use_long_term_memory': False,
                'document_priority': 0.0,
                'memory_priority': 1.0,
            },
            QueryIntent.DOCUMENT: {
                'retrieve_documents': True,
                'use_short_term_memory': False,
                'use_long_term_memory': True,
                'document_priority': 1.0,
                'memory_priority': 0.3,
            },
            QueryIntent.HYBRID: {
                'retrieve_documents': True,
                'use_short_term_memory': True,
                'use_long_term_memory': True,
                'document_priority': 0.6,
                'memory_priority': 0.8,
            },
            QueryIntent.GENERAL: {
                'retrieve_documents': False,
                'use_short_term_memory': False,
                'use_long_term_memory': False,
                'document_priority': 0.0,
                'memory_priority': 0.0,
            },
        }
        
        return strategies.get(intent, strategies[QueryIntent.DOCUMENT])

