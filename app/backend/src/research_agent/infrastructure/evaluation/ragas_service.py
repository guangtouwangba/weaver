"""Ragas evaluation service for real-time RAG quality assessment."""

import asyncio

from datasets import Dataset
from langchain_openai import ChatOpenAI
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.shared.utils.logger import logger


class RagasEvaluationService:
    """
    Ragas evaluation service for RAG quality metrics.

    Supports real-time evaluation of individual queries without ground truth.

    Note on metrics and ground truth requirements:
    - faithfulness: NO ground truth needed (checks answer vs contexts)
    - answer_relevancy: NO ground truth needed (checks answer vs question)
    - context_precision: REQUIRES ground truth (reference)
    - context_recall: REQUIRES ground truth (reference)
    """

    def __init__(
        self,
        llm: ChatOpenAI,
        embeddings: EmbeddingService,
        use_ground_truth_metrics: bool = False,  # Whether to use metrics requiring ground_truth
    ):
        """
        Initialize Ragas evaluation service.

        Args:
            llm: Language model for evaluation
            embeddings: Embedding service
            use_ground_truth_metrics: Whether to use metrics that require ground_truth
                                      (context_precision, context_recall)
        """
        self.llm = llm
        self.embeddings = embeddings
        self.use_ground_truth_metrics = use_ground_truth_metrics

        # Metrics that DON'T require ground truth (for real-time evaluation)
        self.base_metrics = [
            faithfulness,  # Answer faithfulness to contexts (no hallucination)
            answer_relevancy,  # Answer relevance to question
        ]

        # Metrics that REQUIRE ground truth (for offline/batch evaluation)
        self.ground_truth_metrics = [
            context_precision,  # Precision of retrieved contexts (needs reference)
            context_recall,  # Recall of retrieved contexts (needs reference)
        ]

        # Default metrics (no ground truth required)
        self.metrics = self.base_metrics.copy()

        if use_ground_truth_metrics:
            self.metrics.extend(self.ground_truth_metrics)

        logger.info(
            f"Initialized RagasEvaluationService with metrics: {[m.name for m in self.metrics]}"
        )

    async def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: str | None = None,
    ) -> dict[str, float]:
        """
        Evaluate a single RAG query/answer pair.

        Args:
            question: User question
            answer: Generated answer
            contexts: Retrieved context documents
            ground_truth: Optional ground truth answer (enables context_precision/recall)

        Returns:
            Dictionary of metric scores, e.g.:
            {
                "faithfulness": 0.95,
                "answer_relevancy": 0.88,
                "context_precision": 0.92,  # only if ground_truth provided
                "context_recall": 0.85      # only if ground_truth provided
            }
        """
        try:
            logger.debug(f"[Ragas] Evaluating question: {question[:50]}...")

            # Select metrics based on whether ground_truth is available
            # context_precision and context_recall REQUIRE ground_truth (reference)
            if ground_truth:
                metrics_to_use = self.base_metrics + self.ground_truth_metrics
                logger.debug("[Ragas] Using all metrics (ground_truth provided)")
            else:
                metrics_to_use = self.base_metrics
                logger.debug("[Ragas] Using base metrics only (no ground_truth)")

            # Build evaluation dataset
            data = {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts],
            }

            if ground_truth:
                data["reference"] = [ground_truth]  # RAGAS uses "reference" column name

            dataset = Dataset.from_dict(data)

            # Run evaluation
            # Note: evaluate() is synchronous, so we run it in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: evaluate(
                    dataset,
                    metrics=metrics_to_use,
                    llm=self.llm,
                    embeddings=self.embeddings,
                ),
            )

            # Convert to dict and extract scores
            metrics_dict = {}
            for metric_name in result.keys():
                if metric_name not in ["user_input", "retrieved_contexts", "response", "reference"]:
                    try:
                        metrics_dict[metric_name] = float(result[metric_name])
                    except (ValueError, TypeError):
                        logger.warning(
                            f"[Ragas] Could not convert {metric_name} to float: {result[metric_name]}"
                        )

            logger.info(f"[Ragas] Evaluation complete: {metrics_dict}")
            return metrics_dict

        except Exception as e:
            logger.error(f"[Ragas] Evaluation failed: {e}", exc_info=True)
            return {}

    async def evaluate_batch(
        self,
        questions: list[str],
        answers: list[str],
        contexts_list: list[list[str]],
        ground_truths: list[str] | None = None,
    ) -> dict[str, float]:
        """
        Evaluate a batch of queries (for offline evaluation).

        Args:
            questions: List of questions
            answers: List of answers
            contexts_list: List of context lists
            ground_truths: Optional list of ground truth answers (enables context_precision/recall)

        Returns:
            Aggregated metrics (mean scores across all samples)
        """
        try:
            logger.info(f"[Ragas] Batch evaluating {len(questions)} samples...")

            # Select metrics based on whether ground_truths is available
            if ground_truths:
                metrics_to_use = self.base_metrics + self.ground_truth_metrics
                logger.info("[Ragas] Using all metrics (ground_truths provided)")
            else:
                metrics_to_use = self.base_metrics
                logger.info("[Ragas] Using base metrics only (no ground_truths)")

            # Build dataset
            data = {
                "question": questions,
                "answer": answers,
                "contexts": contexts_list,
            }

            if ground_truths:
                data["reference"] = ground_truths  # RAGAS uses "reference" column name

            dataset = Dataset.from_dict(data)

            # Run evaluation (in executor for async)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: evaluate(
                    dataset,
                    metrics=metrics_to_use,
                    llm=self.llm,
                    embeddings=self.embeddings,
                ),
            )

            # Extract aggregated scores
            metrics_dict = {}
            for metric_name in result.keys():
                if metric_name not in ["user_input", "retrieved_contexts", "response", "reference"]:
                    try:
                        metrics_dict[metric_name] = float(result[metric_name])
                    except (ValueError, TypeError):
                        logger.warning(f"[Ragas] Could not convert {metric_name} to float")

            logger.info(f"[Ragas] Batch evaluation complete: {metrics_dict}")
            return metrics_dict

        except Exception as e:
            logger.error(f"[Ragas] Batch evaluation failed: {e}", exc_info=True)
            return {}
