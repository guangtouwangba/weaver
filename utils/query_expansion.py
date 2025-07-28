"""
Query expansion utilities for improving search capabilities
"""
import logging
import openai
from typing import List, Dict, Set
import re

logger = logging.getLogger(__name__)

class QueryExpander:
    """AI-powered query expansion for better search results"""
    
    def __init__(self, openai_api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.model = model
        
        # Common academic term mappings
        self.term_mappings = {
            "rag": ["retrieval augmented generation", "retrieval-augmented generation", "knowledge retrieval", "vector search", "semantic search"],
            "llm": ["large language model", "language model", "transformer", "neural language model"],
            "ml": ["machine learning", "artificial intelligence", "neural network"],
            "ai": ["artificial intelligence", "machine learning", "deep learning", "neural network"],
            "cv": ["computer vision", "image processing", "visual recognition"],
            "nlp": ["natural language processing", "computational linguistics", "text processing"],
            "gpt": ["generative pre-trained transformer", "transformer", "language model"],
            "bert": ["bidirectional encoder representations from transformers", "transformer", "language model"],
            "attention": ["attention mechanism", "self-attention", "multi-head attention", "transformer attention"],
            "cnn": ["convolutional neural network", "convolution", "image classification"],
            "rnn": ["recurrent neural network", "lstm", "gru", "sequence modeling"],
            "gan": ["generative adversarial network", "adversarial training", "generative model"],
            "vae": ["variational autoencoder", "autoencoder", "generative model", "latent variable model"],
            "rl": ["reinforcement learning", "policy learning", "reward learning", "markov decision process"],
            "ssl": ["self-supervised learning", "unsupervised learning", "contrastive learning"],
            "few-shot": ["few-shot learning", "meta-learning", "transfer learning", "in-context learning"],
            "zero-shot": ["zero-shot learning", "transfer learning", "generalization"],
            "multimodal": ["multi-modal", "vision-language", "cross-modal", "multimedia"],
            "embedding": ["vector representation", "feature representation", "latent representation"],
            "fine-tuning": ["fine-tune", "transfer learning", "adaptation", "domain adaptation"],
            "prompt": ["prompting", "prompt engineering", "instruction following", "in-context learning"],
            "benchmark": ["evaluation", "dataset", "metric", "performance assessment"],
            "optimization": ["gradient descent", "training", "learning algorithm", "parameter update"],
            "regularization": ["dropout", "weight decay", "normalization", "overfitting prevention"],
            "architecture": ["model design", "network structure", "neural architecture"],
            "scaling": ["model scaling", "parameter scaling", "compute scaling", "data scaling"],
            "efficiency": ["computational efficiency", "model compression", "pruning", "quantization"],
            "interpretability": ["explainability", "model interpretation", "feature importance", "attention visualization"],
            "robustness": ["adversarial robustness", "model robustness", "generalization", "out-of-distribution"],
            "alignment": ["ai alignment", "human feedback", "preference learning", "value alignment"],
            "safety": ["ai safety", "model safety", "risk mitigation", "harmful output prevention"],
            "reasoning": ["logical reasoning", "chain-of-thought", "step-by-step reasoning", "problem solving"],
            "knowledge": ["knowledge graph", "knowledge base", "factual knowledge", "world knowledge"],
            "memory": ["external memory", "memory network", "long-term memory", "episodic memory"],
            "planning": ["task planning", "sequential decision making", "goal-oriented behavior"],
            "grounding": ["symbol grounding", "language grounding", "visual grounding", "embodied ai"],
            "causality": ["causal inference", "causal reasoning", "causal discovery", "counterfactual"],
            "bias": ["algorithmic bias", "fairness", "demographic parity", "equalized odds"],
            "privacy": ["differential privacy", "federated learning", "data privacy", "privacy-preserving"],
            "graph": ["graph neural network", "node embedding", "graph representation", "network analysis"],
            "time-series": ["temporal data", "sequence modeling", "forecasting", "time series analysis"],
            "recommendation": ["recommender system", "collaborative filtering", "content-based filtering"],
            "retrieval": ["information retrieval", "document retrieval", "passage retrieval", "semantic search"],
            "generation": ["text generation", "content generation", "creative writing", "language generation"],
            "summarization": ["text summarization", "document summarization", "abstractive summarization"],
            "translation": ["machine translation", "neural machine translation", "cross-lingual"],
            "classification": ["text classification", "document classification", "sentiment analysis"],
            "clustering": ["document clustering", "topic modeling", "unsupervised clustering"],
            "similarity": ["semantic similarity", "text similarity", "document similarity", "cosine similarity"],
            "evaluation": ["model evaluation", "performance metrics", "benchmark", "assessment"],
            "dataset": ["training data", "corpus", "benchmark dataset", "evaluation dataset"],
            "annotation": ["data annotation", "labeling", "ground truth", "human annotation"],
            "preprocessing": ["data preprocessing", "text preprocessing", "data cleaning", "tokenization"],
            "tokenization": ["subword tokenization", "byte-pair encoding", "wordpiece", "sentencepiece"],
            "vocabulary": ["vocabulary size", "out-of-vocabulary", "subword vocabulary"],
            "loss": ["loss function", "training objective", "optimization objective"],
            "gradient": ["gradient descent", "backpropagation", "gradient update", "parameter update"],
            "batch": ["batch size", "mini-batch", "batch training", "stochastic gradient descent"],
            "epoch": ["training epoch", "iteration", "training step"],
            "learning-rate": ["learning rate", "adaptive learning rate", "learning rate schedule"],
            "checkpoint": ["model checkpoint", "model saving", "training checkpoint"],
            "inference": ["model inference", "prediction", "forward pass", "deployment"],
            "latency": ["inference latency", "response time", "computational speed"],
            "throughput": ["inference throughput", "processing speed", "scalability"],
            "deployment": ["model deployment", "production deployment", "serving", "inference serving"],
            "edge": ["edge computing", "mobile deployment", "on-device inference"],
            "cloud": ["cloud computing", "distributed computing", "cluster computing"],
            "distributed": ["distributed training", "parallel training", "multi-gpu training"],
            "federated": ["federated learning", "decentralized learning", "privacy-preserving learning"],
            "continual": ["continual learning", "lifelong learning", "incremental learning", "catastrophic forgetting"],
            "meta": ["meta-learning", "learning to learn", "few-shot learning", "adaptation"],
            "transfer": ["transfer learning", "domain adaptation", "cross-domain", "knowledge transfer"],
            "distillation": ["knowledge distillation", "model compression", "teacher-student"],
            "pruning": ["network pruning", "weight pruning", "structured pruning", "model compression"],
            "quantization": ["model quantization", "weight quantization", "precision reduction"],
            "sparsity": ["sparse model", "sparse attention", "sparse connectivity"],
            "efficiency": ["parameter efficiency", "computational efficiency", "memory efficiency"]
        }
    
    def expand_query(self, query: str, max_expansions: int = 5) -> List[str]:
        """
        Expand a query using multiple strategies
        
        Args:
            query: Original search query
            max_expansions: Maximum number of expanded terms to return
            
        Returns:
            List of expanded search terms
        """
        try:
            expanded_terms = set([query.lower().strip()])
            
            # Strategy 1: Rule-based expansion using term mappings
            rule_based_terms = self._rule_based_expansion(query)
            expanded_terms.update(rule_based_terms)
            
            # Strategy 2: AI-powered expansion
            try:
                ai_terms = self._ai_powered_expansion(query)
                expanded_terms.update(ai_terms)
            except Exception as e:
                logger.warning(f"AI expansion failed, using rule-based only: {e}")
            
            # Strategy 3: Academic synonym expansion
            academic_terms = self._academic_synonym_expansion(query)
            expanded_terms.update(academic_terms)
            
            # Convert to list and limit results
            result = list(expanded_terms)[:max_expansions]
            logger.info(f"Expanded query '{query}' to {len(result)} terms: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Query expansion failed: {e}")
            return [query]  # Fallback to original query
    
    def _rule_based_expansion(self, query: str) -> Set[str]:
        """Expand query using predefined term mappings"""
        expanded = set()
        query_lower = query.lower()
        
        # Direct mapping lookup
        for term, expansions in self.term_mappings.items():
            if term in query_lower:
                expanded.update(expansions)
                # Also add variations with the original context
                for expansion in expansions[:3]:  # Limit to top 3
                    expanded.add(query_lower.replace(term, expansion))
        
        # Handle common abbreviations and variations
        if re.search(r'\brag\b', query_lower, re.IGNORECASE):
            expanded.update([
                "retrieval augmented generation",
                "vector database search",
                "semantic retrieval",
                "knowledge retrieval system",
                "document retrieval"
            ])
        
        if re.search(r'\btransformer', query_lower, re.IGNORECASE):
            expanded.update([
                "attention mechanism",
                "self-attention",
                "multi-head attention",
                "encoder-decoder architecture"
            ])
        
        return expanded
    
    def _ai_powered_expansion(self, query: str) -> Set[str]:
        """Use OpenAI to generate expanded search terms"""
        try:
            prompt = f"""
Given the search query: "{query}"

Generate 5 alternative academic search terms that would find relevant research papers on the same topic. Focus on:
1. Academic synonyms and technical terms
2. Related concepts and methodologies  
3. Broader and narrower terms
4. Common variations used in research papers

Return only the search terms, one per line, without numbering or explanation.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            terms = [term.strip() for term in content.split('\n') if term.strip()]
            
            # Clean and validate terms
            cleaned_terms = set()
            for term in terms:
                # Remove numbering, bullets, etc.
                clean_term = re.sub(r'^\d+\.?\s*', '', term)
                clean_term = re.sub(r'^[-*•]\s*', '', clean_term)
                clean_term = clean_term.strip('"\'')
                
                if clean_term and len(clean_term) > 2:
                    cleaned_terms.add(clean_term.lower())
            
            logger.debug(f"AI expansion generated: {cleaned_terms}")
            return cleaned_terms
            
        except Exception as e:
            logger.error(f"AI-powered expansion failed: {e}")
            return set()
    
    def _academic_synonym_expansion(self, query: str) -> Set[str]:
        """Generate academic variations of the query"""
        expanded = set()
        query_lower = query.lower()
        
        # Common academic variations
        academic_patterns = [
            (r'\bdeep learning\b', ['neural networks', 'artificial neural networks', 'deep neural networks']),
            (r'\bmachine learning\b', ['statistical learning', 'computational learning', 'automated learning']),
            (r'\bneural network\b', ['artificial neural network', 'connectionist model', 'parallel distributed processing']),
            (r'\boptimization\b', ['mathematical optimization', 'parameter optimization', 'objective optimization']),
            (r'\bclassification\b', ['categorization', 'pattern recognition', 'supervised learning']),
            (r'\bclustering\b', ['unsupervised clustering', 'data clustering', 'cluster analysis']),
            (r'\bregression\b', ['predictive modeling', 'function approximation', 'supervised regression']),
            (r'\bfeature\b', ['attribute', 'variable', 'predictor', 'input dimension']),
            (r'\bmodel\b', ['algorithm', 'method', 'approach', 'framework', 'system']),
            (r'\btraining\b', ['learning', 'optimization', 'parameter estimation', 'model fitting']),
            (r'\bprediction\b', ['inference', 'forecasting', 'estimation', 'classification']),
            (r'\bperformance\b', ['accuracy', 'effectiveness', 'efficiency', 'quality metrics']),
            (r'\bevaluation\b', ['assessment', 'validation', 'testing', 'benchmarking']),
            (r'\barchitecture\b', ['topology', 'structure', 'design', 'configuration']),
            (r'\balgorithm\b', ['method', 'technique', 'procedure', 'approach']),
        ]
        
        for pattern, synonyms in academic_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                for synonym in synonyms:
                    # Replace the matched term with synonym
                    expanded_query = re.sub(pattern, synonym, query_lower, flags=re.IGNORECASE)
                    expanded.add(expanded_query)
        
        return expanded
    
    def generate_arxiv_search_queries(self, original_query: str) -> List[str]:
        """
        Generate specific search queries optimized for arXiv search
        
        Args:
            original_query: Original user query
            
        Returns:
            List of arXiv-optimized search queries
        """
        try:
            expanded_terms = self.expand_query(original_query, max_expansions=3)
            
            # Create arXiv-specific queries
            arxiv_queries = []
            
            # Add the original query
            arxiv_queries.append(original_query)
            
            # Add expanded terms
            for term in expanded_terms[:2]:  # Limit to top 2 expansions
                arxiv_queries.append(term)
            
            # Create combined queries for better results
            if len(expanded_terms) >= 2:
                combined_query = f"{expanded_terms[0]} OR {expanded_terms[1]}"
                arxiv_queries.append(combined_query)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_queries = []
            for query in arxiv_queries:
                if query.lower() not in seen:
                    seen.add(query.lower())
                    unique_queries.append(query)
            
            logger.info(f"Generated {len(unique_queries)} arXiv queries for '{original_query}'")
            return unique_queries[:4]  # Limit to 4 queries
            
        except Exception as e:
            logger.error(f"ArXiv query generation failed: {e}")
            return [original_query]