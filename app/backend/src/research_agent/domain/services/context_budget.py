"""Context Budget Manager for dynamic token allocation.

Manages context window budgets based on query complexity and available resources.
Ensures efficient use of LLM context windows by allocating appropriate amounts
based on actual needs rather than using maximum capacity for all queries.
"""

from dataclasses import dataclass
from typing import List, Optional

from research_agent.domain.services.query_classifier import (
    QueryClassification,
    QueryComplexity,
)
from research_agent.infrastructure.database.models import DocumentModel
from research_agent.shared.utils.logger import logger


@dataclass
class ContextAllocation:
    """Result of context budget allocation."""

    allocated_tokens: int  # Tokens allocated for this query
    max_documents: int  # Maximum number of documents to include
    priority_order: List[str]  # Document IDs in priority order
    reasoning: str
    utilization_ratio: float  # allocated / available

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "allocated_tokens": self.allocated_tokens,
            "max_documents": self.max_documents,
            "priority_order": self.priority_order,
            "reasoning": self.reasoning,
            "utilization_ratio": self.utilization_ratio,
        }


class ContextBudgetManager:
    """Manages context budget allocation for queries.

    Allocates context window space based on:
    - Query complexity classification
    - Available token budget
    - Document characteristics
    """

    # Budget allocation ratios by complexity
    BUDGET_RATIOS = {
        QueryComplexity.SIMPLE: 0.0,  # No context needed
        QueryComplexity.MODERATE: 0.15,  # 15% of available budget
        QueryComplexity.COMPLEX: 1.0,  # Full budget
    }

    # Absolute limits by complexity
    ABSOLUTE_LIMITS = {
        QueryComplexity.SIMPLE: 0,
        QueryComplexity.MODERATE: 30000,  # 30K max for moderate
        QueryComplexity.COMPLEX: -1,  # No limit
    }

    # Minimum tokens to be useful
    MIN_USEFUL_TOKENS = 1000

    def __init__(
        self,
        default_max_tokens: int = 500000,
        enable_logging: bool = True,
    ):
        """Initialize the budget manager.

        Args:
            default_max_tokens: Default maximum tokens if not specified
            enable_logging: Whether to log allocation decisions
        """
        self._default_max_tokens = default_max_tokens
        self._enable_logging = enable_logging

    def allocate(
        self,
        classification: QueryClassification,
        available_documents: List[DocumentModel],
        max_tokens: int,
        force_minimum: bool = False,
    ) -> ContextAllocation:
        """Allocate context budget for a query.

        Args:
            classification: Query classification result
            available_documents: Documents available for context
            max_tokens: Maximum available tokens
            force_minimum: If True, always allocate at least MIN_USEFUL_TOKENS

        Returns:
            ContextAllocation with budget details
        """
        complexity = classification.complexity

        # Get base allocation from classification
        ratio = self.BUDGET_RATIOS.get(complexity, 0.5)
        absolute_limit = self.ABSOLUTE_LIMITS.get(complexity, -1)

        # Calculate allocation
        base_allocation = int(max_tokens * ratio)

        # Apply absolute limit if set
        if absolute_limit > 0:
            allocated = min(base_allocation, absolute_limit)
        elif absolute_limit == 0:
            allocated = 0
        else:
            allocated = base_allocation

        # Use classification's estimated tokens if provided and lower
        if classification.estimated_tokens_needed > 0:
            allocated = min(allocated, classification.estimated_tokens_needed)

        # Ensure minimum if forced
        if force_minimum and allocated < self.MIN_USEFUL_TOKENS and allocated > 0:
            allocated = self.MIN_USEFUL_TOKENS

        # Calculate how many documents we can include
        max_docs, priority_docs = self._calculate_document_allocation(
            available_documents, allocated
        )

        utilization = allocated / max_tokens if max_tokens > 0 else 0.0

        allocation = ContextAllocation(
            allocated_tokens=allocated,
            max_documents=max_docs,
            priority_order=priority_docs,
            reasoning=f"Complexity={complexity.value}, ratio={ratio:.2f}, limit={absolute_limit}",
            utilization_ratio=utilization,
        )

        if self._enable_logging:
            logger.info(
                f"[ContextBudget] Allocated {allocated:,} tokens "
                f"({utilization:.1%} of {max_tokens:,}), "
                f"max_docs={max_docs}, "
                f"complexity={complexity.value}"
            )

        return allocation

    def _calculate_document_allocation(
        self,
        documents: List[DocumentModel],
        token_budget: int,
    ) -> tuple[int, List[str]]:
        """Calculate how many documents fit in the budget.

        Args:
            documents: Available documents
            token_budget: Token budget to allocate

        Returns:
            Tuple of (max_documents, priority_document_ids)
        """
        if token_budget <= 0 or not documents:
            return 0, []

        # Sort documents by token count (smallest first for fitting)
        sorted_docs = sorted(
            documents,
            key=lambda d: d.content_token_count or 0,
        )

        selected_ids = []
        remaining_budget = token_budget

        for doc in sorted_docs:
            token_count = doc.content_token_count or 0
            if token_count <= remaining_budget:
                selected_ids.append(str(doc.id))
                remaining_budget -= token_count
            else:
                # Can't fit more documents
                break

        return len(selected_ids), selected_ids

    def estimate_tokens_for_complexity(
        self,
        complexity: QueryComplexity,
        max_tokens: int,
    ) -> int:
        """Estimate tokens needed for a given complexity level.

        Args:
            complexity: Query complexity
            max_tokens: Maximum available tokens

        Returns:
            Estimated tokens needed
        """
        ratio = self.BUDGET_RATIOS.get(complexity, 0.5)
        absolute_limit = self.ABSOLUTE_LIMITS.get(complexity, -1)

        estimated = int(max_tokens * ratio)

        if absolute_limit > 0:
            estimated = min(estimated, absolute_limit)

        return estimated

    def should_use_full_context(
        self,
        classification: QueryClassification,
        total_doc_tokens: int,
        max_tokens: int,
    ) -> bool:
        """Determine if full context mode should be used.

        Args:
            classification: Query classification
            total_doc_tokens: Total tokens across all documents
            max_tokens: Maximum available tokens

        Returns:
            True if full context should be used
        """
        # Complex queries always use full context
        if classification.complexity == QueryComplexity.COMPLEX:
            return True

        # If all documents fit easily, use full context
        if total_doc_tokens < max_tokens * 0.3:  # Less than 30% of budget
            return True

        # Otherwise, use selective retrieval
        return False


# Singleton instance
_budget_manager: Optional[ContextBudgetManager] = None


def get_context_budget_manager(
    default_max_tokens: int = 500000,
) -> ContextBudgetManager:
    """Get the context budget manager instance.

    Args:
        default_max_tokens: Default maximum tokens

    Returns:
        ContextBudgetManager instance
    """
    global _budget_manager
    if _budget_manager is None:
        _budget_manager = ContextBudgetManager(default_max_tokens=default_max_tokens)
    return _budget_manager


def reset_context_budget_manager() -> None:
    """Reset the singleton instance (for testing)."""
    global _budget_manager
    _budget_manager = None













