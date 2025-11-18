#!/usr/bin/env python3
"""
实际评估 RAG 系统的完整示例脚本

使用步骤:
1. 准备测试问题列表
2. 运行 RAG 系统获取答案
3. 收集评估数据
4. 使用 RAGAS 评估
5. 分析和优化

Usage:
    python examples/evaluate_rag_system.py
"""

# Fix OpenMP conflict on macOS
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import asyncio
import sys
from pathlib import Path
from typing import List, Dict
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag_core.evaluation import RAGASEvaluator, EvaluationDataset, EvaluationMetrics
from rag_core.retrievers import HybridRetriever, VectorRetriever, RetrieverFactory
from rag_core.chains.llm import build_llm
from rag_core.chains.embeddings import build_embedding_function
from rag_core.chains.vectorstore import load_vector_store
from shared_config.settings import AppSettings


# ========================================
# 步骤 1: 准备测试问题
# ========================================

def load_test_questions() -> List[Dict[str, str]]:
    """
    加载测试问题列表。
    
    在实际使用中，你可以从文件加载或直接定义。
    """
    test_questions = [
        {
            "question": "What is machine learning?",
            "ground_truth": "Machine learning is a method of data analysis that automates analytical model building.",
            "topic": "ml_basics"
        },
        {
            "question": "How do neural networks learn?",
            "ground_truth": "Neural networks learn through backpropagation and gradient descent.",
            "topic": "neural_networks"
        },
        {
            "question": "What is the difference between supervised and unsupervised learning?",
            "ground_truth": "Supervised learning uses labeled data, while unsupervised learning finds patterns in unlabeled data.",
            "topic": "ml_types"
        },
        # 添加更多问题...
    ]
    
    return test_questions


# ========================================
# 步骤 2: 运行 RAG 系统收集数据
# ========================================

async def collect_rag_responses(
    test_questions: List[Dict],
    retriever,
    llm,
    settings: AppSettings
) -> EvaluationDataset:
    """
    运行 RAG 系统，收集评估数据。
    
    Args:
        test_questions: 测试问题列表
        retriever: 检索器实例
        llm: LLM 实例
        settings: 应用配置
    
    Returns:
        包含 RAG 响应的评估数据集
    """
    print(f"📊 开始收集 RAG 系统响应...")
    print(f"   问题数量: {len(test_questions)}")
    print()
    
    dataset = EvaluationDataset(
        name="rag_system_evaluation",
        description=f"RAG system evaluation with {len(test_questions)} questions"
    )
    
    for i, item in enumerate(test_questions, 1):
        question = item["question"]
        ground_truth = item.get("ground_truth")
        
        print(f"   [{i}/{len(test_questions)}] 处理: {question[:50]}...")
        
        try:
            # 1. 检索相关文档
            retrieved_docs = await retriever.retrieve(question, top_k=5)
            
            # 2. 准备上下文
            contexts = [doc.page_content for doc in retrieved_docs]
            
            # 3. 生成答案（简化版，实际应该使用完整的 QA chain）
            if contexts:
                context_text = "\n\n".join(contexts)
                prompt = f"""Based on the following context, answer the question.

Context:
{context_text}

Question: {question}

Answer:"""
                
                answer = await llm.ainvoke(prompt)
                if hasattr(answer, 'content'):
                    answer_text = answer.content
                else:
                    answer_text = str(answer)
            else:
                answer_text = "I don't have enough information to answer this question."
            
            # 4. 添加到评估数据集
            dataset.add_sample(
                question=question,
                answer=answer_text,
                contexts=contexts,
                ground_truth=ground_truth,
                metadata={
                    "topic": item.get("topic", "unknown"),
                    "num_contexts": len(contexts)
                }
            )
            
            print(f"      ✓ 检索到 {len(contexts)} 个文档")
            
        except Exception as e:
            print(f"      ✗ 错误: {e}")
            continue
    
    print(f"\n✅ 收集完成! 成功处理 {len(dataset)} 个问题\n")
    return dataset


# ========================================
# 步骤 3: 运行 RAGAS 评估
# ========================================

async def evaluate_with_ragas(
    dataset: EvaluationDataset,
    llm,
    embeddings
) -> Dict:
    """
    使用 RAGAS 评估数据集。
    
    Args:
        dataset: 评估数据集
        llm: LLM 用于评估
        embeddings: Embeddings 用于相似度计算
    
    Returns:
        评估结果字典
    """
    print("🎯 开始 RAGAS 评估...")
    print(f"   数据集: {dataset.name}")
    print(f"   样本数: {len(dataset)}")
    print()
    
    # 创建评估器
    evaluator = RAGASEvaluator(
        llm=llm,
        embeddings=embeddings
    )
    
    # 选择评估指标
    metrics = [
        EvaluationMetrics.FAITHFULNESS,        # 检测幻觉
        EvaluationMetrics.ANSWER_RELEVANCY,    # 答案相关性
        EvaluationMetrics.CONTEXT_PRECISION,   # 检索精确度
    ]
    
    # 如果有 ground truth，添加更多指标
    has_ground_truth = any(s.ground_truth for s in dataset.samples)
    if has_ground_truth:
        metrics.append(EvaluationMetrics.ANSWER_SIMILARITY)
        print("   ℹ️  检测到 ground truth，将评估答案相似度")
    
    print(f"   评估指标: {[m.value for m in metrics]}")
    print()
    
    try:
        # 运行评估
        results = await evaluator.evaluate(
            dataset,
            metrics=metrics
        )
        
        print("✅ 评估完成!\n")
        print(results.summary())
        print()
        
        return {
            "scores": results.scores,
            "metadata": results.metadata
        }
        
    except Exception as e:
        print(f"❌ 评估失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# ========================================
# 步骤 4: 分析结果
# ========================================

def analyze_results(results: Dict, dataset: EvaluationDataset):
    """分析评估结果，提供优化建议。"""
    print("=" * 80)
    print("📈 结果分析和优化建议")
    print("=" * 80)
    print()
    
    if not results or "scores" not in results:
        print("❌ 没有可用的评估结果")
        return
    
    scores = results["scores"]
    
    # 分析各项指标
    print("1️⃣  指标分析:")
    print()
    
    # Faithfulness
    if "faithfulness" in scores:
        faith_score = scores["faithfulness"]
        print(f"   📌 Faithfulness (忠实度): {faith_score:.3f}")
        if faith_score < 0.7:
            print("      ⚠️  分数偏低! 可能存在幻觉问题")
            print("      💡 建议:")
            print("         - 改进 prompt，强调'仅基于上下文回答'")
            print("         - 提升检索质量，确保相关上下文")
            print("         - 考虑使用更可控的 LLM")
        elif faith_score < 0.85:
            print("      ℹ️  分数中等，有改进空间")
            print("      💡 建议: 检查低分样本，针对性优化")
        else:
            print("      ✅ 分数良好! 幻觉问题较少")
        print()
    
    # Answer Relevancy
    if "answer_relevancy" in scores:
        rel_score = scores["answer_relevancy"]
        print(f"   📌 Answer Relevancy (答案相关性): {rel_score:.3f}")
        if rel_score < 0.7:
            print("      ⚠️  答案经常跑题或过于通用")
            print("      💡 建议:")
            print("         - 优化 prompt，使答案更聚焦")
            print("         - 调整生成参数 (temperature, max_tokens)")
            print("         - 改进问题理解和上下文选择")
        elif rel_score < 0.85:
            print("      ℹ️  相关性尚可，可以继续优化")
        else:
            print("      ✅ 答案相关性很好!")
        print()
    
    # Context Precision
    if "context_precision" in scores:
        prec_score = scores["context_precision"]
        print(f"   📌 Context Precision (检索精确度): {prec_score:.3f}")
        if prec_score < 0.7:
            print("      ⚠️  检索到的文档相关性不足")
            print("      💡 建议:")
            print("         - 使用 HybridRetriever (BM25 + Vector)")
            print("         - 添加 Reranker 精排")
            print("         - 调整相似度阈值")
            print("         - 增加 top_k 再用 reranker 筛选")
        elif prec_score < 0.85:
            print("      ℹ️  检索质量中等")
            print("      💡 建议: 考虑添加 reranker 提升精度")
        else:
            print("      ✅ 检索质量很好!")
        print()
    
    # 总体建议
    print("2️⃣  总体建议:")
    print()
    
    avg_score = sum(scores.values()) / len(scores)
    print(f"   平均分数: {avg_score:.3f}")
    
    if avg_score < 0.7:
        print("   🔴 系统质量需要显著改进")
        print("   优先级:")
        print("      1. 检查数据质量（向量库是否有相关文档）")
        print("      2. 优化检索策略（hybrid + reranker）")
        print("      3. 改进 prompt engineering")
    elif avg_score < 0.85:
        print("   🟡 系统质量中等，有优化空间")
        print("   建议:")
        print("      1. 找出低分样本，分析原因")
        print("      2. 针对性优化薄弱环节")
        print("      3. A/B 测试不同配置")
    else:
        print("   🟢 系统质量良好!")
        print("   继续:")
        print("      1. 在更多样本上测试")
        print("      2. 监控生产环境表现")
        print("      3. 持续收集用户反馈")
    
    print()


# ========================================
# 步骤 5: 保存结果
# ========================================

def save_evaluation_results(
    dataset: EvaluationDataset,
    results: Dict,
    output_dir: Path
):
    """保存评估数据和结果。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存数据集
    dataset_path = output_dir / f"{dataset.name}.json"
    dataset.save(dataset_path)
    print(f"💾 数据集已保存: {dataset_path}")
    
    # 保存评估结果
    if results:
        results_path = output_dir / f"{dataset.name}_results.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 结果已保存: {results_path}")
    
    print()


# ========================================
# 主函数
# ========================================

async def main():
    """主函数：完整的 RAG 评估流程。"""
    print("\n" + "=" * 80)
    print("🎯 RAG 系统评估 - 完整流程")
    print("=" * 80)
    print()
    
    # 初始化
    print("🔧 初始化系统...")
    try:
        settings = AppSettings()
        print(f"   LLM Provider: {settings.llm.provider}")
        print(f"   LLM Model: {settings.llm.model}")
        print(f"   Embedding Provider: {settings.embedding.provider}")
        print()
        
        # 初始化组件
        llm = build_llm(settings)
        embeddings = build_embedding_function(settings)
        vector_store = load_vector_store()
        
        if not vector_store:
            print("❌ 向量库为空! 请先导入文档:")
            print("   python examples/ingest_documents.py")
            return
        
        # 创建检索器（使用配置中的设置）
        retriever = RetrieverFactory.create_from_settings(
            settings=settings,
            vector_store=vector_store
        )
        
        print(f"✅ 系统初始化完成")
        print(f"   检索器: {retriever.__class__.__name__}")
        print()
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 步骤 1: 加载测试问题
    print("=" * 80)
    print("步骤 1: 加载测试问题")
    print("=" * 80)
    print()
    
    test_questions = load_test_questions()
    print(f"✅ 加载了 {len(test_questions)} 个测试问题")
    print()
    
    # 步骤 2: 收集 RAG 响应
    print("=" * 80)
    print("步骤 2: 运行 RAG 系统收集数据")
    print("=" * 80)
    print()
    
    dataset = await collect_rag_responses(
        test_questions,
        retriever,
        llm,
        settings
    )
    
    if len(dataset) == 0:
        print("❌ 没有收集到任何数据")
        return
    
    # 步骤 3: RAGAS 评估
    print("=" * 80)
    print("步骤 3: RAGAS 评估")
    print("=" * 80)
    print()
    
    results = await evaluate_with_ragas(dataset, llm, embeddings)
    
    # 步骤 4: 分析结果
    if results:
        analyze_results(results, dataset)
    
    # 步骤 5: 保存结果
    print("=" * 80)
    print("步骤 5: 保存结果")
    print("=" * 80)
    print()
    
    output_dir = project_root / "data" / "evaluation"
    save_evaluation_results(dataset, results, output_dir)
    
    # 完成
    print("=" * 80)
    print("✅ 评估流程完成!")
    print("=" * 80)
    print()
    print("📊 下一步:")
    print("   1. 查看保存的评估结果")
    print("   2. 根据建议优化系统")
    print("   3. 重新评估验证改进")
    print("   4. 建立持续评估流程")
    print()


if __name__ == "__main__":
    asyncio.run(main())

