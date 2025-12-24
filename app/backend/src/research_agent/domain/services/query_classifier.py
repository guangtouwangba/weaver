"""Query Classification Service for intelligent RAG routing.

This service analyzes incoming queries and classifies them by complexity
to enable efficient routing to appropriate processing strategies.

Complexity Levels:
- simple: Greetings, clarifications, short factual questions
- moderate: Single-topic questions, specific lookups
- complex: Multi-part questions, comparative analysis, synthesis tasks
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from research_agent.shared.utils.logger import logger


class QueryComplexity(str, Enum):
    """Query complexity levels."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class QueryClassification:
    """Result of query classification."""

    complexity: QueryComplexity
    requires_context: bool
    estimated_tokens_needed: int
    confidence: float
    reasoning: str
    detected_patterns: List[str]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "complexity": self.complexity.value,
            "requires_context": self.requires_context,
            "estimated_tokens_needed": self.estimated_tokens_needed,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "detected_patterns": self.detected_patterns,
        }


class QueryClassifierService:
    """Service for classifying query complexity.

    Uses rule-based classification with configurable patterns.
    Can be extended with ML-based classification in the future.
    """

    # Greeting patterns (simple, no context needed)
    GREETING_PATTERNS = [
        r"^(你好|您好|hi|hello|hey|嗨|哈喽)",
        r"^(谢谢|感谢|thanks|thank you)",
        r"^(好的|ok|okay|understood|明白了|收到)",
        r"^(bye|再见|拜拜|goodbye)",
    ]

    # Clarification patterns (simple, may need minimal context)
    CLARIFICATION_PATTERNS = [
        r"^(什么意思|啥意思|怎么理解)",
        r"^(可以再说一遍|再说一次|pardon)",
        r"^(是的|对|不是|不对|yes|no)",
        r"^(继续|go on|接着说)",
    ]

    # Complex query indicators
    COMPLEX_INDICATORS = [
        r"(比较|对比|compare|versus|vs\.?)",
        r"(分析|analyze|analysis)",
        r"(总结|概括|summarize|summary)",
        r"(为什么.*又|一方面.*另一方面)",
        r"(第一.*第二|首先.*其次|1\).*2\)|一、.*二、)",
        r"(如何.*同时|既要.*又要)",
        r"(优缺点|pros.*cons|advantages.*disadvantages)",
        r"(区别.*联系|difference.*similarity)",
        r"(全面|comprehensive|详细|in detail|深入)",
    ]

    # Domain-specific keywords that suggest context is needed
    DOMAIN_KEYWORDS = [
        r"(文档|document|论文|paper|报告|report)",
        r"(章节|section|段落|paragraph|页|page)",
        r"(数据|data|表格|table|图表|chart)",
        r"(代码|code|实现|implementation)",
        r"(设计|design|架构|architecture)",
        r"(功能|feature|需求|requirement)",
    ]

    # Token budget by complexity
    TOKEN_BUDGETS = {
        QueryComplexity.SIMPLE: 0,  # No context needed
        QueryComplexity.MODERATE: 20000,  # ~20K tokens
        QueryComplexity.COMPLEX: -1,  # Full budget (unlimited)
    }

    def __init__(
        self,
        simple_max_length: int = 20,
        moderate_max_length: int = 100,
        enable_logging: bool = True,
    ):
        """Initialize the classifier.

        Args:
            simple_max_length: Max query length for simple classification
            moderate_max_length: Max query length for moderate classification
            enable_logging: Whether to log classification results
        """
        self._simple_max_length = simple_max_length
        self._moderate_max_length = moderate_max_length
        self._enable_logging = enable_logging

        # Compile regex patterns for performance
        self._greeting_patterns = [re.compile(p, re.IGNORECASE) for p in self.GREETING_PATTERNS]
        self._clarification_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.CLARIFICATION_PATTERNS
        ]
        self._complex_patterns = [re.compile(p, re.IGNORECASE) for p in self.COMPLEX_INDICATORS]
        self._domain_patterns = [re.compile(p, re.IGNORECASE) for p in self.DOMAIN_KEYWORDS]

    def classify(
        self,
        query: str,
        chat_history: Optional[List[str]] = None,
        document_count: int = 0,
    ) -> QueryClassification:
        """Classify a query by complexity.

        Args:
            query: The user query to classify
            chat_history: Optional list of previous messages for context
            document_count: Number of documents in the project

        Returns:
            QueryClassification with complexity and metadata
        """
        query = query.strip()
        detected_patterns: List[str] = []
        confidence = 0.8  # Base confidence

        # Check for greeting patterns (simple)
        if self._matches_any(query, self._greeting_patterns):
            detected_patterns.append("greeting")
            return self._create_classification(
                complexity=QueryComplexity.SIMPLE,
                requires_context=False,
                confidence=0.95,
                reasoning="Query matches greeting pattern",
                detected_patterns=detected_patterns,
            )

        # Check for clarification patterns (simple)
        if self._matches_any(query, self._clarification_patterns):
            detected_patterns.append("clarification")
            return self._create_classification(
                complexity=QueryComplexity.SIMPLE,
                requires_context=False,
                confidence=0.9,
                reasoning="Query matches clarification pattern",
                detected_patterns=detected_patterns,
            )

        # Check for complex indicators
        complex_matches = self._count_matches(query, self._complex_patterns)
        if complex_matches > 0:
            detected_patterns.append(f"complex_indicators({complex_matches})")

        # Check for domain keywords
        domain_matches = self._count_matches(query, self._domain_patterns)
        if domain_matches > 0:
            detected_patterns.append(f"domain_keywords({domain_matches})")

        # Length-based classification
        query_length = len(query)

        # Short queries without complex indicators
        if query_length <= self._simple_max_length and complex_matches == 0:
            # If no documents, treat as simple
            if document_count == 0:
                detected_patterns.append("short_no_docs")
                return self._create_classification(
                    complexity=QueryComplexity.SIMPLE,
                    requires_context=False,
                    confidence=0.85,
                    reasoning="Short query with no documents available",
                    detected_patterns=detected_patterns,
                )

            # Short query but has documents - moderate
            detected_patterns.append("short_with_docs")
            return self._create_classification(
                complexity=QueryComplexity.MODERATE,
                requires_context=True,
                confidence=0.75,
                reasoning="Short query but documents available for context",
                detected_patterns=detected_patterns,
            )

        # Medium length queries
        if query_length <= self._moderate_max_length:
            if complex_matches >= 2 or domain_matches >= 2:
                # Has complexity indicators - complex
                detected_patterns.append("medium_complex")
                return self._create_classification(
                    complexity=QueryComplexity.COMPLEX,
                    requires_context=True,
                    confidence=0.8,
                    reasoning="Medium query with multiple complexity indicators",
                    detected_patterns=detected_patterns,
                )

            # Standard medium query - moderate
            detected_patterns.append("medium_standard")
            return self._create_classification(
                complexity=QueryComplexity.MODERATE,
                requires_context=document_count > 0,
                confidence=0.8,
                reasoning="Standard medium-length query",
                detected_patterns=detected_patterns,
            )

        # Long queries are typically complex
        detected_patterns.append("long_query")
        return self._create_classification(
            complexity=QueryComplexity.COMPLEX,
            requires_context=True,
            confidence=0.85,
            reasoning="Long query typically requires comprehensive analysis",
            detected_patterns=detected_patterns,
        )

    def _matches_any(self, text: str, patterns: List[re.Pattern]) -> bool:
        """Check if text matches any of the patterns."""
        return any(p.search(text) for p in patterns)

    def _count_matches(self, text: str, patterns: List[re.Pattern]) -> int:
        """Count how many patterns match the text."""
        return sum(1 for p in patterns if p.search(text))

    def _create_classification(
        self,
        complexity: QueryComplexity,
        requires_context: bool,
        confidence: float,
        reasoning: str,
        detected_patterns: List[str],
    ) -> QueryClassification:
        """Create a classification result."""
        estimated_tokens = self.TOKEN_BUDGETS.get(complexity, -1)

        classification = QueryClassification(
            complexity=complexity,
            requires_context=requires_context,
            estimated_tokens_needed=estimated_tokens,
            confidence=confidence,
            reasoning=reasoning,
            detected_patterns=detected_patterns,
        )

        if self._enable_logging:
            logger.info(
                f"[QueryClassifier] Classified query: complexity={complexity.value}, "
                f"requires_context={requires_context}, confidence={confidence:.2f}, "
                f"patterns={detected_patterns}"
            )

        return classification

    def get_token_budget(self, classification: QueryClassification) -> int:
        """Get the recommended token budget for a classification.

        Args:
            classification: The query classification

        Returns:
            Token budget (-1 for unlimited)
        """
        return self.TOKEN_BUDGETS.get(classification.complexity, -1)


# Singleton instance
_classifier_instance: Optional[QueryClassifierService] = None


def get_query_classifier() -> QueryClassifierService:
    """Get the singleton query classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = QueryClassifierService()
    return _classifier_instance












