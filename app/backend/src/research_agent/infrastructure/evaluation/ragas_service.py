"""Ragas evaluation service for real-time RAG quality assessment."""

from typing import List, Dict, Optional
import asyncio

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset
from langchain_openai import ChatOpenAI

from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.shared.utils.logger import logger


class RagasEvaluationService:
    """
    Ragas evaluation service for RAG quality metrics.
    
    Supports real-time evaluation of individual queries without ground truth.
    """
    
    def __init__(
        self,
        llm: ChatOpenAI,
        embeddings: EmbeddingService,
        use_context_recall: bool = False,  # Requires ground_truth
    ):
        """
        Initialize Ragas evaluation service.
        
        Args:
            llm: Language model for evaluation
            embeddings: Embedding service
            use_context_recall: Whether to use context_recall (requires ground_truth)
        """
        self.llm = llm
        self.embeddings = embeddings
        
        # Select metrics based on whether ground_truth is available
        self.metrics = [
            faithfulness,        # Answer faithfulness to contexts (no hallucination)
            answer_relevancy,    # Answer relevance to question
            context_precision,   # Precision of retrieved contexts
        ]
        
        if use_context_recall:
            self.metrics.append(context_recall)  # Requires ground_truth
        
        logger.info(f"Initialized RagasEvaluationService with metrics: {[m.name for m in self.metrics]}")
    
    async def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Evaluate a single RAG query/answer pair.
        
        Args:
            question: User question
            answer: Generated answer
            contexts: Retrieved context documents
            ground_truth: Optional ground truth answer (for offline evaluation)
        
        Returns:
            Dictionary of metric scores, e.g.:
            {
                "faithfulness": 0.95,
                "answer_relevancy": 0.88,
                "context_precision": 0.92,
                "context_recall": 0.85  # only if ground_truth provided
            }
        """
        try:
            logger.debug(f"[Ragas] Evaluating question: {question[:50]}...")
            
            # Build evaluation dataset
            data = {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts],
            }
            
            if ground_truth:
                data["ground_truth"] = [ground_truth]
            
            dataset = Dataset.from_dict(data)
            
            # Run evaluation
            # Note: evaluate() is synchronous, so we run it in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: evaluate(
                    dataset,
                    metrics=self.metrics,
                    llm=self.llm,
                    embeddings=self.embeddings,
                )
            )
            
            # Convert to dict and extract scores
            metrics_dict = {}
            for metric_name in result.keys():
                if metric_name not in ["user_input", "retrieved_contexts", "response", "reference"]:
                    try:
                        metrics_dict[metric_name] = float(result[metric_name])
                    except (ValueError, TypeError):
                        logger.warning(f"[Ragas] Could not convert {metric_name} to float: {result[metric_name]}")
            
            logger.info(f"[Ragas] Evaluation complete: {metrics_dict}")
            return metrics_dict
            
        except Exception as e:
            logger.error(f"[Ragas] Evaluation failed: {e}", exc_info=True)
            return {}
    
    async def evaluate_batch(
        self,
        questions: List[str],
        answers: List[str],
        contexts_list: List[List[str]],
        ground_truths: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """
        Evaluate a batch of queries (for offline evaluation).
        
        Args:
            questions: List of questions
            answers: List of answers
            contexts_list: List of context lists
            ground_truths: Optional list of ground truth answers
        
        Returns:
            Aggregated metrics (mean scores across all samples)
        """
        try:
            logger.info(f"[Ragas] Batch evaluating {len(questions)} samples...")
            
            # Build dataset
            data = {
                "question": questions,
                "answer": answers,
                "contexts": contexts_list,
            }
            
            if ground_truths:
                data["ground_truth"] = ground_truths
            
            dataset = Dataset.from_dict(data)
            
            # Run evaluation (in executor for async)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: evaluate(
                    dataset,
                    metrics=self.metrics,
                    llm=self.llm,
                    embeddings=self.embeddings,
                )
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

