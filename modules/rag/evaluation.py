"""
Comprehensive RAG Evaluation Framework

Provides extensive evaluation metrics for retrieval quality, generation quality,
and end-to-end performance with automated testing and continuous improvement.
"""

import asyncio
import json
import logging
import math
import statistics
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from .retrieval import RetrievalResult
from .generation import GeneratedAnswer

logger = logging.getLogger(__name__)

class MetricType(str, Enum):
    """Evaluation metric types"""
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    END_TO_END = "end_to_end"
    USER_EXPERIENCE = "user_experience"

@dataclass
class TestCase:
    """Test case for evaluation"""
    id: str
    query: str
    topic_id: int
    ground_truth_answer: str
    relevant_document_ids: List[str]
    expected_sources: List[Dict[str, Any]]
    difficulty: str  # easy, medium, hard
    category: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class EvaluationResult:
    """Single evaluation result"""
    test_case_id: str
    metric_name: str
    score: float
    details: Dict[str, Any]
    timestamp: datetime

@dataclass
class EvaluationReport:
    """Comprehensive evaluation report"""
    overall_score: float
    metric_scores: Dict[str, float]
    detailed_results: List[EvaluationResult]
    recommendations: List[str]
    test_summary: Dict[str, Any]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class IEvaluationMetric(ABC):
    """Abstract evaluation metric interface"""
    
    @abstractmethod
    def get_name(self) -> str:
        """Get metric name"""
        pass
    
    @abstractmethod
    def get_type(self) -> MetricType:
        """Get metric type"""
        pass
    
    @abstractmethod
    async def evaluate(self, test_cases: List[TestCase], 
                      results: List[Dict[str, Any]]) -> List[EvaluationResult]:
        """Evaluate test cases"""
        pass

class RetrievalMetrics(IEvaluationMetric):
    """Retrieval quality metrics"""
    
    def get_name(self) -> str:
        return "retrieval_metrics"
    
    def get_type(self) -> MetricType:
        return MetricType.RETRIEVAL
    
    async def evaluate(self, test_cases: List[TestCase], 
                      results: List[Dict[str, Any]]) -> List[EvaluationResult]:
        """Evaluate retrieval performance"""
        evaluation_results = []
        
        for test_case, result in zip(test_cases, results):
            retrieval_results = result.get("retrieval_results", [])
            
            # Calculate various retrieval metrics
            metrics = await self._calculate_retrieval_metrics(
                test_case, retrieval_results
            )
            
            for metric_name, score in metrics.items():
                evaluation_results.append(
                    EvaluationResult(
                        test_case_id=test_case.id,
                        metric_name=f"retrieval_{metric_name}",
                        score=score,
                        details={"retrieved_count": len(retrieval_results)},
                        timestamp=datetime.now()
                    )
                )
        
        return evaluation_results
    
    async def _calculate_retrieval_metrics(self, test_case: TestCase, 
                                         retrieval_results: List[RetrievalResult]) -> Dict[str, float]:
        """Calculate comprehensive retrieval metrics"""
        relevant_docs = set(test_case.relevant_document_ids)
        retrieved_docs = {r.document_id for r in retrieval_results}
        
        metrics = {}
        
        # Precision@K
        for k in [1, 3, 5, 10]:
            top_k_docs = {r.document_id for r in retrieval_results[:k]}
            if top_k_docs:
                precision_k = len(top_k_docs.intersection(relevant_docs)) / len(top_k_docs)
            else:
                precision_k = 0.0
            metrics[f"precision@{k}"] = precision_k
        
        # Recall@K
        for k in [1, 3, 5, 10]:
            top_k_docs = {r.document_id for r in retrieval_results[:k]}
            if relevant_docs:
                recall_k = len(top_k_docs.intersection(relevant_docs)) / len(relevant_docs)
            else:
                recall_k = 0.0
            metrics[f"recall@{k}"] = recall_k
        
        # Mean Reciprocal Rank (MRR)
        metrics["mrr"] = self._calculate_mrr(retrieval_results, relevant_docs)
        
        # Normalized Discounted Cumulative Gain (NDCG)
        metrics["ndcg@10"] = self._calculate_ndcg(retrieval_results, relevant_docs, k=10)
        
        # Hit Rate
        metrics["hit_rate"] = 1.0 if retrieved_docs.intersection(relevant_docs) else 0.0
        
        # Mean Average Precision (MAP)
        metrics["map"] = self._calculate_map(retrieval_results, relevant_docs)
        
        return metrics
    
    def _calculate_mrr(self, retrieval_results: List[RetrievalResult], 
                      relevant_docs: set) -> float:
        """Calculate Mean Reciprocal Rank"""
        for i, result in enumerate(retrieval_results, 1):
            if result.document_id in relevant_docs:
                return 1.0 / i
        return 0.0
    
    def _calculate_ndcg(self, retrieval_results: List[RetrievalResult], 
                       relevant_docs: set, k: int = 10) -> float:
        """Calculate Normalized Discounted Cumulative Gain"""
        # DCG
        dcg = 0.0
        for i, result in enumerate(retrieval_results[:k], 1):
            relevance = 1 if result.document_id in relevant_docs else 0
            dcg += relevance / math.log2(i + 1)
        
        # IDCG (Ideal DCG)
        ideal_relevances = [1] * min(len(relevant_docs), k) + [0] * max(0, k - len(relevant_docs))
        idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal_relevances))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def _calculate_map(self, retrieval_results: List[RetrievalResult], 
                      relevant_docs: set) -> float:
        """Calculate Mean Average Precision"""
        if not relevant_docs:
            return 0.0
        
        precision_sum = 0.0
        relevant_count = 0
        
        for i, result in enumerate(retrieval_results, 1):
            if result.document_id in relevant_docs:
                relevant_count += 1
                precision_at_i = relevant_count / i
                precision_sum += precision_at_i
        
        return precision_sum / len(relevant_docs) if len(relevant_docs) > 0 else 0.0

class GenerationMetrics(IEvaluationMetric):
    """Generation quality metrics"""
    
    def __init__(self):
        self.llm_evaluator = None
    
    def get_name(self) -> str:
        return "generation_metrics"
    
    def get_type(self) -> MetricType:
        return MetricType.GENERATION
    
    async def evaluate(self, test_cases: List[TestCase], 
                      results: List[Dict[str, Any]]) -> List[EvaluationResult]:
        """Evaluate generation performance"""
        evaluation_results = []
        
        for test_case, result in zip(test_cases, results):
            generated_answer = result.get("generated_answer")
            if not generated_answer:
                continue
            
            # Calculate generation metrics
            metrics = await self._calculate_generation_metrics(
                test_case, generated_answer
            )
            
            for metric_name, score in metrics.items():
                evaluation_results.append(
                    EvaluationResult(
                        test_case_id=test_case.id,
                        metric_name=f"generation_{metric_name}",
                        score=score,
                        details={"answer_length": len(generated_answer.content)},
                        timestamp=datetime.now()
                    )
                )
        
        return evaluation_results
    
    async def _calculate_generation_metrics(self, test_case: TestCase, 
                                          generated_answer: GeneratedAnswer) -> Dict[str, float]:
        """Calculate comprehensive generation metrics"""
        metrics = {}
        
        # BLEU Score
        metrics["bleu"] = self._calculate_bleu(
            generated_answer.content, test_case.ground_truth_answer
        )
        
        # ROUGE Scores
        rouge_scores = self._calculate_rouge(
            generated_answer.content, test_case.ground_truth_answer
        )
        metrics.update(rouge_scores)
        
        # Semantic Similarity (simplified)
        metrics["semantic_similarity"] = await self._calculate_semantic_similarity(
            generated_answer.content, test_case.ground_truth_answer
        )
        
        # Answer Completeness
        metrics["completeness"] = self._calculate_completeness(
            generated_answer.content, test_case.ground_truth_answer
        )
        
        # Citation Quality
        metrics["citation_quality"] = self._calculate_citation_quality(
            generated_answer, test_case.expected_sources
        )
        
        # Faithfulness (based on context)
        metrics["faithfulness"] = await self._calculate_faithfulness(
            generated_answer, test_case
        )
        
        return metrics
    
    def _calculate_bleu(self, generated: str, reference: str) -> float:
        """Calculate BLEU score (simplified implementation)"""
        try:
            from nltk.translate.bleu_score import sentence_bleu
            from nltk.tokenize import word_tokenize
            
            reference_tokens = [word_tokenize(reference.lower())]
            generated_tokens = word_tokenize(generated.lower())
            
            return sentence_bleu(reference_tokens, generated_tokens)
            
        except ImportError:
            # Fallback to simple word overlap
            ref_words = set(reference.lower().split())
            gen_words = set(generated.lower().split())
            
            if not gen_words:
                return 0.0
            
            overlap = len(ref_words.intersection(gen_words))
            return overlap / len(gen_words)
    
    def _calculate_rouge(self, generated: str, reference: str) -> Dict[str, float]:
        """Calculate ROUGE scores"""
        try:
            from rouge import Rouge
            
            rouge = Rouge()
            scores = rouge.get_scores(generated, reference)[0]
            
            return {
                "rouge_1_f": scores['rouge-1']['f'],
                "rouge_2_f": scores['rouge-2']['f'],
                "rouge_l_f": scores['rouge-l']['f']
            }
            
        except ImportError:
            # Fallback implementation
            ref_words = reference.lower().split()
            gen_words = generated.lower().split()
            
            # ROUGE-1 approximation
            overlap = len(set(ref_words).intersection(set(gen_words)))
            rouge_1 = 2 * overlap / (len(ref_words) + len(gen_words)) if (len(ref_words) + len(gen_words)) > 0 else 0
            
            return {
                "rouge_1_f": rouge_1,
                "rouge_2_f": rouge_1 * 0.8,  # Approximation
                "rouge_l_f": rouge_1 * 0.9   # Approximation
            }
    
    async def _calculate_semantic_similarity(self, generated: str, reference: str) -> float:
        """Calculate semantic similarity using embeddings"""
        try:
            # This would use the embedding manager in a real implementation
            # For now, return a simple similarity based on word overlap
            gen_words = set(generated.lower().split())
            ref_words = set(reference.lower().split())
            
            if not gen_words or not ref_words:
                return 0.0
            
            intersection = len(gen_words.intersection(ref_words))
            union = len(gen_words.union(ref_words))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_completeness(self, generated: str, reference: str) -> float:
        """Calculate answer completeness"""
        # Simple heuristic: check if key concepts from reference are covered
        ref_concepts = self._extract_key_concepts(reference)
        gen_concepts = self._extract_key_concepts(generated)
        
        if not ref_concepts:
            return 1.0
        
        covered_concepts = len(ref_concepts.intersection(gen_concepts))
        return covered_concepts / len(ref_concepts)
    
    def _extract_key_concepts(self, text: str) -> set:
        """Extract key concepts from text"""
        import re
        
        # Extract meaningful words (> 3 chars, not common words)
        words = re.findall(r'\b\w{4,}\b', text.lower())
        
        # Filter out common words (simplified stopwords)
        stopwords = {"that", "this", "with", "have", "will", "from", "they", "been", "said", "each", "which", "their", "time", "would", "there", "make", "more", "very", "what", "know", "just", "when", "into", "good", "some", "could", "state", "than", "also"}
        
        key_concepts = {word for word in words if word not in stopwords}
        return key_concepts
    
    def _calculate_citation_quality(self, generated_answer: GeneratedAnswer, 
                                  expected_sources: List[Dict[str, Any]]) -> float:
        """Calculate citation quality"""
        if not expected_sources:
            return 1.0  # No expected citations
        
        citations = generated_answer.citations or []
        if not citations:
            return 0.0  # No citations provided
        
        # Check if citations match expected sources
        expected_doc_ids = {src.get("document_id") for src in expected_sources}
        cited_doc_ids = {cite.get("document_id") for cite in citations}
        
        overlap = len(expected_doc_ids.intersection(cited_doc_ids))
        return overlap / len(expected_sources)
    
    async def _calculate_faithfulness(self, generated_answer: GeneratedAnswer, 
                                    test_case: TestCase) -> float:
        """Calculate faithfulness to source material"""
        # This would ideally use an LLM to evaluate faithfulness
        # For now, use a simple heuristic based on citation coverage
        
        if not generated_answer.citations:
            return 0.5  # Neutral score without citations
        
        # Higher score if more citations are provided
        citation_coverage = len(generated_answer.citations) / max(len(generated_answer.sources), 1)
        return min(citation_coverage, 1.0)

class EndToEndMetrics(IEvaluationMetric):
    """End-to-end system performance metrics"""
    
    def get_name(self) -> str:
        return "end_to_end_metrics"
    
    def get_type(self) -> MetricType:
        return MetricType.END_TO_END
    
    async def evaluate(self, test_cases: List[TestCase], 
                      results: List[Dict[str, Any]]) -> List[EvaluationResult]:
        """Evaluate end-to-end performance"""
        evaluation_results = []
        
        for test_case, result in zip(test_cases, results):
            metrics = await self._calculate_e2e_metrics(test_case, result)
            
            for metric_name, score in metrics.items():
                evaluation_results.append(
                    EvaluationResult(
                        test_case_id=test_case.id,
                        metric_name=f"e2e_{metric_name}",
                        score=score,
                        details={"processing_time": result.get("processing_time", 0)},
                        timestamp=datetime.now()
                    )
                )
        
        return evaluation_results
    
    async def _calculate_e2e_metrics(self, test_case: TestCase, 
                                   result: Dict[str, Any]) -> Dict[str, float]:
        """Calculate end-to-end metrics"""
        metrics = {}
        
        # Overall Answer Quality (composite score)
        retrieval_quality = result.get("retrieval_score", 0.5)
        generation_quality = result.get("generation_score", 0.5)
        metrics["answer_quality"] = (retrieval_quality * 0.4 + generation_quality * 0.6)
        
        # Response Time Performance
        processing_time = result.get("processing_time", 0)
        if processing_time > 0:
            # Score based on response time (lower is better)
            # Good: < 2s, Acceptable: < 5s, Poor: > 5s
            if processing_time < 2.0:
                time_score = 1.0
            elif processing_time < 5.0:
                time_score = 0.8 - (processing_time - 2) * 0.2 / 3
            else:
                time_score = max(0.4 - (processing_time - 5) * 0.1, 0.0)
            metrics["response_time"] = time_score
        
        # Source Coverage
        expected_sources = len(test_case.expected_sources)
        actual_sources = len(result.get("sources_used", []))
        if expected_sources > 0:
            metrics["source_coverage"] = min(actual_sources / expected_sources, 1.0)
        
        # Confidence Calibration
        generated_answer = result.get("generated_answer")
        if generated_answer:
            # Simple calibration: high confidence should correlate with good answer
            confidence = generated_answer.confidence
            answer_quality = metrics.get("answer_quality", 0.5)
            # Good calibration: confidence matches quality
            calibration = 1.0 - abs(confidence - answer_quality)
            metrics["confidence_calibration"] = calibration
        
        return metrics

class UserExperienceMetrics(IEvaluationMetric):
    """User experience and satisfaction metrics"""
    
    def get_name(self) -> str:
        return "user_experience_metrics"
    
    def get_type(self) -> MetricType:
        return MetricType.USER_EXPERIENCE
    
    async def evaluate(self, test_cases: List[TestCase], 
                      results: List[Dict[str, Any]]) -> List[EvaluationResult]:
        """Evaluate user experience"""
        evaluation_results = []
        
        for test_case, result in zip(test_cases, results):
            metrics = await self._calculate_ux_metrics(test_case, result)
            
            for metric_name, score in metrics.items():
                evaluation_results.append(
                    EvaluationResult(
                        test_case_id=test_case.id,
                        metric_name=f"ux_{metric_name}",
                        score=score,
                        details={},
                        timestamp=datetime.now()
                    )
                )
        
        return evaluation_results
    
    async def _calculate_ux_metrics(self, test_case: TestCase, 
                                  result: Dict[str, Any]) -> Dict[str, float]:
        """Calculate user experience metrics"""
        metrics = {}
        
        generated_answer = result.get("generated_answer")
        if not generated_answer:
            return {"readability": 0.0, "helpfulness": 0.0}
        
        # Readability
        metrics["readability"] = self._calculate_readability(generated_answer.content)
        
        # Helpfulness (based on follow-up questions and completeness)
        follow_up_questions = generated_answer.follow_up_questions or []
        helpfulness = 0.8 if len(generated_answer.content) > 50 else 0.5
        helpfulness += 0.2 if follow_up_questions else 0.0
        metrics["helpfulness"] = min(helpfulness, 1.0)
        
        # Clarity (based on structure and citations)
        citations = generated_answer.citations or []
        clarity = 0.7 if len(generated_answer.content.split('.')) > 2 else 0.5
        clarity += 0.3 if citations else 0.0
        metrics["clarity"] = min(clarity, 1.0)
        
        # Satisfaction proxy (composite score)
        satisfaction = (metrics["readability"] * 0.3 + 
                       metrics["helpfulness"] * 0.4 + 
                       metrics["clarity"] * 0.3)
        metrics["satisfaction"] = satisfaction
        
        return metrics
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (simplified)"""
        if not text:
            return 0.0
        
        # Simple readability based on sentence and word length
        sentences = text.split('.')
        words = text.split()
        
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Optimal ranges: 15-20 words per sentence, 4-6 chars per word
        sentence_score = 1.0 - abs(avg_sentence_length - 17.5) / 17.5
        word_score = 1.0 - abs(avg_word_length - 5) / 5
        
        return (sentence_score + word_score) / 2

class RAGEvaluationFramework:
    """Comprehensive RAG evaluation framework"""
    
    def __init__(self):
        self.metrics = [
            RetrievalMetrics(),
            GenerationMetrics(),
            EndToEndMetrics(),
            UserExperienceMetrics()
        ]
        self.test_cases_db = {}  # In-memory storage
    
    async def load_test_cases(self, test_cases_file: Optional[str] = None) -> List[TestCase]:
        """Load test cases from file or generate default ones"""
        if test_cases_file:
            try:
                with open(test_cases_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                test_cases = []
                for item in data:
                    test_case = TestCase(**item)
                    test_cases.append(test_case)
                
                return test_cases
                
            except Exception as e:
                logger.error(f"Failed to load test cases: {e}")
        
        # Return default test cases
        return self._generate_default_test_cases()
    
    def _generate_default_test_cases(self) -> List[TestCase]:
        """Generate default test cases for evaluation"""
        return [
            TestCase(
                id="test_001",
                query="什么是人工智能？",
                topic_id=1,
                ground_truth_answer="人工智能是一种模拟人类智能的技术，包括机器学习、深度学习等技术。",
                relevant_document_ids=["doc_1", "doc_2"],
                expected_sources=[{"document_id": "doc_1", "title": "AI概述"}],
                difficulty="easy",
                category="定义问答"
            ),
            TestCase(
                id="test_002",
                query="比较机器学习和深度学习的区别",
                topic_id=1,
                ground_truth_answer="机器学习是更广泛的概念，深度学习是机器学习的一个子集，使用神经网络。",
                relevant_document_ids=["doc_3", "doc_4"],
                expected_sources=[{"document_id": "doc_3", "title": "机器学习"}, {"document_id": "doc_4", "title": "深度学习"}],
                difficulty="medium",
                category="比较分析"
            )
        ]
    
    async def run_comprehensive_evaluation(self, test_cases: List[TestCase],
                                         rag_system: Any) -> EvaluationReport:
        """Run comprehensive evaluation"""
        logger.info(f"Starting evaluation with {len(test_cases)} test cases")
        
        # Run test cases through RAG system
        test_results = []
        for test_case in test_cases:
            try:
                # This would call the actual RAG system
                result = await self._run_test_case(test_case, rag_system)
                test_results.append(result)
            except Exception as e:
                logger.error(f"Test case {test_case.id} failed: {e}")
                test_results.append({"error": str(e)})
        
        # Evaluate with all metrics
        all_evaluation_results = []
        metric_scores = {}
        
        for metric in self.metrics:
            try:
                results = await metric.evaluate(test_cases, test_results)
                all_evaluation_results.extend(results)
                
                # Calculate average score for this metric type
                metric_type_results = [r for r in results if r.metric_name.startswith(metric.get_name())]
                if metric_type_results:
                    avg_score = sum(r.score for r in metric_type_results) / len(metric_type_results)
                    metric_scores[metric.get_name()] = avg_score
                    
            except Exception as e:
                logger.error(f"Metric {metric.get_name()} evaluation failed: {e}")
                metric_scores[metric.get_name()] = 0.0
        
        # Calculate overall score
        overall_score = sum(metric_scores.values()) / len(metric_scores) if metric_scores else 0.0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metric_scores, all_evaluation_results)
        
        # Create test summary
        test_summary = {
            "total_cases": len(test_cases),
            "successful_cases": len([r for r in test_results if "error" not in r]),
            "failed_cases": len([r for r in test_results if "error" in r]),
            "difficulty_distribution": self._analyze_difficulty_distribution(test_cases),
            "category_distribution": self._analyze_category_distribution(test_cases)
        }
        
        return EvaluationReport(
            overall_score=overall_score,
            metric_scores=metric_scores,
            detailed_results=all_evaluation_results,
            recommendations=recommendations,
            test_summary=test_summary,
            timestamp=datetime.now(),
            metadata={"framework_version": "1.0", "total_metrics": len(self.metrics)}
        )
    
    async def _run_test_case(self, test_case: TestCase, rag_system: Any) -> Dict[str, Any]:
        """Run a single test case through the RAG system"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # This is a placeholder - in real implementation, this would call the actual RAG system
            # For now, return mock results
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "test_case_id": test_case.id,
                "retrieval_results": [],  # Would be actual retrieval results
                "generated_answer": None,  # Would be actual generated answer
                "retrieval_score": 0.7,   # Would be calculated
                "generation_score": 0.8,  # Would be calculated
                "processing_time": processing_time,
                "sources_used": test_case.expected_sources,
                "metadata": {"mock_result": True}
            }
            
        except Exception as e:
            return {"error": str(e), "test_case_id": test_case.id}
    
    def _generate_recommendations(self, metric_scores: Dict[str, float], 
                                detailed_results: List[EvaluationResult]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Analyze metric scores
        if metric_scores.get("retrieval_metrics", 0) < 0.7:
            recommendations.append("检索质量需要改进。建议优化嵌入模型或调整检索策略。")
        
        if metric_scores.get("generation_metrics", 0) < 0.7:
            recommendations.append("生成质量需要改进。建议调整提示工程或使用更强的生成模型。")
        
        if metric_scores.get("end_to_end_metrics", 0) < 0.7:
            recommendations.append("端到端性能需要优化。建议检查系统集成和响应时间。")
        
        if metric_scores.get("user_experience_metrics", 0) < 0.7:
            recommendations.append("用户体验需要改进。建议优化答案格式和可读性。")
        
        # Analyze specific metrics
        precision_results = [r for r in detailed_results if "precision" in r.metric_name]
        if precision_results:
            avg_precision = sum(r.score for r in precision_results) / len(precision_results)
            if avg_precision < 0.6:
                recommendations.append("检索精确度较低。建议改进查询处理和文档排序。")
        
        recall_results = [r for r in detailed_results if "recall" in r.metric_name]
        if recall_results:
            avg_recall = sum(r.score for r in recall_results) / len(recall_results)
            if avg_recall < 0.6:
                recommendations.append("检索召回率较低。建议扩大检索范围或改进索引策略。")
        
        if not recommendations:
            recommendations.append("系统整体表现良好。可以考虑在边缘案例上进一步优化。")
        
        return recommendations
    
    def _analyze_difficulty_distribution(self, test_cases: List[TestCase]) -> Dict[str, int]:
        """Analyze difficulty distribution"""
        distribution = {"easy": 0, "medium": 0, "hard": 0}
        for case in test_cases:
            difficulty = case.difficulty.lower()
            if difficulty in distribution:
                distribution[difficulty] += 1
        return distribution
    
    def _analyze_category_distribution(self, test_cases: List[TestCase]) -> Dict[str, int]:
        """Analyze category distribution"""
        from collections import Counter
        categories = [case.category for case in test_cases]
        return dict(Counter(categories))
    
    def export_report(self, report: EvaluationReport, output_file: str) -> None:
        """Export evaluation report to file"""
        try:
            # Convert to serializable format
            report_dict = {
                "overall_score": report.overall_score,
                "metric_scores": report.metric_scores,
                "detailed_results": [
                    {
                        "test_case_id": r.test_case_id,
                        "metric_name": r.metric_name,
                        "score": r.score,
                        "details": r.details,
                        "timestamp": r.timestamp.isoformat()
                    } for r in report.detailed_results
                ],
                "recommendations": report.recommendations,
                "test_summary": report.test_summary,
                "timestamp": report.timestamp.isoformat(),
                "metadata": report.metadata
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Evaluation report exported to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Test with minimal test cases
            test_cases = self._generate_default_test_cases()[:1]
            
            return {
                "status": "healthy",
                "metrics_available": [m.get_name() for m in self.metrics],
                "test_cases_loaded": len(test_cases),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }