"""RAGAS-based evaluation for RAG systems."""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


class EvaluationMetrics(str, Enum):
    """Available RAGAS evaluation metrics."""
    
    # Retrieval metrics (measure retrieval quality)
    CONTEXT_PRECISION = "context_precision"  # Precision of retrieved contexts
    CONTEXT_RECALL = "context_recall"  # Recall of retrieved contexts
    CONTEXT_RELEVANCY = "context_relevancy"  # Relevancy of retrieved contexts
    
    # Generation metrics (measure answer quality)
    FAITHFULNESS = "faithfulness"  # Answer is grounded in context
    ANSWER_RELEVANCY = "answer_relevancy"  # Answer addresses the question
    ANSWER_SIMILARITY = "answer_similarity"  # Similarity to ground truth
    ANSWER_CORRECTNESS = "answer_correctness"  # Correctness vs ground truth
    
    # Combined metrics
    HARMONIC_MEAN = "harmonic_mean"  # Harmonic mean of all metrics


@dataclass
class EvaluationResult:
    """Result of a RAG system evaluation."""
    
    scores: Dict[str, float]  # Metric name -> score
    per_sample_scores: Optional[List[Dict[str, float]]] = None  # Per-sample scores
    metadata: Dict[str, Any] = None  # Additional metadata
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def get_score(self, metric: str | EvaluationMetrics) -> float:
        """Get score for a specific metric."""
        if isinstance(metric, EvaluationMetrics):
            metric = metric.value
        return self.scores.get(metric, 0.0)
    
    def summary(self) -> str:
        """Get a summary string of the evaluation results."""
        lines = ["=== Evaluation Results ==="]
        for metric, score in sorted(self.scores.items()):
            lines.append(f"{metric:25s}: {score:.4f}")
        return "\n".join(lines)


class JSONCleaningLLMWrapper:
    """
    Wrapper for LLM that cleans JSON responses.
    
    Some LLMs (like Claude) return JSON wrapped in markdown code blocks.
    This wrapper extracts the JSON content before returning it to RAGAS.
    """
    
    def __init__(self, llm: Any):
        """
        Initialize the wrapper.
        
        Args:
            llm: The underlying LLM to wrap
        """
        self.llm = llm
        self._is_chat_model = hasattr(llm, 'chat')
        logger.info(f"🧹 JSONCleaningLLMWrapper initialized for {llm.__class__.__name__}")
        logger.info(f"   Wrapper methods: invoke, ainvoke, generate, agenerate")
        logger.info(f"   Will clean markdown code blocks from JSON responses")
    
    def _clean_json_response(self, text: str) -> str:
        """
        Clean JSON response by removing markdown code blocks.
        
        Args:
            text: Raw response text
            
        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks (```json ... ``` or ``` ... ```)
        # Pattern 1: ```json\n...\n```
        pattern1 = r'```json\s*\n(.*?)\n```'
        match = re.search(pattern1, text, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
            logger.debug(f"Cleaned JSON from markdown (pattern 1): {len(text)} -> {len(cleaned)} chars")
            return cleaned
        
        # Pattern 2: ```\n...\n```
        pattern2 = r'```\s*\n(.*?)\n```'
        match = re.search(pattern2, text, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
            logger.debug(f"Cleaned JSON from markdown (pattern 2): {len(text)} -> {len(cleaned)} chars")
            return cleaned
        
        # No markdown found, return as-is
        return text.strip()
    
    def invoke(self, prompt: str, **kwargs) -> Any:
        """Invoke the underlying LLM and clean the response."""
        logger.debug(f"JSONCleaningLLMWrapper.invoke called with prompt length: {len(prompt)}")
        response = self.llm.invoke(prompt, **kwargs)
        
        # Handle different response types
        if hasattr(response, 'content'):
            # LangChain AIMessage
            original_content = response.content
            cleaned_content = self._clean_json_response(original_content)
            if cleaned_content != original_content:
                logger.info(f"🧹 Cleaned markdown from LLM response: {original_content[:100]}...")
                response.content = cleaned_content
        elif isinstance(response, str):
            # Direct string response
            original = response
            response = self._clean_json_response(response)
            if response != original:
                logger.info(f"🧹 Cleaned markdown from string response: {original[:100]}...")
        
        return response
    
    async def ainvoke(self, prompt: str, **kwargs) -> Any:
        """Async invoke the underlying LLM and clean the response."""
        logger.debug(f"JSONCleaningLLMWrapper.ainvoke called with prompt length: {len(prompt)}")
        response = await self.llm.ainvoke(prompt, **kwargs)
        
        # Handle different response types
        if hasattr(response, 'content'):
            # LangChain AIMessage
            original_content = response.content
            cleaned_content = self._clean_json_response(original_content)
            if cleaned_content != original_content:
                logger.info(f"🧹 Cleaned markdown from async LLM response: {original_content[:100]}...")
                response.content = cleaned_content
        elif isinstance(response, str):
            # Direct string response
            original = response
            response = self._clean_json_response(response)
            if response != original:
                logger.info(f"🧹 Cleaned markdown from async string response: {original[:100]}...")
        
        return response
    
    def generate(self, prompts: List[str], **kwargs) -> Any:
        """Generate responses for multiple prompts."""
        logger.debug(f"JSONCleaningLLMWrapper.generate called with {len(prompts)} prompts")
        result = self.llm.generate(prompts, **kwargs)
        
        # Clean all generations
        cleaned_count = 0
        for generation_list in result.generations:
            for generation in generation_list:
                if hasattr(generation, 'text'):
                    original = generation.text
                    generation.text = self._clean_json_response(generation.text)
                    if original != generation.text:
                        cleaned_count += 1
                        logger.debug(f"🧹 Cleaned generation.text")
                if hasattr(generation, 'message') and hasattr(generation.message, 'content'):
                    original = generation.message.content
                    generation.message.content = self._clean_json_response(generation.message.content)
                    if original != generation.message.content:
                        cleaned_count += 1
                        logger.debug(f"🧹 Cleaned generation.message.content")
        
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned markdown from {cleaned_count} batch generations")
        
        return result
    
    async def agenerate(self, prompts: List[str], **kwargs) -> Any:
        """Async generate responses for multiple prompts."""
        logger.debug(f"JSONCleaningLLMWrapper.agenerate called with {len(prompts)} prompts")
        result = await self.llm.agenerate(prompts, **kwargs)
        
        # Clean all generations
        cleaned_count = 0
        for generation_list in result.generations:
            for generation in generation_list:
                if hasattr(generation, 'text'):
                    original = generation.text
                    generation.text = self._clean_json_response(generation.text)
                    if original != generation.text:
                        cleaned_count += 1
                        logger.debug(f"🧹 Cleaned async generation.text")
                if hasattr(generation, 'message') and hasattr(generation.message, 'content'):
                    original = generation.message.content
                    generation.message.content = self._clean_json_response(generation.message.content)
                    if original != generation.message.content:
                        cleaned_count += 1
                        logger.debug(f"🧹 Cleaned async generation.message.content")
        
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned markdown from {cleaned_count} async batch generations")
        
        return result
    
    def call(self, prompt: str, **kwargs) -> str:
        """Call the LLM (alternative interface) and clean response."""
        logger.debug(f"JSONCleaningLLMWrapper.call intercepted")
        if hasattr(self.llm, 'call'):
            response = self.llm.call(prompt, **kwargs)
        else:
            response = self.llm(prompt, **kwargs)
        
        if isinstance(response, str):
            original = response
            response = self._clean_json_response(response)
            if response != original:
                logger.info(f"🧹 Cleaned markdown from call() response")
        elif hasattr(response, 'content'):
            original = response.content
            response.content = self._clean_json_response(response.content)
            if response.content != original:
                logger.info(f"🧹 Cleaned markdown from call() AIMessage")
        
        return response
    
    def __call__(self, prompt: str, **kwargs) -> Any:
        """Make the wrapper callable like the underlying LLM."""
        logger.debug(f"JSONCleaningLLMWrapper.__call__ intercepted")
        response = self.llm(prompt, **kwargs)
        
        if isinstance(response, str):
            original = response
            response = self._clean_json_response(response)
            if response != original:
                logger.info(f"🧹 Cleaned markdown from __call__ response")
        elif hasattr(response, 'content'):
            original = response.content
            response.content = self._clean_json_response(response.content)
            if response.content != original:
                logger.info(f"🧹 Cleaned markdown from __call__ AIMessage")
        
        return response
    
    def bind(self, **kwargs):
        """Bind parameters to the LLM and return a wrapped version."""
        logger.debug(f"JSONCleaningLLMWrapper.bind called with: {list(kwargs.keys())}")
        bound_llm = self.llm.bind(**kwargs)
        # Return a new wrapper around the bound LLM
        return JSONCleaningLLMWrapper(bound_llm)
    
    def with_structured_output(self, schema, **kwargs):
        """Intercept structured output calls - RAGAS likely uses this."""
        logger.warning(f"⚠️  JSONCleaningLLMWrapper: RAGAS is using with_structured_output!")
        logger.warning(f"   Schema: {schema}")
        logger.warning(f"   This bypasses our cleaning wrapper!")
        
        # We need to wrap the structured output to still clean the responses
        # Get the structured output LLM
        structured_llm = self.llm.with_structured_output(schema, **kwargs)
        
        # Unfortunately, structured output uses a different pipeline
        # We need to intercept at the client level instead
        logger.warning(f"   → Returning wrapped structured LLM")
        return JSONCleaningLLMWrapper(structured_llm)
    
    def __getattr__(self, name: str) -> Any:
        """Forward all other attributes to the underlying LLM."""
        # Log when unknown attributes are accessed
        if not name.startswith('_') and name not in ['dict', 'copy', 'model_fields']:
            logger.debug(f"JSONCleaningLLMWrapper: forwarding attribute '{name}' to underlying LLM")
        return getattr(self.llm, name)


class RAGASEvaluator:
    """
    RAGAS-based evaluator for RAG systems.

    Evaluates both retrieval quality and generation quality using RAGAS metrics.
    
    Supported metrics:
    - context_precision: Measures if relevant contexts are ranked higher
    - context_recall: Measures if all relevant contexts are retrieved
    - faithfulness: Measures if answer is grounded in retrieved contexts
    - answer_relevancy: Measures if answer addresses the question
    - answer_similarity: Cosine similarity with ground truth
    - answer_correctness: Weighted combination of similarity and factual correctness

    Example:
        ```python
        from rag_core.evaluation import RAGASEvaluator, EvaluationDataset
        
        # Create evaluator
        evaluator = RAGASEvaluator(
            llm=your_llm,
            embeddings=your_embeddings
        )
        
        # Load dataset
        dataset = EvaluationDataset.load("eval_data.json")
        
        # Evaluate
        results = await evaluator.evaluate(
            dataset,
            metrics=[
                EvaluationMetrics.FAITHFULNESS,
                EvaluationMetrics.ANSWER_RELEVANCY,
                EvaluationMetrics.CONTEXT_PRECISION
            ]
        )
        
        print(results.summary())
        ```
    """

    def __init__(
        self,
        llm: Any = None,
        embeddings: Any = None,
        enable_llm_metrics: bool = True,
        enable_embedding_metrics: bool = True,
    ):
        """
        Initialize RAGAS evaluator.

        Args:
            llm: Language model for LLM-based metrics (faithfulness, etc.)
            embeddings: Embedding model for similarity metrics
            enable_llm_metrics: Enable metrics that require LLM
            enable_embedding_metrics: Enable metrics that require embeddings
        """
        # Wrap LLM with JSON cleaning wrapper to handle Claude's markdown responses
        self.llm = JSONCleaningLLMWrapper(llm) if llm is not None else None
        self.embeddings = embeddings
        self.enable_llm_metrics = enable_llm_metrics and llm is not None
        self.enable_embedding_metrics = enable_embedding_metrics and embeddings is not None
        
        # Lazy import of RAGAS
        self._ragas_metrics = None
        self._ragas_evaluate = None
        
        logger.info(
            f"RAGASEvaluator initialized: "
            f"LLM metrics={'enabled' if self.enable_llm_metrics else 'disabled'}, "
            f"Embedding metrics={'enabled' if self.enable_embedding_metrics else 'disabled'}"
        )
        if llm is not None:
            logger.info("LLM wrapped with JSON cleaning wrapper for RAGAS compatibility")
    
    def _init_ragas(self):
        """Lazy initialization of RAGAS components."""
        if self._ragas_metrics is not None:
            return
        
        try:
            from ragas import evaluate
            from ragas.metrics import (
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
                answer_similarity,
                answer_correctness,
            )
            
            self._ragas_evaluate = evaluate
            self._ragas_metrics = {
                EvaluationMetrics.FAITHFULNESS: faithfulness,
                EvaluationMetrics.ANSWER_RELEVANCY: answer_relevancy,
                EvaluationMetrics.CONTEXT_PRECISION: context_precision,
                EvaluationMetrics.CONTEXT_RECALL: context_recall,
                EvaluationMetrics.ANSWER_SIMILARITY: answer_similarity,
                EvaluationMetrics.ANSWER_CORRECTNESS: answer_correctness,
            }
            
            logger.info("RAGAS metrics initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import RAGAS: {e}")
            logger.error("Please install: pip install ragas")
            raise
    
    def evaluate_sync(
        self,
        dataset: "EvaluationDataset",  # type: ignore
        metrics: Optional[List[EvaluationMetrics | str]] = None,
        batch_size: int = 10,
    ) -> EvaluationResult:
        """
        同步评估方法 - 用于在线程池中运行，避免 uvloop 嵌套事件循环问题。

        Args:
            dataset: EvaluationDataset with samples to evaluate
            metrics: List of metrics to compute (None = all available)
            batch_size: Batch size for evaluation

        Returns:
            EvaluationResult with scores and metadata

        Raises:
            ValueError: If dataset is empty or metrics are invalid
        """
        return self._evaluate_internal(dataset, metrics, batch_size)
    
    async def evaluate(
        self,
        dataset: "EvaluationDataset",  # type: ignore
        metrics: Optional[List[EvaluationMetrics | str]] = None,
        batch_size: int = 10,
    ) -> EvaluationResult:
        """
        异步评估方法 - 在线程池中运行同步评估以避免 uvloop 冲突。

        Args:
            dataset: EvaluationDataset with samples to evaluate
            metrics: List of metrics to compute (None = all available)
            batch_size: Batch size for evaluation

        Returns:
            EvaluationResult with scores and metadata

        Raises:
            ValueError: If dataset is empty or metrics are invalid
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._evaluate_internal, dataset, metrics, batch_size)
    
    def _evaluate_internal(
        self,
        dataset: "EvaluationDataset",  # type: ignore
        metrics: Optional[List[EvaluationMetrics | str]] = None,
        batch_size: int = 10,
    ) -> EvaluationResult:
        """
        内部评估实现（同步方法）。

        Args:
            dataset: EvaluationDataset with samples to evaluate
            metrics: List of metrics to compute (None = all available)
            batch_size: Batch size for evaluation

        Returns:
            EvaluationResult with scores and metadata

        Raises:
            ValueError: If dataset is empty or metrics are invalid
        """
        if len(dataset) == 0:
            raise ValueError("Dataset is empty")
        
        # Initialize RAGAS
        self._init_ragas()
        
        # Determine which metrics to use
        if metrics is None:
            metrics = self._get_default_metrics()
        else:
            # Convert string metrics to enum
            metrics = [
                EvaluationMetrics(m) if isinstance(m, str) else m
                for m in metrics
            ]
        
        # Validate metrics
        self._validate_metrics(metrics)
        
        # Convert dataset to RAGAS format
        eval_data = self._prepare_data(dataset)
        
        # Select RAGAS metric objects
        ragas_metrics = [self._ragas_metrics[m] for m in metrics]
        
        logger.info(f"Evaluating {len(dataset)} samples with metrics: {[m.value for m in metrics]}")
        
        try:
            # Run RAGAS evaluation
            from datasets import Dataset

            eval_dataset = Dataset.from_dict(eval_data)
            
            # Configure metrics with LLM and embeddings if needed
            logger.info(f"🔧 Configuring {len(ragas_metrics)} RAGAS metrics with wrapped LLM")
            for metric in ragas_metrics:
                metric_name = metric.__class__.__name__
                if hasattr(metric, 'llm') and self.llm:
                    metric.llm = self.llm
                    logger.info(f"   ✅ {metric_name}.llm = JSONCleaningLLMWrapper({self.llm.llm.__class__.__name__})")
                    
                    # Also set _llm if it exists (some RAGAS versions use this)
                    if hasattr(metric, '_llm'):
                        metric._llm = self.llm
                        logger.debug(f"   ✅ Also set {metric_name}._llm")
                        
                if hasattr(metric, 'embeddings') and self.embeddings:
                    metric.embeddings = self.embeddings
                    logger.debug(f"   ✅ {metric_name}.embeddings configured")

            # Run evaluation
            results = self._ragas_evaluate(
                eval_dataset,
                metrics=ragas_metrics,
            )

            # Extract scores from RAGAS result
            # Handle different RAGAS versions and return types
            if hasattr(results, 'to_pandas'):
                # RAGAS 0.1.x+ returns EvaluationResult with to_pandas()
                df = results.to_pandas()
                scores = {}
                for col in df.columns:
                    if col not in ['question', 'answer', 'contexts', 'ground_truth', 'ground_truths', 'user_input', 'retrieved_contexts', 'response', 'reference']:
                        # Calculate mean score for this metric
                        scores[col] = float(df[col].mean())
            elif isinstance(results, dict):
                # Older RAGAS versions return dict
                scores = {
                    col: float(results[col])
                    for col in results.keys()
                    if col not in ['question', 'answer', 'contexts', 'ground_truth', 'ground_truths', 'user_input', 'retrieved_contexts', 'response', 'reference']
                }
            else:
                # Fallback: try to access as attributes
                scores = {}
                for metric in metrics:
                    metric_name = metric.value
                    if hasattr(results, metric_name):
                        scores[metric_name] = float(getattr(results, metric_name))
            
            logger.info(f"Evaluation completed. Scores: {scores}")
            
            return EvaluationResult(
                scores=scores,
                metadata={
                    "num_samples": len(dataset),
                    "metrics": [m.value for m in metrics],
                    "dataset_name": dataset.name,
                }
            )

        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            raise

    def _get_default_metrics(self) -> List[EvaluationMetrics]:
        """Get default metrics based on available components."""
        metrics = []
        
        if self.enable_llm_metrics:
            metrics.extend([
                EvaluationMetrics.FAITHFULNESS,
                EvaluationMetrics.ANSWER_RELEVANCY,
                EvaluationMetrics.CONTEXT_PRECISION,
            ])
        
        if self.enable_embedding_metrics:
            metrics.extend([
                EvaluationMetrics.ANSWER_SIMILARITY,
            ])
        
        return metrics if metrics else [EvaluationMetrics.CONTEXT_PRECISION]
    
    def _validate_metrics(self, metrics: List[EvaluationMetrics]) -> None:
        """Validate that requested metrics are supported."""
        llm_metrics = {
            EvaluationMetrics.FAITHFULNESS,
            EvaluationMetrics.ANSWER_RELEVANCY,
            EvaluationMetrics.CONTEXT_PRECISION,
            EvaluationMetrics.CONTEXT_RECALL,
        }
        
        embedding_metrics = {
            EvaluationMetrics.ANSWER_SIMILARITY,
            EvaluationMetrics.ANSWER_CORRECTNESS,
        }
        
        for metric in metrics:
            if metric in llm_metrics and not self.enable_llm_metrics:
                raise ValueError(
                    f"Metric {metric.value} requires LLM but LLM is not available"
                )
            
            if metric in embedding_metrics and not self.enable_embedding_metrics:
                raise ValueError(
                    f"Metric {metric.value} requires embeddings but embeddings are not available"
                )
    
    def _prepare_data(self, dataset: "EvaluationDataset") -> Dict[str, List]:  # type: ignore
        """Prepare dataset for RAGAS evaluation."""
        data = dataset.to_ragas_format()
        
        # RAGAS requires non-empty contexts and ground_truth for certain metrics
        # Filter out samples with missing required fields
        valid_indices = []
        for i in range(len(data['question'])):
            if data['contexts'][i] and data['answer'][i]:  # Minimum requirements
                valid_indices.append(i)
        
        if not valid_indices:
            raise ValueError("No valid samples found (need question, answer, and contexts)")
        
        # Filter to valid samples
        filtered_data = {
            key: [values[i] for i in valid_indices]
            for key, values in data.items()
        }
        
        if len(valid_indices) < len(data['question']):
            logger.warning(
                f"Filtered {len(data['question']) - len(valid_indices)} samples "
                f"with missing required fields"
            )
        
        return filtered_data
    
    def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
        metrics: Optional[List[EvaluationMetrics]] = None,
    ) -> Dict[str, float]:
        """
        Evaluate a single QA sample.

        Args:
            question: User question
            answer: Generated answer
            contexts: Retrieved contexts
            ground_truth: Reference answer (optional)
            metrics: Metrics to compute

        Returns:
            Dictionary of metric scores
        """
        from rag_core.evaluation.dataset import EvaluationDataset
        
        # Create temporary dataset
        dataset = EvaluationDataset(name="temp")
        dataset.add_sample(
                    question=question,
            answer=answer,
            contexts=contexts,
            ground_truth=ground_truth
                )

        # Evaluate
        import asyncio
        result = asyncio.run(self.evaluate(dataset, metrics=metrics))

        return result.scores
