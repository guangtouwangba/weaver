#!/usr/bin/env python3
"""
使用已生成的测试数据集评估 RAG 系统

这个脚本会：
1. 加载已有的测试数据集（只有 question 和 ground_truth）
2. 运行 RAG 系统获取答案和上下文
3. 使用 RAGAS 评估
4. 分析结果并保存

Usage:
    # 评估指定数据集
    python examples/evaluate_with_dataset.py data/evaluation/generated_test_set.json
    
    # 评估并保存详细结果
    python examples/evaluate_with_dataset.py data/evaluation/generated_test_set.json --save-details
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
import asyncio
import json
from pathlib import Path
from typing import List, Dict
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag_core.evaluation import RAGASEvaluator, EvaluationDataset, EvaluationMetrics
from rag_core.retrievers import RetrieverFactory
from rag_core.rerankers import RerankerFactory
from rag_core.chains.llm import build_llm
from rag_core.chains.embeddings import build_embedding_function
from rag_core.chains.vectorstore import load_vector_store
from shared_config.settings import AppSettings


async def fill_rag_responses(
    dataset: EvaluationDataset,
    retriever,
    reranker,
    llm,
    settings: AppSettings,
    show_progress: bool = True
) -> EvaluationDataset:
    """
    为数据集中的每个问题运行 RAG 系统，填充答案和上下文。
    
    Args:
        dataset: 输入数据集（只有 question 和 ground_truth）
        retriever: 检索器
        reranker: 重排器（可选）
        llm: LLM
        settings: 配置
        show_progress: 是否显示进度
    
    Returns:
        填充了答案和上下文的数据集
    """
    print(f"🔄 运行 RAG 系统填充答案和上下文...")
    print(f"   问题数量: {len(dataset)}")
    print(f"   检索器: {retriever.__class__.__name__}")
    if reranker:
        print(f"   重排器: {reranker.__class__.__name__}")
    print()
    
    # 创建新数据集
    filled_dataset = EvaluationDataset(
        name=f"{dataset.name}_filled",
        description=f"RAG responses for {dataset.name}"
    )
    
    success_count = 0
    
    for i, sample in enumerate(dataset.samples, 1):
        question = sample.question
        
        if show_progress:
            print(f"   [{i}/{len(dataset)}] {question[:60]}...")
        
        try:
            # 1. 检索相关文档
            if hasattr(settings.retriever, 'top_k'):
                top_k = settings.retriever.top_k
            else:
                top_k = 5
            
            retrieved_docs = await retriever.retrieve(question, top_k=top_k * 2)  # 多取一些
            
            # 2. 可选：重排序
            if reranker and len(retrieved_docs) > 0:
                retrieved_docs = await reranker.rerank(
                    query=question,
                    documents=retrieved_docs,
                    top_n=top_k
                )
            else:
                retrieved_docs = retrieved_docs[:top_k]
            
            # 3. 准备上下文
            contexts = [doc.page_content for doc in retrieved_docs]
            
            # 4. 生成答案
            if contexts:
                context_text = "\n\n".join(contexts)
                prompt = f"""Based on the following context, answer the question.

Context:
{context_text}

Question: {question}

Answer:"""
                
                response = await llm.ainvoke(prompt)
                answer = response.content if hasattr(response, 'content') else str(response)
            else:
                answer = "I don't have enough information to answer this question."
            
            # 5. 添加到新数据集
            filled_dataset.add_sample(
                question=question,
                answer=answer,
                contexts=contexts,
                ground_truth=sample.ground_truth,
                metadata=sample.metadata
            )
            
            if show_progress:
                print(f"      ✓ 检索: {len(contexts)} 个文档, 答案: {len(answer)} 字符")
            
            success_count += 1
            
        except Exception as e:
            print(f"      ✗ 错误: {e}")
            # 添加空响应
            filled_dataset.add_sample(
                question=question,
                answer="Error: Failed to generate response",
                contexts=[],
                ground_truth=sample.ground_truth,
                metadata=sample.metadata
            )
            continue
    
    print(f"\n✅ 完成! 成功处理 {success_count}/{len(dataset)} 个问题\n")
    return filled_dataset


async def evaluate_dataset(
    dataset: EvaluationDataset,
    llm,
    embeddings,
    metrics: List[EvaluationMetrics]
) -> Dict:
    """
    使用 RAGAS 评估数据集。
    
    Args:
        dataset: 评估数据集
        llm: LLM 用于评估
        embeddings: Embeddings 用于相似度计算
        metrics: 评估指标列表
    
    Returns:
        评估结果
    """
    print("🎯 开始 RAGAS 评估...")
    print(f"   数据集: {dataset.name}")
    print(f"   样本数: {len(dataset)}")
    print(f"   指标: {[m.value for m in metrics]}")
    print()
    
    evaluator = RAGASEvaluator(llm=llm, embeddings=embeddings)
    
    try:
        results = await evaluator.evaluate(dataset, metrics=metrics)
        
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
    
    for metric, score in scores.items():
        print(f"   📌 {metric}: {score:.3f}")
        
        if score < 0.7:
            print(f"      ⚠️  分数偏低!")
        elif score < 0.85:
            print(f"      ℹ️  分数中等，有改进空间")
        else:
            print(f"      ✅ 分数良好!")
        print()
    
    # 总体建议
    print("2️⃣  总体评分:")
    print()
    
    avg_score = sum(scores.values()) / len(scores)
    print(f"   平均分数: {avg_score:.3f}")
    
    if avg_score >= 0.85:
        grade = "A (优秀)"
        emoji = "🟢"
    elif avg_score >= 0.75:
        grade = "B (良好)"
        emoji = "🟡"
    elif avg_score >= 0.65:
        grade = "C (中等)"
        emoji = "🟠"
    else:
        grade = "D (需改进)"
        emoji = "🔴"
    
    print(f"   {emoji} 评级: {grade}")
    print()


def save_results(
    original_dataset: EvaluationDataset,
    filled_dataset: EvaluationDataset,
    results: Dict,
    output_dir: Path,
    save_details: bool = False
):
    """保存评估结果。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存填充后的数据集
    filled_path = output_dir / f"{filled_dataset.name}.json"
    filled_dataset.save(filled_path)
    print(f"💾 完整数据集已保存: {filled_path}")
    
    # 保存评估结果
    if results:
        results_path = output_dir / f"{original_dataset.name}_results.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 评估结果已保存: {results_path}")
    
    # 可选：保存详细报告
    if save_details and results:
        report_path = output_dir / f"{original_dataset.name}_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# 评估报告: {original_dataset.name}\n\n")
            f.write(f"## 概览\n\n")
            f.write(f"- 数据集: {original_dataset.name}\n")
            f.write(f"- 问题数量: {len(original_dataset)}\n")
            f.write(f"- 评估时间: {results.get('metadata', {}).get('timestamp', 'N/A')}\n\n")
            
            f.write(f"## 评分\n\n")
            scores = results["scores"]
            avg_score = sum(scores.values()) / len(scores)
            f.write(f"**平均分数**: {avg_score:.3f}\n\n")
            f.write("| 指标 | 分数 | 评价 |\n")
            f.write("|------|------|------|\n")
            for metric, score in scores.items():
                status = "✅ 优秀" if score >= 0.85 else "🟡 良好" if score >= 0.75 else "🔴 需改进"
                f.write(f"| {metric} | {score:.3f} | {status} |\n")
            
            f.write(f"\n## 样本示例\n\n")
            for i, sample in enumerate(filled_dataset.samples[:3], 1):
                f.write(f"### 示例 {i}\n\n")
                f.write(f"**问题**: {sample.question}\n\n")
                f.write(f"**RAG 答案**: {sample.answer[:200]}...\n\n")
                f.write(f"**参考答案**: {sample.ground_truth[:200]}...\n\n")
                f.write(f"**检索文档数**: {len(sample.contexts)}\n\n")
        
        print(f"💾 详细报告已保存: {report_path}")
    
    print()


async def main():
    parser = argparse.ArgumentParser(
        description="使用已生成的测试数据集评估 RAG 系统"
    )
    parser.add_argument(
        'dataset',
        type=Path,
        help='测试数据集路径（JSON 文件）'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        default=Path('data/evaluation'),
        help='输出目录（默认: data/evaluation）'
    )
    parser.add_argument(
        '--metrics', '-m',
        nargs='+',
        choices=['faithfulness', 'answer_relevancy', 'context_precision', 
                 'answer_similarity', 'answer_correctness', 'context_recall'],
        default=['faithfulness', 'answer_relevancy', 'context_precision'],
        help='评估指标（默认: faithfulness answer_relevancy context_precision）'
    )
    parser.add_argument(
        '--save-details',
        action='store_true',
        help='保存详细报告'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("🎯 RAG 系统评估 - 使用已生成的数据集")
    print("=" * 80)
    print()
    
    # 验证文件
    if not args.dataset.exists():
        print(f"❌ 数据集文件不存在: {args.dataset}")
        return
    
    # 初始化
    print("🔧 初始化系统...")
    try:
        settings = AppSettings()
        llm = build_llm(settings)
        embeddings = build_embedding_function(settings)
        vector_store = load_vector_store()  # 不需要传递参数
        
        if not vector_store:
            print("❌ 向量库为空! 请先导入文档")
            return
        
        # 创建检索器
        retriever = RetrieverFactory.create_from_settings(
            settings=settings,
            vector_store=vector_store
        )
        
        # 创建重排器（如果启用）
        reranker = None
        if settings.reranker.enabled:
            reranker = RerankerFactory.create_from_settings(settings)
        
        print(f"   LLM: {settings.llm.provider} / {settings.llm.model}")
        print(f"   检索器: {retriever.__class__.__name__}")
        if reranker:
            print(f"   重排器: {reranker.__class__.__name__}")
        print()
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 1: 加载数据集
    print("=" * 80)
    print("步骤 1: 加载测试数据集")
    print("=" * 80)
    print()
    
    try:
        dataset = EvaluationDataset.load(args.dataset)
        print(f"✅ 加载数据集: {dataset.name}")
        print(f"   问题数量: {len(dataset)}")
        print()
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return
    
    # Step 2: 运行 RAG 系统
    print("=" * 80)
    print("步骤 2: 运行 RAG 系统")
    print("=" * 80)
    print()
    
    filled_dataset = await fill_rag_responses(
        dataset, retriever, reranker, llm, settings
    )
    
    # Step 3: RAGAS 评估
    print("=" * 80)
    print("步骤 3: RAGAS 评估")
    print("=" * 80)
    print()
    
    # 转换指标名称
    metrics = [EvaluationMetrics(m) for m in args.metrics]
    
    results = await evaluate_dataset(
        filled_dataset, llm, embeddings, metrics
    )
    
    # Step 4: 分析结果
    if results:
        analyze_results(results, dataset)
    
    # Step 5: 保存结果
    print("=" * 80)
    print("步骤 5: 保存结果")
    print("=" * 80)
    print()
    
    save_results(
        dataset, filled_dataset, results, 
        args.output_dir, args.save_details
    )
    
    # 完成
    print("=" * 80)
    print("✅ 评估完成!")
    print("=" * 80)
    print()


if __name__ == "__main__":
    asyncio.run(main())

