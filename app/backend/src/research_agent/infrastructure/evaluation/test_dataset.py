"""Test dataset management for RAG evaluation."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from research_agent.shared.utils.logger import logger


@dataclass
class TestCase:
    """Test case for RAG evaluation."""

    id: str
    question: str
    ground_truth: str
    relevant_document_ids: list[str]
    category: str | None = None
    difficulty: str | None = None
    expected_context_keywords: list[str] | None = None


@dataclass
class EvaluationStrategy:
    """Chunking strategy configuration."""

    name: str
    description: str
    config: dict[str, Any]


@dataclass
class RetrievalMode:
    """Retrieval mode configuration."""

    name: str
    description: str


class TestDataset:
    """
    Test dataset for RAG evaluation.

    Manages test cases and evaluation configurations.
    """

    def __init__(
        self,
        test_cases: list[TestCase],
        evaluation_strategies: list[EvaluationStrategy],
        retrieval_modes: list[RetrievalMode],
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize test dataset.

        Args:
            test_cases: List of test cases
            evaluation_strategies: List of chunking strategies to evaluate
            retrieval_modes: List of retrieval modes to test
            metadata: Optional dataset metadata
        """
        self.test_cases = test_cases
        self.evaluation_strategies = evaluation_strategies
        self.retrieval_modes = retrieval_modes
        self.metadata = metadata or {}

    @classmethod
    def from_json(cls, file_path: str | Path) -> "TestDataset":
        """
        Load test dataset from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            TestDataset instance
        """
        with open(file_path) as f:
            data = json.load(f)

        # Parse test cases
        test_cases = [
            TestCase(
                id=tc["id"],
                question=tc["question"],
                ground_truth=tc["ground_truth"],
                relevant_document_ids=tc.get("relevant_document_ids", []),
                category=tc.get("category"),
                difficulty=tc.get("difficulty"),
                expected_context_keywords=tc.get("expected_context_keywords"),
            )
            for tc in data.get("test_cases", [])
        ]

        # Parse evaluation strategies
        strategies = [
            EvaluationStrategy(
                name=s["name"],
                description=s["description"],
                config=s.get("config", {}),
            )
            for s in data.get("evaluation_strategies", [])
        ]

        # Parse retrieval modes
        modes = [
            RetrievalMode(
                name=m["name"],
                description=m["description"],
            )
            for m in data.get("retrieval_modes", [])
        ]

        logger.info(f"Loaded test dataset: {len(test_cases)} test cases, "
                   f"{len(strategies)} strategies, {len(modes)} retrieval modes")

        return cls(
            test_cases=test_cases,
            evaluation_strategies=strategies,
            retrieval_modes=modes,
            metadata=data.get("metadata", {}),
        )

    def to_json(self, file_path: str | Path):
        """
        Save test dataset to JSON file.

        Args:
            file_path: Path to save JSON file
        """
        data = {
            "metadata": self.metadata,
            "test_cases": [
                {
                    "id": tc.id,
                    "question": tc.question,
                    "ground_truth": tc.ground_truth,
                    "relevant_document_ids": tc.relevant_document_ids,
                    "category": tc.category,
                    "difficulty": tc.difficulty,
                    "expected_context_keywords": tc.expected_context_keywords,
                }
                for tc in self.test_cases
            ],
            "evaluation_strategies": [
                {
                    "name": s.name,
                    "description": s.description,
                    "config": s.config,
                }
                for s in self.evaluation_strategies
            ],
            "retrieval_modes": [
                {
                    "name": m.name,
                    "description": m.description,
                }
                for m in self.retrieval_modes
            ],
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved test dataset to {file_path}")

    def filter_by_category(self, category: str) -> "TestDataset":
        """Filter test cases by category."""
        filtered_cases = [tc for tc in self.test_cases if tc.category == category]
        return TestDataset(
            test_cases=filtered_cases,
            evaluation_strategies=self.evaluation_strategies,
            retrieval_modes=self.retrieval_modes,
            metadata={**self.metadata, "filtered_by": f"category={category}"},
        )

    def filter_by_difficulty(self, difficulty: str) -> "TestDataset":
        """Filter test cases by difficulty."""
        filtered_cases = [tc for tc in self.test_cases if tc.difficulty == difficulty]
        return TestDataset(
            test_cases=filtered_cases,
            evaluation_strategies=self.evaluation_strategies,
            retrieval_modes=self.retrieval_modes,
            metadata={**self.metadata, "filtered_by": f"difficulty={difficulty}"},
        )

