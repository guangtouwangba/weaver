#!/usr/bin/env python3
"""
RAG系统诊断脚本
用于排查文档检索问题
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def check_server():
    """检查服务是否运行"""
    print("=" * 80)
    print("🔧 步骤1: 检查服务状态")
    print("-" * 80)
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ 服务正常运行")
            return True
        else:
            print(f"⚠️  服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        print(f"   请确保已运行: make dev")
        return False


def list_documents():
    """列出所有文档"""
    print("\n" + "=" * 80)
    print("📋 步骤2: 检查已上传的文档")
    print("-" * 80)
    try:
        response = requests.get(f"{BASE_URL}/documents/")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            docs = data.get('documents', [])
            
            if total == 0:
                print("⚠️  向量库中没有文档！")
                print("   原因: 尚未上传任何文档，或文档入库失败")
                print("   解决: 先上传文档")
                print()
                print("   curl -X POST 'http://localhost:8000/documents/' \\")
                print("        -F 'file=@your_document.pdf'")
                return []
            else:
                print(f"✅ 找到 {total} 个文档:")
                for i, doc in enumerate(docs, 1):
                    print(f"   [{i}] {doc['filename']}")
                    print(f"       • Document ID: {doc['document_id']}")
                    print(f"       • Chunks: {doc['chunk_count']}")
                return docs
        else:
            print(f"❌ 获取文档列表失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return []
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return []


def test_qa_all_documents():
    """测试在所有文档中搜索"""
    print("\n" + "=" * 80)
    print("💬 步骤3: 测试全局搜索（不指定document_ids）")
    print("-" * 80)
    try:
        payload = {
            "question": "文档的主要内容是什么？",
            "top_k": 4
        }
        print(f"请求: {payload}")
        response = requests.post(f"{BASE_URL}/qa/", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            sources = data.get('sources', [])
            answer = data.get('answer', '')
            
            print(f"\n✅ 请求成功")
            print(f"   • 检索到 {len(sources)} 个来源")
            print(f"   • 答案长度: {len(answer)} 字符")
            
            if len(sources) == 0:
                print(f"\n⚠️  警告: 没有检索到任何文档!")
                print(f"   可能原因:")
                print(f"   1. 向量库确实为空")
                print(f"   2. Embedding模型配置错误")
                print(f"   3. FAISS索引损坏")
            else:
                print(f"\n   答案预览:")
                print(f"   {answer[:200]}...")
                print(f"\n   来源预览:")
                for i, source in enumerate(sources[:2], 1):
                    print(f"   [{i}] {source['content'][:80]}...")
                    if source.get('metadata'):
                        print(f"       Metadata: {source['metadata']}")
            
            return data
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None


def test_qa_with_filter(document_id):
    """测试带文档过滤的搜索"""
    print("\n" + "=" * 80)
    print(f"💬 步骤4: 测试文档过滤（指定document_id）")
    print("-" * 80)
    try:
        payload = {
            "question": "这个文档说了什么？",
            "top_k": 4,
            "document_ids": [document_id]
        }
        print(f"请求: {payload}")
        response = requests.post(f"{BASE_URL}/qa/", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            sources = data.get('sources', [])
            answer = data.get('answer', '')
            
            print(f"\n✅ 请求成功")
            print(f"   • 检索到 {len(sources)} 个来源")
            print(f"   • 答案长度: {len(answer)} 字符")
            
            if len(sources) == 0:
                print(f"\n⚠️  警告: 过滤后没有结果!")
                print(f"   可能原因:")
                print(f"   1. 指定的document_id不存在")
                print(f"   2. metadata中缺少document_id字段")
                print(f"   3. 文档入库时metadata未正确保存")
            else:
                print(f"\n   验证: 所有来源都来自指定文档")
                all_match = all(
                    s.get('metadata', {}).get('document_id') == document_id 
                    for s in sources
                )
                if all_match:
                    print(f"   ✅ 过滤成功!")
                else:
                    print(f"   ⚠️  过滤失败: 存在其他文档的结果")
            
            return data
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None


def check_environment():
    """检查环境配置"""
    print("\n" + "=" * 80)
    print("⚙️  步骤5: 环境配置检查")
    print("-" * 80)
    print("请检查以下环境变量:")
    print()
    print("   • EMBEDDING_PROVIDER: 应该设置为 fake/openai/openrouter")
    print("   • LLM_PROVIDER: 应该设置为 fake/openai/openrouter")
    print()
    print("建议测试配置:")
    print("   export EMBEDDING_PROVIDER=fake")
    print("   export FAKE_EMBEDDING_SIZE=1536")
    print("   export LLM_PROVIDER=fake")
    print()
    print("然后重启服务:")
    print("   make dev")


def main():
    print("\n🔍 RAG系统诊断工具")
    print("=" * 80)
    
    # 1. 检查服务
    if not check_server():
        return
    
    # 2. 列出文档
    docs = list_documents()
    
    # 3. 测试全局搜索
    qa_result = test_qa_all_documents()
    
    # 4. 如果有文档，测试过滤搜索
    if docs:
        test_qa_with_filter(docs[0]['document_id'])
    
    # 5. 环境配置建议
    check_environment()
    
    print("\n" + "=" * 80)
    print("✨ 诊断完成")
    print("=" * 80)
    
    # 总结
    print("\n📊 诊断总结:")
    if not docs:
        print("   ❌ 主要问题: 向量库为空")
        print("   🔧 解决方案: 上传文档")
    elif qa_result and len(qa_result.get('sources', [])) == 0:
        print("   ❌ 主要问题: 检索失败（向量库有数据但无法检索）")
        print("   🔧 解决方案: 检查Embedding配置")
    else:
        print("   ✅ 系统运行正常")
    
    print()


if __name__ == "__main__":
    main()

