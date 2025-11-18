#!/usr/bin/env python3
"""
运行时评估系统示例

演示如何在 RAG 系统中集成运行时评估
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import asyncio
import logging
import sys
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ========================================
# 配置日志
# ========================================
logging.basicConfig(
    level=logging.INFO,  # 使用 INFO 级别查看评估过程
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler('runtime_evaluation_example.log')  # 保存到文件
    ]
)

# 如果想看更详细的信息，可以设置为 DEBUG
# logging.getLogger('rag_core.evaluation').setLevel(logging.DEBUG)

from rag_core.evaluation import (
    create_runtime_evaluator,
    EvaluationMode,
)
from rag_core.chains.llm import build_llm
from rag_core.chains.embeddings import build_embedding_function
from rag_core.chains.vectorstore import load_vector_store
from rag_core.retrievers import RetrieverFactory
from shared_config.settings import AppSettings


async def simulate_rag_query(
    question: str,
    retriever,
    llm,
    runtime_evaluator
):
    """
    模拟一次 RAG 查询，并进行运行时评估。
    
    Args:
        question: 用户问题
        retriever: 检索器
        llm: LLM
        runtime_evaluator: 运行时评估器
    """
    query_id = str(uuid.uuid4())
    
    print(f"\n{'='*60}")
    print(f"📝 查询: {question}")
    print(f"   Query ID: {query_id}")
    
    try:
        # 1. 检索相关文档
        print(f"🔍 检索相关文档...")
        retrieved_docs = await retriever.retrieve(question, top_k=5)
        contexts = [doc.page_content for doc in retrieved_docs]
        print(f"   ✓ 检索到 {len(contexts)} 个文档")
        
        # 2. 生成答案
        print(f"🤖 生成答案...")
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
        
        print(f"   ✓ 答案生成完成")
        print(f"   答案: {answer[:100]}...")
        
        # 3. 记录到运行时评估系统
        print(f"📊 记录到评估系统...")
        await runtime_evaluator.record_query(
            query_id=query_id,
            question=question,
            answer=answer,
            contexts=contexts,
            metadata={
                "source": "example",
                "num_contexts": len(contexts)
            }
        )
        
        # 判断是否会被评估
        if runtime_evaluator.should_evaluate():
            print(f"   ✅ 该查询将被评估")
        else:
            print(f"   ⏭️  该查询已跳过评估（采样）")
        
        return {
            "query_id": query_id,
            "question": question,
            "answer": answer,
            "contexts": contexts
        }
    
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def evaluation_callback(result: dict):
    """评估完成后的回调函数"""
    print(f"\n🎯 评估完成回调:")
    print(f"   Query ID: {result.get('query_id', 'N/A')}")
    print(f"   Scores: {result.get('scores', {})}")


async def main():
    print("\n" + "="*60)
    print("🎯 运行时评估系统示例")
    print("="*60)
    print()
    
    # ========================================
    # 1. 初始化系统
    # ========================================
    print("🔧 初始化系统...")
    try:
        settings = AppSettings()
        llm = build_llm(settings)
        embeddings = build_embedding_function(settings)
        vector_store = load_vector_store()  # 不需要传递参数
        
        if not vector_store:
            print("❌ 向量库为空! 请先导入文档")
            return
        
        retriever = RetrieverFactory.create_from_settings(
            settings=settings,
            vector_store=vector_store
        )
        
        print(f"✅ 系统初始化完成")
        print()
    
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # ========================================
    # 2. 创建运行时评估器
    # ========================================
    print("📊 创建运行时评估器...")
    print()
    
    # 方式 1: 采样评估模式（推荐用于生产）
    runtime_evaluator = create_runtime_evaluator(
        llm=llm,
        embeddings=embeddings,
        mode="sampling",          # 采样模式
        sampling_rate=0.5,        # 评估 50% 的查询（示例用，生产环境建议 0.1）
        metrics=["faithfulness", "answer_relevancy"]
    )
    
    # 方式 2: 异步评估所有查询（适合测试环境）
    # runtime_evaluator = create_runtime_evaluator(
    #     llm=llm,
    #     embeddings=embeddings,
    #     mode="async_all",
    #     metrics=["faithfulness", "answer_relevancy"]
    # )
    
    # 方式 3: 批量评估模式（适合离线分析）
    # runtime_evaluator = create_runtime_evaluator(
    #     llm=llm,
    #     embeddings=embeddings,
    #     mode="batch",
    #     metrics=["faithfulness", "answer_relevancy"]
    # )
    
    # 设置回调
    runtime_evaluator.on_evaluation_complete = evaluation_callback
    
    # 启动评估器（如果是批量模式）
    await runtime_evaluator.start()
    
    print()
    
    # ========================================
    # 3. 模拟多次 RAG 查询
    # ========================================
    print("="*60)
    print("模拟 RAG 查询")
    print("="*60)
    
    test_questions = [
        "What is machine learning?",
        "How do neural networks work?",
        "Explain the concept of deep learning",
        "What is the difference between AI and ML?",
        "How does backpropagation work?",
    ]
    
    results = []
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"查询 {i}/{len(test_questions)}")
        print(f"{'='*60}")
        
        result = await simulate_rag_query(
            question=question,
            retriever=retriever,
            llm=llm,
            runtime_evaluator=runtime_evaluator
        )
        
        if result:
            results.append(result)
        
        # 短暂延迟，避免 API 限流
        await asyncio.sleep(2)
    
    # ========================================
    # 4. 等待异步评估完成
    # ========================================
    print(f"\n{'='*60}")
    print("⏳ 等待异步评估完成...")
    print(f"{'='*60}")
    await asyncio.sleep(5)  # 等待异步评估完成
    
    # ========================================
    # 5. 查看统计信息
    # ========================================
    print(f"\n{'='*60}")
    print("📈 评估统计信息")
    print(f"{'='*60}")
    
    stats = runtime_evaluator.get_stats()
    print(f"\n总体统计:")
    print(f"   总查询数: {stats['total_queries']}")
    print(f"   已评估: {stats['evaluated_queries']}")
    print(f"   已跳过: {stats['skipped_queries']}")
    print(f"   评估率: {stats['evaluation_rate']*100:.1f}%")
    print(f"   错误数: {stats['evaluation_errors']}")
    
    if "recent_avg_scores" in stats:
        print(f"\n最近的平均分数:")
        for metric, score in stats["recent_avg_scores"].items():
            print(f"   {metric}: {score:.3f}")
    
    # ========================================
    # 6. 查看最近的评估结果
    # ========================================
    recent_results = runtime_evaluator.get_recent_results(limit=3)
    
    if recent_results:
        print(f"\n最近的评估结果 (最多 3 个):")
        for i, result in enumerate(recent_results, 1):
            print(f"\n   结果 {i}:")
            print(f"      Query ID: {result.get('query_id', 'N/A')}")
            print(f"      Question: {result.get('question', 'N/A')}")
            if 'scores' in result:
                print(f"      Scores:")
                for metric, score in result['scores'].items():
                    print(f"         {metric}: {score:.3f}")
    
    # ========================================
    # 7. 停止评估器
    # ========================================
    print(f"\n{'='*60}")
    print("🛑 停止评估器...")
    await runtime_evaluator.stop()
    
    print(f"\n{'='*60}")
    print("✅ 示例完成！")
    print(f"{'='*60}")
    print()
    print(f"📁 评估结果已保存到: data/evaluation/runtime/")
    print(f"   查看结果: cat data/evaluation/runtime/runtime_evaluation_results.jsonl")
    print()


if __name__ == "__main__":
    asyncio.run(main())

