#!/usr/bin/env python3
"""
RAG系统使用示例
展示如何上传文档并进行问答
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def upload_document(file_path: str):
    """上传文档到RAG系统"""
    print("=" * 80)
    print("📤 步骤1: 上传文档")
    print("-" * 80)
    
    url = f"{BASE_URL}/documents/"
    
    with open(file_path, "rb") as f:
        files = {"file": (file_path, f)}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 文档上传成功!")
        print(f"   ├─ 状态: {result['status']}")
        print(f"   └─ Document ID: {result['document_id']}")
        return result
    else:
        print(f"❌ 上传失败: {response.status_code}")
        print(f"   错误: {response.text}")
        return None


def ask_question(question: str, top_k: int = 4):
    """向RAG系统提问"""
    print("\n" + "=" * 80)
    print("💬 步骤2: 提问")
    print("-" * 80)
    print(f"问题: {question}")
    print("-" * 80)
    
    url = f"{BASE_URL}/qa/"
    payload = {
        "question": question,
        "top_k": top_k
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ 回答:")
        print(f"{result['answer']}")
        print(f"\n📚 引用来源 ({len(result['sources'])} 个):")
        for i, source in enumerate(result['sources'], 1):
            print(f"\n   [{i}] {source['content'][:200]}...")
            if source.get('metadata'):
                print(f"       元数据: {source['metadata']}")
        return result
    else:
        print(f"❌ 问答失败: {response.status_code}")
        print(f"   错误: {response.text}")
        return None


def main():
    print("\n🚀 RAG系统使用示例")
    print("=" * 80)
    
    # 示例1: 上传文档
    print("\n📋 使用说明:")
    print("   1. 确保服务已启动: make dev")
    print("   2. 准备要上传的文档（PDF、TXT、DOCX等）")
    print("   3. 修改下面的 file_path 为你的文档路径")
    print()
    
    # 这里替换为你的文档路径
    file_path = "your_document.pdf"
    
    # 检查文件是否存在
    try:
        with open(file_path, "r"):
            pass
    except FileNotFoundError:
        print(f"⚠️  示例文档不存在: {file_path}")
        print(f"\n💡 使用方法:")
        print(f"   python example_usage.py")
        print(f"\n   或者直接使用curl命令:")
        print(f"\n   # 1. 上传文档")
        print(f'   curl -X POST "http://localhost:8000/documents/" \\')
        print(f'        -F "file=@your_document.pdf"')
        print(f"\n   # 2. 提问")
        print(f'   curl -X POST "http://localhost:8000/qa/" \\')
        print(f'        -H "Content-Type: application/json" \\')
        print(f'        -d \'{{"question": "文档的主要内容是什么？", "top_k": 4}}\'')
        return
    
    # 上传文档
    result = upload_document(file_path)
    if not result:
        return
    
    # 等待文档处理完成（后台任务）
    print("\n⏳ 等待文档处理完成（约5秒）...")
    time.sleep(5)
    
    # 提问示例
    questions = [
        "文档的主要内容是什么？",
        "有哪些关键信息？",
    ]
    
    for question in questions:
        ask_question(question)
    
    print("\n" + "=" * 80)
    print("✨ 示例完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()

