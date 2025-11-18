#!/usr/bin/env python3
"""
从 PDF 文档自动生成测试问题和参考答案

这个脚本会：
1. 读取 PDF 文档
2. 提取关键内容片段
3. 使用 LLM 生成高质量的问题和答案
4. 保存为评估数据集

Usage:
    # 从单个 PDF 生成问题
    python examples/generate_test_questions.py data/uploads/your_paper.pdf
    
    # 从多个 PDF 生成问题
    python examples/generate_test_questions.py data/uploads/*.pdf
    
    # 指定生成数量
    python examples/generate_test_questions.py data/uploads/paper.pdf --num-questions 20
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Optional
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag_core.chains.llm import build_llm
from rag_core.evaluation import EvaluationDataset
from shared_config.settings import AppSettings
from langchain_community.document_loaders import PyPDFLoader


# ========================================
# 提示词模板
# ========================================

QUESTION_GENERATION_PROMPT = """你是一个专业的测试问题生成专家。基于给定的文档内容，生成高质量的测试问题和参考答案。

要求：
1. 问题应该覆盖文档的关键概念和重要信息
2. 问题难度分为 easy（基础概念）、medium（理解应用）、hard（深入分析）
3. 每个问题都要有明确的参考答案（ground truth）
4. 问题应该是 RAG 系统能够回答的（答案在文档中）
5. 避免过于简单的是非题，多问"如何"、"为什么"、"是什么"

文档内容：
{context}

请生成 {num_questions} 个测试问题，返回 JSON 格式：

[
  {{
    "question": "问题内容",
    "ground_truth": "详细的参考答案",
    "difficulty": "easy|medium|hard",
    "topic": "问题主题",
    "question_type": "factual|conceptual|analytical"
  }},
  ...
]

只返回 JSON，不要其他说明。
"""


# ========================================
# 文档处理
# ========================================

def load_pdf_documents(pdf_paths: List[Path]) -> List[Dict]:
    """
    加载 PDF 文档并提取内容。
    
    Args:
        pdf_paths: PDF 文件路径列表
    
    Returns:
        文档内容列表
    """
    print(f"📄 加载 PDF 文档...")
    print(f"   文件数量: {len(pdf_paths)}")
    print()
    
    all_docs = []
    for pdf_path in pdf_paths:
        print(f"   处理: {pdf_path.name}")
        try:
            # 使用 PyPDFLoader 加载 PDF
            loader = PyPDFLoader(str(pdf_path))
            docs = loader.load()
            
            if docs:
                all_docs.append({
                    "source": pdf_path.name,
                    "content": "\n\n".join([doc.page_content for doc in docs]),
                    "num_pages": len(docs)
                })
                print(f"      ✓ 提取了 {len(docs)} 页内容")
            else:
                print(f"      ✗ 无法提取内容")
                
        except Exception as e:
            print(f"      ✗ 错误: {e}")
            continue
    
    print(f"\n✅ 成功加载 {len(all_docs)} 个文档\n")
    return all_docs


def extract_key_chunks(content: str, chunk_size: int = 2000, num_chunks: int = 5) -> List[str]:
    """
    从文档中提取关键片段用于生成问题。
    
    Args:
        content: 文档内容
        chunk_size: 每个片段的大小
        num_chunks: 提取片段数量
    
    Returns:
        文档片段列表
    """
    # 简单分块策略：按段落分割
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    # 合并成大块
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk)
    
    # 均匀采样
    if len(chunks) > num_chunks:
        step = len(chunks) // num_chunks
        chunks = [chunks[i * step] for i in range(num_chunks)]
    
    return chunks


# ========================================
# 问题生成
# ========================================

async def generate_questions_for_chunk(
    chunk: str,
    llm,
    num_questions: int = 3,
    source: str = "unknown"
) -> List[Dict]:
    """
    为单个文档片段生成问题。
    
    Args:
        chunk: 文档片段
        llm: LLM 实例
        num_questions: 生成问题数量
        source: 来源文档名称
    
    Returns:
        问题列表
    """
    try:
        # 构建 prompt
        prompt = QUESTION_GENERATION_PROMPT.format(
            context=chunk[:3000],  # 限制上下文长度
            num_questions=num_questions
        )
        
        # 调用 LLM
        response = await llm.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # 解析 JSON
        # 尝试提取 JSON（可能包含在其他文本中）
        import re
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            questions = json.loads(json_match.group())
        else:
            questions = json.loads(response_text)
        
        # 添加源信息
        for q in questions:
            q['source'] = source
        
        return questions
        
    except json.JSONDecodeError as e:
        print(f"      ✗ JSON 解析失败: {e}")
        print(f"      响应: {response_text[:200]}...")
        return []
    except Exception as e:
        print(f"      ✗ 生成失败: {e}")
        return []


async def generate_questions_from_documents(
    documents: List[Dict],
    llm,
    questions_per_chunk: int = 3,
    chunks_per_doc: int = 5
) -> List[Dict]:
    """
    从所有文档生成问题。
    
    Args:
        documents: 文档列表
        llm: LLM 实例
        questions_per_chunk: 每个片段生成的问题数
        chunks_per_doc: 每个文档提取的片段数
    
    Returns:
        所有生成的问题
    """
    print("🤖 使用 LLM 生成测试问题...")
    print(f"   每个文档片段: {questions_per_chunk} 个问题")
    print(f"   每个文档: {chunks_per_doc} 个片段")
    print()
    
    all_questions = []
    
    for doc in documents:
        source = doc['source']
        content = doc['content']
        
        print(f"   处理文档: {source}")
        
        # 提取关键片段
        chunks = extract_key_chunks(content, num_chunks=chunks_per_doc)
        print(f"      提取了 {len(chunks)} 个片段")
        
        # 为每个片段生成问题
        for i, chunk in enumerate(chunks, 1):
            print(f"      片段 {i}/{len(chunks)}...", end=" ")
            
            questions = await generate_questions_for_chunk(
                chunk,
                llm,
                num_questions=questions_per_chunk,
                source=source
            )
            
            if questions:
                all_questions.extend(questions)
                print(f"✓ 生成 {len(questions)} 个问题")
            else:
                print("✗ 失败")
            
            # 避免 API 限流
            await asyncio.sleep(1)
        
        print()
    
    print(f"✅ 总共生成 {len(all_questions)} 个问题\n")
    return all_questions


# ========================================
# 数据集创建
# ========================================

def create_evaluation_dataset(
    questions: List[Dict],
    output_path: Path
) -> EvaluationDataset:
    """
    创建评估数据集并保存。
    
    Args:
        questions: 问题列表
        output_path: 输出文件路径
    
    Returns:
        评估数据集
    """
    print("📊 创建评估数据集...")
    
    dataset = EvaluationDataset(
        name=output_path.stem,
        description=f"Auto-generated test set with {len(questions)} questions"
    )
    
    # 添加问题（注意：这里只有 question 和 ground_truth，没有 answer 和 contexts）
    # 这些将在运行 RAG 系统时填充
    for q in questions:
        dataset.add_sample(
            question=q['question'],
            answer="",  # 待 RAG 系统填充
            contexts=[],  # 待 RAG 系统填充
            ground_truth=q['ground_truth'],
            metadata={
                'source': q.get('source', 'unknown'),
                'difficulty': q.get('difficulty', 'medium'),
                'topic': q.get('topic', 'general'),
                'question_type': q.get('question_type', 'factual')
            }
        )
    
    # 保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.save(output_path)
    
    print(f"✅ 数据集已保存: {output_path}")
    print(f"   问题总数: {len(dataset)}")
    print()
    
    # 统计信息
    difficulties = {}
    topics = {}
    for sample in dataset.samples:
        diff = sample.metadata.get('difficulty', 'unknown')
        topic = sample.metadata.get('topic', 'unknown')
        difficulties[diff] = difficulties.get(diff, 0) + 1
        topics[topic] = topics.get(topic, 0) + 1
    
    print("   难度分布:")
    for diff, count in sorted(difficulties.items()):
        print(f"      {diff:10s}: {count:3d} ({count/len(dataset)*100:.1f}%)")
    
    print(f"\n   主题分布 (top 5):")
    for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"      {topic:20s}: {count:3d}")
    
    print()
    return dataset


def save_raw_questions(questions: List[Dict], output_path: Path):
    """保存原始问题 JSON（可选，用于查看）。"""
    raw_path = output_path.parent / f"{output_path.stem}_raw.json"
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    print(f"💾 原始问题已保存: {raw_path}\n")


# ========================================
# 主函数
# ========================================

async def main():
    parser = argparse.ArgumentParser(
        description="从 PDF 文档自动生成测试问题和参考答案"
    )
    parser.add_argument(
        'pdf_files',
        nargs='+',
        type=Path,
        help='PDF 文件路径（可以多个）'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('data/evaluation/generated_test_set.json'),
        help='输出数据集路径（默认: data/evaluation/generated_test_set.json）'
    )
    parser.add_argument(
        '--questions-per-chunk', '-q',
        type=int,
        default=3,
        help='每个文档片段生成的问题数（默认: 3）'
    )
    parser.add_argument(
        '--chunks-per-doc', '-c',
        type=int,
        default=5,
        help='每个文档提取的片段数（默认: 5）'
    )
    parser.add_argument(
        '--save-raw',
        action='store_true',
        help='保存原始问题 JSON'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("🎯 自动生成测试问题和参考答案")
    print("=" * 80)
    print()
    
    # 验证文件
    pdf_files = []
    for path in args.pdf_files:
        if path.is_file() and path.suffix.lower() == '.pdf':
            pdf_files.append(path)
        else:
            print(f"⚠️  跳过无效文件: {path}")
    
    if not pdf_files:
        print("❌ 没有找到有效的 PDF 文件")
        return
    
    print(f"📁 找到 {len(pdf_files)} 个 PDF 文件:")
    for f in pdf_files:
        print(f"   - {f.name}")
    print()
    
    # 初始化
    print("🔧 初始化系统...")
    try:
        settings = AppSettings()
        llm = build_llm(settings)
        print(f"   LLM: {settings.llm.provider} / {settings.llm.model}")
        print()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 1: 加载 PDF 文档
    print("=" * 80)
    print("步骤 1: 加载 PDF 文档")
    print("=" * 80)
    print()
    
    documents = load_pdf_documents(pdf_files)
    
    if not documents:
        print("❌ 没有成功加载任何文档")
        return
    
    # Step 2: 生成问题
    print("=" * 80)
    print("步骤 2: 生成测试问题")
    print("=" * 80)
    print()
    
    questions = await generate_questions_from_documents(
        documents,
        llm,
        questions_per_chunk=args.questions_per_chunk,
        chunks_per_doc=args.chunks_per_doc
    )
    
    if not questions:
        print("❌ 没有生成任何问题")
        return
    
    # Step 3: 创建数据集
    print("=" * 80)
    print("步骤 3: 创建评估数据集")
    print("=" * 80)
    print()
    
    dataset = create_evaluation_dataset(questions, args.output)
    
    # 可选：保存原始 JSON
    if args.save_raw:
        save_raw_questions(questions, args.output)
    
    # 显示示例
    print("=" * 80)
    print("📝 示例问题（前 3 个）")
    print("=" * 80)
    print()
    
    for i, sample in enumerate(dataset.samples[:3], 1):
        print(f"{i}. 问题: {sample.question}")
        print(f"   参考答案: {sample.ground_truth[:100]}...")
        print(f"   难度: {sample.metadata.get('difficulty', 'N/A')}")
        print(f"   主题: {sample.metadata.get('topic', 'N/A')}")
        print()
    
    # 完成
    print("=" * 80)
    print("✅ 测试问题生成完成!")
    print("=" * 80)
    print()
    print("📊 下一步:")
    print(f"   1. 查看生成的问题: cat {args.output}")
    print(f"   2. 运行 RAG 评估:")
    print(f"      python examples/evaluate_with_dataset.py {args.output}")
    print()


if __name__ == "__main__":
    asyncio.run(main())

