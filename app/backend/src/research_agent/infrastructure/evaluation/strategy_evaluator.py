"""Strategy evaluator for comparing different chunking and retrieval strategies."""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.application.graphs.rag_graph import stream_rag_response
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.evaluation.evaluation_logger import EvaluationLogger
from research_agent.infrastructure.evaluation.ragas_service import RagasEvaluationService
from research_agent.infrastructure.evaluation.retrieval_metrics import (
    RetrievalMetrics,
    RetrievalMetricsResult,
)
from research_agent.infrastructure.evaluation.test_dataset import TestCase, TestDataset
from research_agent.infrastructure.vector_store.factory import get_vector_store
from research_agent.infrastructure.vector_store.langchain_pgvector import create_pgvector_retriever
from research_agent.shared.utils.logger import logger


@dataclass
class StrategyResult:
    """Result of evaluating a single strategy."""

    strategy_name: str
    retrieval_mode: str

    # Retrieval metrics
    hit_rate: float = 0.0
    mrr: float = 0.0
    precision_at_k: float = 0.0
    recall_at_k: float = 0.0
    ndcg_at_k: float = 0.0

    # Ragas metrics (averaged)
    faithfulness: float = 0.0
    answer_relevancy: float = 0.0
    context_precision: float = 0.0

    # Additional info
    num_test_cases: int = 0
    errors: List[str] = field(default_factory=list)


class StrategyEvaluator:
    """
    Evaluator for comparing different chunking and retrieval strategies.

    Usage:
        evaluator = StrategyEvaluator(test_dataset, session, embedding_service, llm)
        results = await evaluator.evaluate_all_strategies(project_id)

        # Print comparison
        evaluator.print_comparison(results)
    """

    def __init__(
        self,
        test_dataset: TestDataset,
        session: AsyncSession,
        embedding_service: EmbeddingService,
        llm,
        k: int = 5,
    ):
        """
        Initialize strategy evaluator.

        Args:
            test_dataset: Test dataset with test cases
            session: Database session
            embedding_service: Embedding service
            llm: LLM for generation and evaluation
            k: Number of top results to consider for metrics
        """
        self.test_dataset = test_dataset
        self.session = session
        self.embedding_service = embedding_service
        self.llm = llm
        self.k = k

        self.ragas_service = RagasEvaluationService(llm=llm, embeddings=embedding_service)
        self.evaluation_logger = EvaluationLogger(session)

    async def evaluate_strategy(
        self,
        strategy_name: str,
        retrieval_mode: str,
        project_id: UUID,
    ) -> StrategyResult:
        """
        Evaluate a single strategy.

        Args:
            strategy_name: Name of chunking strategy
            retrieval_mode: 'vector' or 'hybrid'
            project_id: Project ID containing the documents

        Returns:
            StrategyResult with all metrics
        """
        logger.info(f"Evaluating strategy: {strategy_name} + {retrieval_mode}")

        result = StrategyResult(
            strategy_name=strategy_name,
            retrieval_mode=retrieval_mode,
            num_test_cases=len(self.test_dataset.test_cases),
        )

        # For retrieval metrics
        all_retrieved_doc_ids = []
        all_relevant_doc_ids = []

        # For Ragas metrics
        ragas_metrics_list = []

        # Create retriever
        vector_store = get_vector_store(self.session)
        use_hybrid = retrieval_mode == "hybrid"
        retriever = create_pgvector_retriever(
            vector_store=vector_store,
            embedding_service=self.embedding_service,
            project_id=project_id,
            k=self.k,
            use_hybrid_search=use_hybrid,
        )

        # Process each test case
        for test_case in self.test_dataset.test_cases:
            try:
                # Retrieve documents
                retrieved_docs = await retriever._aget_relevant_documents(test_case.question)
                retrieved_doc_ids = [doc.metadata.get("document_id") for doc in retrieved_docs]
                retrieved_contexts = [doc.page_content for doc in retrieved_docs]

                # Store for retrieval metrics
                all_retrieved_doc_ids.append(retrieved_doc_ids)
                all_relevant_doc_ids.append(test_case.relevant_document_ids)

                # Generate answer using RAG
                answer = ""
                async for event in stream_rag_response(
                    question=test_case.question,
                    retriever=retriever,
                    llm=self.llm,
                    chat_history=[],
                    use_rewrite=False,
                    use_rerank=False,
                    use_grading=True,
                ):
                    if event["type"] == "token":
                        answer += event.get("content", "")

                # Evaluate with Ragas
                if answer and retrieved_contexts:
                    ragas_metrics = await self.ragas_service.evaluate_single(
                        question=test_case.question,
                        answer=answer,
                        contexts=retrieved_contexts,
                        ground_truth=test_case.ground_truth,
                    )
                    ragas_metrics_list.append(ragas_metrics)

                    # Log to database
                    await self.evaluation_logger.log_evaluation(
                        question=test_case.question,
                        answer=answer,
                        contexts=retrieved_contexts,
                        metrics=ragas_metrics,
                        project_id=project_id,
                        chunking_strategy=strategy_name,
                        retrieval_mode=retrieval_mode,
                        test_case_id=test_case.id,
                        ground_truth=test_case.ground_truth,
                        evaluation_type="offline",
                    )

                logger.debug(
                    f"Evaluated test case {test_case.id}: {len(retrieved_docs)} docs retrieved"
                )

            except Exception as e:
                logger.error(f"Error evaluating test case {test_case.id}: {e}", exc_info=True)
                result.errors.append(f"{test_case.id}: {str(e)}")

        # Calculate retrieval metrics
        retrieval_metrics = RetrievalMetrics.calculate_all_metrics(
            retrieved_doc_ids_list=all_retrieved_doc_ids,
            relevant_doc_ids_list=all_relevant_doc_ids,
            k=self.k,
        )

        result.hit_rate = retrieval_metrics.hit_rate
        result.mrr = retrieval_metrics.mrr
        result.precision_at_k = retrieval_metrics.precision_at_k
        result.recall_at_k = retrieval_metrics.recall_at_k
        result.ndcg_at_k = retrieval_metrics.ndcg_at_k

        # Average Ragas metrics
        if ragas_metrics_list:
            result.faithfulness = sum(m.get("faithfulness", 0) for m in ragas_metrics_list) / len(
                ragas_metrics_list
            )
            result.answer_relevancy = sum(
                m.get("answer_relevancy", 0) for m in ragas_metrics_list
            ) / len(ragas_metrics_list)
            result.context_precision = sum(
                m.get("context_precision", 0) for m in ragas_metrics_list
            ) / len(ragas_metrics_list)

        logger.info(
            f"Strategy {strategy_name} + {retrieval_mode} results: "
            f"HR={result.hit_rate:.3f}, MRR={result.mrr:.3f}, "
            f"Faithfulness={result.faithfulness:.3f}"
        )

        return result

    async def evaluate_all_strategies(
        self,
        project_id: UUID,
    ) -> List[StrategyResult]:
        """
        Evaluate all strategy combinations.

        Args:
            project_id: Project ID

        Returns:
            List of StrategyResult for all combinations
        """
        results = []

        for strategy in self.test_dataset.evaluation_strategies:
            for mode in self.test_dataset.retrieval_modes:
                result = await self.evaluate_strategy(
                    strategy_name=strategy.name,
                    retrieval_mode=mode.name,
                    project_id=project_id,
                )
                results.append(result)

        return results

    @staticmethod
    def print_comparison(results: List[StrategyResult]):
        """
        Print comparison table of all strategy results.

        Args:
            results: List of StrategyResult
        """
        print("\n" + "=" * 120)
        print("STRATEGY COMPARISON")
        print("=" * 120)

        # Header
        print(
            f"{'Strategy':<20} {'Mode':<10} {'HR@5':<8} {'MRR':<8} {'P@5':<8} {'R@5':<8} "
            f"{'NDCG':<8} {'Faith':<8} {'A.Rel':<8} {'C.Pre':<8}"
        )
        print("-" * 120)

        # Sort by Hit Rate (descending)
        sorted_results = sorted(results, key=lambda x: x.hit_rate, reverse=True)

        for r in sorted_results:
            print(
                f"{r.strategy_name:<20} {r.retrieval_mode:<10} "
                f"{r.hit_rate:>6.3f}  {r.mrr:>6.3f}  {r.precision_at_k:>6.3f}  {r.recall_at_k:>6.3f}  "
                f"{r.ndcg_at_k:>6.3f}  {r.faithfulness:>6.3f}  "
                f"{r.answer_relevancy:>6.3f}  {r.context_precision:>6.3f}"
            )

            if r.errors:
                print(f"  ⚠️  Errors: {len(r.errors)}")

        print("=" * 120)

        # Highlight best strategies
        best_hr = max(results, key=lambda x: x.hit_rate)
        best_mrr = max(results, key=lambda x: x.mrr)
        best_faith = max(results, key=lambda x: x.faithfulness)

        print(
            f"\n🏆 Best Hit Rate: {best_hr.strategy_name} + {best_hr.retrieval_mode} ({best_hr.hit_rate:.3f})"
        )
        print(
            f"🏆 Best MRR: {best_mrr.strategy_name} + {best_mrr.retrieval_mode} ({best_mrr.mrr:.3f})"
        )
        print(
            f"🏆 Best Faithfulness: {best_faith.strategy_name} + {best_faith.retrieval_mode} ({best_faith.faithfulness:.3f})"
        )
        print()

    @staticmethod
    def export_to_csv(results: List[StrategyResult], file_path: str):
        """Export results to CSV file."""
        import csv

        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "strategy",
                    "mode",
                    "hit_rate",
                    "mrr",
                    "precision",
                    "recall",
                    "ndcg",
                    "faithfulness",
                    "answer_relevancy",
                    "context_precision",
                    "num_errors",
                ],
            )
            writer.writeheader()

            for r in results:
                writer.writerow(
                    {
                        "strategy": r.strategy_name,
                        "mode": r.retrieval_mode,
                        "hit_rate": r.hit_rate,
                        "mrr": r.mrr,
                        "precision": r.precision_at_k,
                        "recall": r.recall_at_k,
                        "ndcg": r.ndcg_at_k,
                        "faithfulness": r.faithfulness,
                        "answer_relevancy": r.answer_relevancy,
                        "context_precision": r.context_precision,
                        "num_errors": len(r.errors),
                    }
                )

        logger.info(f"Results exported to {file_path}")
