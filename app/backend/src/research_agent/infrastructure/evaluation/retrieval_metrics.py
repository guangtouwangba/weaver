"""Retrieval metrics for evaluating search quality."""

from typing import List, Set
from dataclasses import dataclass

from research_agent.shared.utils.logger import logger


@dataclass
class RetrievalMetricsResult:
    """Result of retrieval metrics calculation."""
    
    hit_rate: float  # Proportion of queries where at least one relevant doc is retrieved
    mrr: float  # Mean Reciprocal Rank
    precision_at_k: float  # Precision at K
    recall_at_k: float  # Recall at K
    ndcg_at_k: float  # Normalized Discounted Cumulative Gain at K


class RetrievalMetrics:
    """
    Calculate retrieval quality metrics.
    
    Metrics:
    - Hit Rate (HR@K): % of queries where at least 1 relevant doc is in top-K
    - Mean Reciprocal Rank (MRR): Average of 1/rank of first relevant doc
    - Precision@K: % of retrieved docs that are relevant
    - Recall@K: % of relevant docs that are retrieved
    - NDCG@K: Normalized Discounted Cumulative Gain
    """
    
    @staticmethod
    def calculate_hit_rate(
        retrieved_doc_ids_list: List[List[str]],
        relevant_doc_ids_list: List[List[str]],
        k: int = 5,
    ) -> float:
        """
        Calculate Hit Rate@K.
        
        Args:
            retrieved_doc_ids_list: List of retrieved document ID lists (one per query)
            relevant_doc_ids_list: List of relevant document ID lists (one per query)
            k: Number of top results to consider
        
        Returns:
            Hit rate (0.0 to 1.0)
        """
        if not retrieved_doc_ids_list:
            return 0.0
        
        hits = 0
        for retrieved, relevant in zip(retrieved_doc_ids_list, relevant_doc_ids_list):
            top_k = set(retrieved[:k])
            relevant_set = set(relevant)
            
            # Hit if any retrieved doc is relevant
            if top_k & relevant_set:  # Set intersection
                hits += 1
        
        hit_rate = hits / len(retrieved_doc_ids_list)
        logger.debug(f"Hit Rate@{k}: {hit_rate:.3f} ({hits}/{len(retrieved_doc_ids_list)})")
        return hit_rate
    
    @staticmethod
    def calculate_mrr(
        retrieved_doc_ids_list: List[List[str]],
        relevant_doc_ids_list: List[List[str]],
    ) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR).
        
        MRR is the average of the reciprocal ranks of the first relevant document.
        Higher is better (max = 1.0 if all first results are relevant).
        
        Args:
            retrieved_doc_ids_list: List of retrieved document ID lists
            relevant_doc_ids_list: List of relevant document ID lists
        
        Returns:
            MRR score (0.0 to 1.0)
        """
        if not retrieved_doc_ids_list:
            return 0.0
        
        reciprocal_ranks = []
        
        for retrieved, relevant in zip(retrieved_doc_ids_list, relevant_doc_ids_list):
            relevant_set = set(relevant)
            
            # Find rank of first relevant document
            for rank, doc_id in enumerate(retrieved, start=1):
                if doc_id in relevant_set:
                    reciprocal_ranks.append(1.0 / rank)
                    break
            else:
                # No relevant document found
                reciprocal_ranks.append(0.0)
        
        mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
        logger.debug(f"MRR: {mrr:.3f}")
        return mrr
    
    @staticmethod
    def calculate_precision_at_k(
        retrieved_doc_ids_list: List[List[str]],
        relevant_doc_ids_list: List[List[str]],
        k: int = 5,
    ) -> float:
        """
        Calculate Precision@K.
        
        Precision = (# relevant docs in top-K) / K
        
        Args:
            retrieved_doc_ids_list: List of retrieved document ID lists
            relevant_doc_ids_list: List of relevant document ID lists
            k: Number of top results to consider
        
        Returns:
            Average precision@K (0.0 to 1.0)
        """
        if not retrieved_doc_ids_list:
            return 0.0
        
        precisions = []
        
        for retrieved, relevant in zip(retrieved_doc_ids_list, relevant_doc_ids_list):
            top_k = retrieved[:k]
            relevant_set = set(relevant)
            
            # Count relevant docs in top-K
            relevant_count = sum(1 for doc_id in top_k if doc_id in relevant_set)
            precision = relevant_count / len(top_k) if top_k else 0.0
            precisions.append(precision)
        
        avg_precision = sum(precisions) / len(precisions)
        logger.debug(f"Precision@{k}: {avg_precision:.3f}")
        return avg_precision
    
    @staticmethod
    def calculate_recall_at_k(
        retrieved_doc_ids_list: List[List[str]],
        relevant_doc_ids_list: List[List[str]],
        k: int = 5,
    ) -> float:
        """
        Calculate Recall@K.
        
        Recall = (# relevant docs in top-K) / (total # relevant docs)
        
        Args:
            retrieved_doc_ids_list: List of retrieved document ID lists
            relevant_doc_ids_list: List of relevant document ID lists
            k: Number of top results to consider
        
        Returns:
            Average recall@K (0.0 to 1.0)
        """
        if not retrieved_doc_ids_list:
            return 0.0
        
        recalls = []
        
        for retrieved, relevant in zip(retrieved_doc_ids_list, relevant_doc_ids_list):
            if not relevant:
                continue
            
            top_k = retrieved[:k]
            relevant_set = set(relevant)
            
            # Count relevant docs in top-K
            relevant_count = sum(1 for doc_id in top_k if doc_id in relevant_set)
            recall = relevant_count / len(relevant_set)
            recalls.append(recall)
        
        avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
        logger.debug(f"Recall@{k}: {avg_recall:.3f}")
        return avg_recall
    
    @staticmethod
    def calculate_all_metrics(
        retrieved_doc_ids_list: List[List[str]],
        relevant_doc_ids_list: List[List[str]],
        k: int = 5,
    ) -> RetrievalMetricsResult:
        """
        Calculate all retrieval metrics.
        
        Args:
            retrieved_doc_ids_list: List of retrieved document ID lists
            relevant_doc_ids_list: List of relevant document ID lists
            k: Number of top results to consider
        
        Returns:
            RetrievalMetricsResult with all metrics
        """
        hit_rate = RetrievalMetrics.calculate_hit_rate(
            retrieved_doc_ids_list, relevant_doc_ids_list, k
        )
        
        mrr = RetrievalMetrics.calculate_mrr(
            retrieved_doc_ids_list, relevant_doc_ids_list
        )
        
        precision = RetrievalMetrics.calculate_precision_at_k(
            retrieved_doc_ids_list, relevant_doc_ids_list, k
        )
        
        recall = RetrievalMetrics.calculate_recall_at_k(
            retrieved_doc_ids_list, relevant_doc_ids_list, k
        )
        
        # NDCG requires relevance scores, using simplified binary version
        ndcg = RetrievalMetrics._calculate_ndcg_at_k(
            retrieved_doc_ids_list, relevant_doc_ids_list, k
        )
        
        logger.info(f"Metrics@{k}: HR={hit_rate:.3f}, MRR={mrr:.3f}, "
                   f"P={precision:.3f}, R={recall:.3f}, NDCG={ndcg:.3f}")
        
        return RetrievalMetricsResult(
            hit_rate=hit_rate,
            mrr=mrr,
            precision_at_k=precision,
            recall_at_k=recall,
            ndcg_at_k=ndcg,
        )
    
    @staticmethod
    def _calculate_ndcg_at_k(
        retrieved_doc_ids_list: List[List[str]],
        relevant_doc_ids_list: List[List[str]],
        k: int = 5,
    ) -> float:
        """
        Calculate NDCG@K (Normalized Discounted Cumulative Gain).
        
        Uses binary relevance (1 if relevant, 0 if not).
        """
        import math
        
        if not retrieved_doc_ids_list:
            return 0.0
        
        ndcgs = []
        
        for retrieved, relevant in zip(retrieved_doc_ids_list, relevant_doc_ids_list):
            relevant_set = set(relevant)
            top_k = retrieved[:k]
            
            # Calculate DCG
            dcg = 0.0
            for i, doc_id in enumerate(top_k, start=1):
                rel = 1.0 if doc_id in relevant_set else 0.0
                dcg += rel / math.log2(i + 1)
            
            # Calculate Ideal DCG (IDCG)
            # Best case: all relevant docs at top
            num_relevant = min(len(relevant_set), k)
            idcg = sum(1.0 / math.log2(i + 1) for i in range(1, num_relevant + 1))
            
            # NDCG
            ndcg = dcg / idcg if idcg > 0 else 0.0
            ndcgs.append(ndcg)
        
        avg_ndcg = sum(ndcgs) / len(ndcgs) if ndcgs else 0.0
        return avg_ndcg

