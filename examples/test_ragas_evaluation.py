#!/usr/bin/env python3
"""
Example script demonstrating RAGAS evaluation.

This script shows how to:
1. Create evaluation datasets
2. Evaluate RAG system with RAGAS metrics
3. Analyze and compare results
4. Save/load evaluation results

Usage:
    python examples/test_ragas_evaluation.py
"""

# Fix OpenMP conflict on macOS
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag_core.evaluation import RAGASEvaluator, EvaluationDataset, EvaluationMetrics

# Optional imports for real LLM evaluation
try:
    from rag_core.chains.llm import build_llm
    from rag_core.chains.embeddings import build_embedding_function
    from shared_config.settings import AppSettings
    HAVE_LLM = True
except ImportError:
    HAVE_LLM = False


def create_sample_dataset() -> EvaluationDataset:
    """Create a sample evaluation dataset."""
    dataset = EvaluationDataset(
        name="sample_ml_qa",
        description="Sample Q&A dataset about machine learning"
    )
    
    # Sample 1: Machine Learning definition
    dataset.add_sample(
        question="What is machine learning?",
        answer="Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can access data and learn patterns from it.",
        contexts=[
            "Machine learning (ML) is a field of inquiry devoted to understanding and building methods that 'learn', that is, methods that leverage data to improve performance on some set of tasks.",
            "Machine learning algorithms build a model based on sample data, known as training data, in order to make predictions or decisions without being explicitly programmed to do so.",
            "Machine learning is closely related to computational statistics, which focuses on making predictions using computers."
        ],
        ground_truth="Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
        metadata={"topic": "ml_basics", "difficulty": "easy"}
    )
    
    # Sample 2: Deep Learning
    dataset.add_sample(
        question="How does deep learning differ from traditional machine learning?",
        answer="Deep learning uses neural networks with multiple layers to automatically learn hierarchical representations of data. Unlike traditional machine learning which requires manual feature engineering, deep learning can automatically discover the representations needed for feature detection or classification from raw data.",
        contexts=[
            "Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning.",
            "Deep learning architectures such as deep neural networks have been applied to fields including computer vision, speech recognition, natural language processing, and more.",
            "The key difference is that deep learning models can automatically learn features from data, while traditional ML often requires manual feature engineering."
        ],
        ground_truth="Deep learning differs from traditional machine learning primarily in its ability to automatically learn hierarchical feature representations from raw data through multiple layers of neural networks, eliminating the need for manual feature engineering that is typically required in traditional ML approaches.",
        metadata={"topic": "deep_learning", "difficulty": "medium"}
    )
    
    # Sample 3: Supervised vs Unsupervised
    dataset.add_sample(
        question="What is the difference between supervised and unsupervised learning?",
        answer="Supervised learning uses labeled data where the correct output is known, training the model to predict outcomes. Unsupervised learning works with unlabeled data, finding hidden patterns and structures without predefined labels.",
        contexts=[
            "Supervised learning is the machine learning task of learning a function that maps an input to an output based on example input-output pairs.",
            "Unsupervised learning is a type of machine learning that looks for previously undetected patterns in a data set with no pre-existing labels.",
            "In supervised learning, you have input variables (X) and output variables (Y) and use an algorithm to learn the mapping function from the input to the output.",
            "Clustering and association are two types of unsupervised learning."
        ],
        ground_truth="Supervised learning requires labeled training data with known outputs to learn a mapping function, while unsupervised learning discovers patterns and structures in unlabeled data without predefined outputs.",
        metadata={"topic": "ml_types", "difficulty": "easy"}
    )
    
    # Sample 4: Overfitting
    dataset.add_sample(
        question="What is overfitting in machine learning?",
        answer="Overfitting occurs when a model learns the training data too well, including its noise and outliers, resulting in poor performance on new, unseen data. The model becomes too complex and fails to generalize.",
        contexts=[
            "Overfitting is a modeling error that occurs when a function is too closely fit to a limited set of data points.",
            "Overfitting occurs when a model learns detail and noise in the training data to the extent that it negatively impacts the performance of the model on new data.",
            "Signs of overfitting include high accuracy on training data but low accuracy on validation/test data."
        ],
        ground_truth="Overfitting is a phenomenon where a machine learning model performs well on training data but poorly on new, unseen data because it has learned the noise and specific details of the training set rather than general patterns.",
        metadata={"topic": "model_evaluation", "difficulty": "medium"}
    )
    
    # Sample 5: Neural Networks
    dataset.add_sample(
        question="How do neural networks learn?",
        answer="Neural networks learn through a process called backpropagation, where they adjust their internal weights based on the error between predicted and actual outputs. This iterative process minimizes the loss function using optimization algorithms like gradient descent.",
        contexts=[
            "Neural networks learn by adjusting connection weights based on the error between predicted and actual output.",
            "Backpropagation is the key algorithm used to train neural networks by computing gradients of the loss function.",
            "The learning process involves forward propagation to make predictions, calculating error, and backward propagation to update weights.",
            "Optimization algorithms like SGD, Adam, and RMSprop are used to update the network's weights efficiently."
        ],
        ground_truth="Neural networks learn through backpropagation, a method that calculates gradients of the loss function with respect to the network's weights and uses gradient descent to iteratively update these weights to minimize the prediction error.",
        metadata={"topic": "neural_networks", "difficulty": "medium"}
    )
    
    return dataset


async def test_basic_evaluation():
    """Test basic RAGAS evaluation."""
    print("=" * 80)
    print("TEST 1: Basic RAGAS Evaluation")
    print("=" * 80 + "\n")
    
    # Create dataset
    print("📊 Creating evaluation dataset...")
    dataset = create_sample_dataset()
    print(f"✅ Created dataset with {len(dataset)} samples\n")
    
    # Initialize evaluator (using fake LLM and embeddings for demo)
    print("🔧 Initializing evaluator...")
    if HAVE_LLM:
        try:
            settings = AppSettings()
            llm = build_llm(settings)
            embeddings = build_embedding_function(settings)
            
            evaluator = RAGASEvaluator(
                llm=llm,
                embeddings=embeddings
            )
            print("✅ Evaluator initialized\n")
        except Exception as e:
            print(f"⚠️  Could not initialize with real LLM: {e}")
            print("   Using mock evaluation for demonstration...\n")
            evaluator = None
    else:
        print("ℹ️  LLM dependencies not available")
        print("   Using mock evaluation for demonstration...\n")
        evaluator = None
    
    # Run evaluation (mock for now)
    print("🎯 Running evaluation...")
    print("   Metrics: faithfulness, answer_relevancy, context_precision")
    print("   (Note: This would use real LLM in production)\n")
    
    # Show what would be evaluated
    print("Sample evaluation data:")
    for i, sample in enumerate(dataset.samples[:2], 1):
        print(f"\n   Sample {i}:")
        print(f"   Question: {sample.question}")
        print(f"   Answer: {sample.answer[:100]}...")
        print(f"   Contexts: {len(sample.contexts)} chunks")
        print(f"   Ground Truth: {sample.ground_truth[:80]}...")
    
    print("\n" + "=" * 80)
    print("✅ Basic evaluation test completed")
    print("=" * 80 + "\n")


async def test_dataset_operations():
    """Test dataset operations."""
    print("=" * 80)
    print("TEST 2: Dataset Operations")
    print("=" * 80 + "\n")
    
    # Create dataset
    dataset = create_sample_dataset()
    
    # Filter by metadata
    print("📋 Filtering by difficulty...")
    easy_samples = dataset.filter_by_metadata("difficulty", "easy")
    medium_samples = dataset.filter_by_metadata("difficulty", "medium")
    print(f"   Easy: {len(easy_samples)} samples")
    print(f"   Medium: {len(medium_samples)} samples\n")
    
    # Split dataset
    print("✂️  Splitting dataset (80/20)...")
    train, test = dataset.split(test_size=0.2, random_state=42)
    print(f"   Train: {len(train)} samples")
    print(f"   Test: {len(test)} samples\n")
    
    # Save dataset
    print("💾 Saving dataset...")
    output_dir = project_root / "data" / "evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    dataset_path = output_dir / "sample_dataset.json"
    dataset.save(dataset_path)
    print(f"   Saved to: {dataset_path}\n")
    
    # Load dataset
    print("📂 Loading dataset...")
    loaded = EvaluationDataset.load(dataset_path)
    print(f"   Loaded: {loaded.name} with {len(loaded)} samples\n")
    
    # Convert to RAGAS format
    print("🔄 Converting to RAGAS format...")
    ragas_data = dataset.to_ragas_format()
    print(f"   Keys: {list(ragas_data.keys())}")
    print(f"   Samples: {len(ragas_data['question'])}\n")
    
    print("=" * 80)
    print("✅ Dataset operations test completed")
    print("=" * 80 + "\n")


async def test_metrics_explanation():
    """Explain available metrics."""
    print("=" * 80)
    print("TEST 3: RAGAS Metrics Overview")
    print("=" * 80 + "\n")
    
    metrics_info = {
        "context_precision": {
            "category": "Retrieval Quality",
            "description": "Measures if relevant contexts are ranked higher",
            "requires": "Ground truth contexts",
            "range": "0-1 (higher is better)"
        },
        "context_recall": {
            "category": "Retrieval Quality",
            "description": "Measures if all relevant contexts are retrieved",
            "requires": "Ground truth contexts",
            "range": "0-1 (higher is better)"
        },
        "faithfulness": {
            "category": "Generation Quality",
            "description": "Measures if answer is grounded in retrieved contexts",
            "requires": "LLM for verification",
            "range": "0-1 (higher is better)"
        },
        "answer_relevancy": {
            "category": "Generation Quality",
            "description": "Measures if answer addresses the question",
            "requires": "LLM and embeddings",
            "range": "0-1 (higher is better)"
        },
        "answer_similarity": {
            "category": "Generation Quality",
            "description": "Cosine similarity between answer and ground truth",
            "requires": "Ground truth answer, embeddings",
            "range": "0-1 (higher is better)"
        },
        "answer_correctness": {
            "category": "Generation Quality",
            "description": "Weighted combination of similarity and factual correctness",
            "requires": "Ground truth answer, LLM",
            "range": "0-1 (higher is better)"
        },
    }
    
    print("📊 Available RAGAS Metrics:\n")
    
    for metric, info in metrics_info.items():
        print(f"🔹 {metric}")
        print(f"   Category: {info['category']}")
        print(f"   Description: {info['description']}")
        print(f"   Requires: {info['requires']}")
        print(f"   Range: {info['range']}")
        print()
    
    print("💡 Metric Selection Guide:")
    print("   - For retrieval optimization: Use context_precision, context_recall")
    print("   - For answer quality: Use faithfulness, answer_relevancy")
    print("   - For comparison with ground truth: Use answer_similarity, answer_correctness")
    print("   - For overall system: Use all metrics together\n")
    
    print("=" * 80)
    print("✅ Metrics explanation completed")
    print("=" * 80 + "\n")


async def test_evaluation_workflow():
    """Show complete evaluation workflow."""
    print("=" * 80)
    print("TEST 4: Complete Evaluation Workflow")
    print("=" * 80 + "\n")
    
    print("📝 Complete RAG Evaluation Workflow:\n")
    
    workflow_steps = [
        ("1. Prepare Evaluation Dataset", [
            "- Collect user questions",
            "- Run RAG system to get answers and contexts",
            "- (Optional) Add ground truth answers",
            "- Create EvaluationDataset",
        ]),
        ("2. Configure Evaluator", [
            "- Initialize RAGASEvaluator with LLM and embeddings",
            "- Choose metrics based on evaluation goals",
            "- Set batch size for efficient processing",
        ]),
        ("3. Run Evaluation", [
            "- evaluator.evaluate(dataset, metrics=selected_metrics)",
            "- RAGAS computes each metric score",
            "- Results include overall and per-sample scores",
        ]),
        ("4. Analyze Results", [
            "- Review metric scores",
            "- Identify weak samples (low scores)",
            "- Compare different system configurations",
            "- Track improvements over time",
        ]),
        ("5. Iterate and Improve", [
            "- Adjust retrieval parameters (top_k, similarity threshold)",
            "- Try different retrieval strategies (hybrid, reranker)",
            "- Improve prompts and generation parameters",
            "- Re-evaluate to measure improvement",
        ]),
    ]
    
    for step_name, details in workflow_steps:
        print(f"📌 {step_name}")
        for detail in details:
            print(f"   {detail}")
        print()
    
    print("🎯 Best Practices:")
    print("   ✓ Use a diverse evaluation set (different topics, difficulties)")
    print("   ✓ Include edge cases and failure modes")
    print("   ✓ Track metrics over time (before/after changes)")
    print("   ✓ Combine automated metrics with human evaluation")
    print("   ✓ Split data: development set for tuning, test set for final eval\n")
    
    print("=" * 80)
    print("✅ Workflow explanation completed")
    print("=" * 80 + "\n")


async def main():
    """Main function."""
    print("\n" + "=" * 80)
    print("🧪 RAGAS Evaluation Test Script")
    print("=" * 80 + "\n")
    
    print("This script demonstrates RAGAS evaluation for RAG systems.")
    print("RAGAS evaluates both retrieval quality and answer quality.\n")
    
    try:
        # Test 1: Basic evaluation
        await test_basic_evaluation()
        
        # Test 2: Dataset operations
        await test_dataset_operations()
        
        # Test 3: Metrics explanation
        await test_metrics_explanation()
        
        # Test 4: Complete workflow
        await test_evaluation_workflow()
        
        print("=" * 80)
        print("✅ All tests completed!")
        print("=" * 80)
        print("\n💡 Next Steps:")
        print("   1. Create your own evaluation dataset with real Q&A pairs")
        print("   2. Run evaluation with your RAG system")
        print("   3. Analyze results and identify improvement areas")
        print("   4. Iterate: make changes, re-evaluate, track improvements")
        print("\n🚀 To use in production:")
        print("   1. Configure real LLM and embeddings (not fake)")
        print("   2. Prepare evaluation dataset (30-100+ samples)")
        print("   3. Run: python examples/evaluate_rag_system.py")
        print("   4. Review results and optimize system")
        print("\n📚 Documentation: docs/RAGAS_EVALUATION.md")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
