"""Evaluation dataset management for RAG system."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EvaluationSample(BaseModel):
    """
    Single evaluation sample for RAG system.
    
    Attributes:
        question: User query/question
        answer: Generated answer from RAG system
        contexts: Retrieved context chunks used for generation
        ground_truth: Reference answer (optional, for answer quality evaluation)
        reference_contexts: Ground truth relevant contexts (optional)
        metadata: Additional metadata (topic, difficulty, etc.)
    """
    
    question: str = Field(..., description="User query or question")
    answer: str = Field(..., description="Generated answer from RAG system")
    contexts: List[str] = Field(default_factory=list, description="Retrieved context chunks")
    ground_truth: Optional[str] = Field(None, description="Reference answer for comparison")
    reference_contexts: Optional[List[str]] = Field(None, description="Ground truth relevant contexts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = {"json_schema_extra": {
        "example": {
            "question": "What is machine learning?",
            "answer": "Machine learning is a subset of AI that enables systems to learn from data.",
            "contexts": [
                "Machine learning (ML) is a field of study in artificial intelligence...",
                "ML algorithms build models based on sample data..."
            ],
            "ground_truth": "Machine learning is a method of data analysis that automates analytical model building.",
            "metadata": {"topic": "ai_basics", "difficulty": "easy"}
        }
    }}


class EvaluationDataset(BaseModel):
    """
    Collection of evaluation samples.
    
    Provides methods to:
    - Load/save datasets from/to JSON
    - Add/remove samples
    - Convert to RAGAS format
    - Split into train/test
    """
    
    samples: List[EvaluationSample] = Field(default_factory=list, description="List of evaluation samples")
    name: str = Field("evaluation_dataset", description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Dataset-level metadata")
    
    def add_sample(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
        reference_contexts: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a new evaluation sample.
        
        Args:
            question: User question
            answer: Generated answer
            contexts: Retrieved contexts
            ground_truth: Reference answer (optional)
            reference_contexts: Ground truth contexts (optional)
            metadata: Sample metadata (optional)
        """
        sample = EvaluationSample(
            question=question,
            answer=answer,
            contexts=contexts,
            ground_truth=ground_truth,
            reference_contexts=reference_contexts,
            metadata=metadata or {}
        )
        self.samples.append(sample)
        logger.debug(f"Added sample: {question[:50]}...")
    
    def save(self, filepath: Path | str) -> None:
        """
        Save dataset to JSON file.
        
        Args:
            filepath: Path to save the dataset
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved dataset with {len(self.samples)} samples to {filepath}")
    
    @classmethod
    def load(cls, filepath: Path | str) -> "EvaluationDataset":
        """
        Load dataset from JSON file.
        
        Args:
            filepath: Path to the dataset file
        
        Returns:
            EvaluationDataset instance
        """
        filepath = Path(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        dataset = cls(**data)
        logger.info(f"Loaded dataset with {len(dataset.samples)} samples from {filepath}")
        return dataset
    
    def to_ragas_format(self) -> Dict[str, List]:
        """
        Convert dataset to RAGAS evaluation format.
        
        Returns:
            Dictionary with keys: question, answer, contexts, ground_truth, ground_truths
        """
        return {
            "question": [s.question for s in self.samples],
            "answer": [s.answer for s in self.samples],
            "contexts": [s.contexts for s in self.samples],
            "ground_truth": [s.ground_truth or "" for s in self.samples],
            "ground_truths": [s.reference_contexts or [] for s in self.samples],
        }
    
    def filter_by_metadata(self, key: str, value: Any) -> "EvaluationDataset":
        """
        Filter samples by metadata value.
        
        Args:
            key: Metadata key to filter by
            value: Value to match
        
        Returns:
            New EvaluationDataset with filtered samples
        """
        filtered_samples = [
            s for s in self.samples
            if s.metadata.get(key) == value
        ]
        
        return EvaluationDataset(
            samples=filtered_samples,
            name=f"{self.name}_filtered_{key}_{value}",
            description=f"Filtered by {key}={value}",
            metadata={**self.metadata, "filter": {key: value}}
        )
    
    def split(self, test_size: float = 0.2, random_state: int = 42) -> tuple["EvaluationDataset", "EvaluationDataset"]:
        """
        Split dataset into train and test sets.
        
        Args:
            test_size: Proportion of test set (0-1)
            random_state: Random seed for reproducibility
        
        Returns:
            Tuple of (train_dataset, test_dataset)
        """
        import random
        
        random.seed(random_state)
        indices = list(range(len(self.samples)))
        random.shuffle(indices)
        
        split_idx = int(len(indices) * (1 - test_size))
        train_indices = indices[:split_idx]
        test_indices = indices[split_idx:]
        
        train_samples = [self.samples[i] for i in train_indices]
        test_samples = [self.samples[i] for i in test_indices]
        
        train_dataset = EvaluationDataset(
            samples=train_samples,
            name=f"{self.name}_train",
            description=f"Train split ({len(train_samples)} samples)",
            metadata={**self.metadata, "split": "train"}
        )
        
        test_dataset = EvaluationDataset(
            samples=test_samples,
            name=f"{self.name}_test",
            description=f"Test split ({len(test_samples)} samples)",
            metadata={**self.metadata, "split": "test"}
        )
        
        return train_dataset, test_dataset
    
    def __len__(self) -> int:
        """Get number of samples."""
        return len(self.samples)
    
    def __getitem__(self, index: int) -> EvaluationSample:
        """Get sample by index."""
        return self.samples[index]
    
    def __repr__(self) -> str:
        """String representation."""
        return f"EvaluationDataset(name='{self.name}', samples={len(self.samples)})"

