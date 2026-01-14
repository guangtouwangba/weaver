"""Evaluation logger for storing RAG evaluation results."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.database.models import EvaluationLogModel
from research_agent.shared.utils.logger import logger


class EvaluationLogger:
    """
    Logger for RAG evaluation results.

    Stores evaluation metrics to database and optionally to Loki.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize evaluation logger.

        Args:
            session: Database session
        """
        self._session = session

    async def log_evaluation(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        metrics: dict[str, float],
        project_id: UUID | None = None,
        chunking_strategy: str | None = None,
        retrieval_mode: str | None = None,
        test_case_id: str | None = None,
        ground_truth: str | None = None,
        evaluation_type: str = "realtime",
    ) -> UUID:
        """
        Log evaluation results to database and Loki.

        Args:
            question: User question
            answer: Generated answer
            contexts: Retrieved contexts
            metrics: Ragas metrics dict
            project_id: Project ID (optional for offline evaluation)
            chunking_strategy: Chunking strategy used
            retrieval_mode: Retrieval mode ('vector', 'hybrid', etc.)
            test_case_id: Test case ID (for offline evaluation)
            ground_truth: Ground truth answer (for offline evaluation)
            evaluation_type: 'realtime' or 'offline'

        Returns:
            Evaluation log ID
        """
        try:
            # Create evaluation log entry
            log_entry = EvaluationLogModel(
                project_id=project_id,
                test_case_id=test_case_id,
                question=question,
                ground_truth=ground_truth,
                chunking_strategy=chunking_strategy,
                retrieval_mode=retrieval_mode,
                retrieved_contexts=contexts,
                generated_answer=answer,
                metrics=metrics,
                evaluation_type=evaluation_type,
            )

            self._session.add(log_entry)
            await self._session.commit()
            await self._session.refresh(log_entry)

            logger.info(f"[EvalLogger] Logged evaluation: {log_entry.id} | Metrics: {metrics}")

            # Send to Loki (if configured)
            await self._log_to_loki(
                project_id=project_id,
                question=question,
                metrics=metrics,
                chunking_strategy=chunking_strategy,
                retrieval_mode=retrieval_mode,
                evaluation_type=evaluation_type,
            )

            return log_entry.id

        except Exception as e:
            logger.error(f"[EvalLogger] Failed to log evaluation: {e}", exc_info=True)
            await self._session.rollback()
            raise

    async def _log_to_loki(
        self,
        project_id: UUID | None,
        question: str,
        metrics: dict[str, float],
        chunking_strategy: str | None,
        retrieval_mode: str | None,
        evaluation_type: str,
    ):
        """
        Send evaluation metrics to Loki for monitoring.

        This creates structured logs that can be queried in Grafana.
        """
        try:
            # Format metrics for logging
            log_data = {
                "service": "rag-evaluation",
                "evaluation_type": evaluation_type,
                "project_id": str(project_id) if project_id else None,
                "question_preview": question[:100],
                "chunking_strategy": chunking_strategy,
                "retrieval_mode": retrieval_mode,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Log with structured format for Loki parsing
            logger.info(
                f"[RAG-Evaluation] {json.dumps(log_data)}",
                extra={
                    "service": "rag-evaluation",
                    **log_data
                }
            )

        except Exception as e:
            logger.warning(f"[EvalLogger] Failed to send to Loki: {e}")
            # Don't raise - Loki logging failure shouldn't break evaluation

    async def get_metrics_summary(
        self,
        project_id: UUID,
        evaluation_type: str = "realtime",
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Get summary statistics for evaluation metrics.

        Args:
            project_id: Project ID
            evaluation_type: 'realtime' or 'offline'
            limit: Number of recent evaluations to analyze

        Returns:
            Summary dict with average metrics
        """
        try:
            from sqlalchemy import select

            # Query recent evaluations
            stmt = (
                select(EvaluationLogModel)
                .where(EvaluationLogModel.project_id == project_id)
                .where(EvaluationLogModel.evaluation_type == evaluation_type)
                .order_by(EvaluationLogModel.created_at.desc())
                .limit(limit)
            )

            result = await self._session.execute(stmt)
            evaluations = result.scalars().all()

            if not evaluations:
                return {}

            # Calculate averages
            metric_keys = set()
            for eval in evaluations:
                metric_keys.update(eval.metrics.keys())

            summary = {
                "total_evaluations": len(evaluations),
                "evaluation_type": evaluation_type,
            }

            for key in metric_keys:
                values = [eval.metrics.get(key, 0) for eval in evaluations if key in eval.metrics]
                if values:
                    summary[f"avg_{key}"] = sum(values) / len(values)
                    summary[f"min_{key}"] = min(values)
                    summary[f"max_{key}"] = max(values)

            logger.info(f"[EvalLogger] Metrics summary: {summary}")
            return summary

        except Exception as e:
            logger.error(f"[EvalLogger] Failed to get metrics summary: {e}", exc_info=True)
            return {}

