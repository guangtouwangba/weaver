#!/usr/bin/env python3
"""
测试语言匹配功能
验证系统是否能用与问题相同的语言回答
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_language_matching():
    """测试中英文问答的语言匹配"""
    
    print("=" * 80)
    print("🌏 语言匹配功能测试")
    print("=" * 80)
    
    # 首先确保有文档
    print("\n1️⃣  检查文档...")
    response = requests.get(f"{BASE_URL}/documents/")
    docs = response.json()
    
    if docs['total'] == 0:
        print("⚠️  没有文档，请先上传文档")
        print("\n示例：")
        print("curl -X POST 'http://localhost:8000/documents/' \\")
        print("     -F 'file=@test.pdf'")
        return
    
    print(f"✅ 找到 {docs['total']} 个文档")
    
    # 测试用例
    test_cases = [
        {
            "name": "中文问题",
            "question": "文档的主要内容是什么？",
            "expected_language": "中文",
        },
        {
            "name": "英文问题",
            "question": "What is the main content of the document?",
            "expected_language": "English",
        },
        {
            "name": "中文问题（详细）",
            "question": "请详细总结一下文档中的关键信息。",
            "expected_language": "中文",
        },
        {
            "name": "英文问题（详细）",
            "question": "Please provide a detailed summary of the key points.",
            "expected_language": "English",
        },
    ]
    
    print("\n" + "=" * 80)
    print("2️⃣  测试不同语言的问答")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        print("-" * 80)
        print(f"问题: {test_case['question']}")
        print(f"期望语言: {test_case['expected_language']}")
        
        payload = {
            "question": test_case['question'],
            "top_k": 4
        }
        
        try:
            response = requests.post(f"{BASE_URL}/qa/", json=payload)
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')
                sources_count = len(data.get('sources', []))
                
                print(f"\n答案 ({len(answer)} 字符):")
                print(f"「{answer}」")
                print(f"\n来源数量: {sources_count}")
                
                # 简单的语言检测
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in answer)
                has_english = any('a' <= char.lower() <= 'z' for char in answer)
                
                detected_lang = "未知"
                if has_chinese and not has_english:
                    detected_lang = "中文"
                elif has_english and not has_chinese:
                    detected_lang = "English"
                elif has_chinese and has_english:
                    detected_lang = "混合"
                
                print(f"检测到的语言: {detected_lang}")
                
                # 判断是否匹配
                if test_case['expected_language'] in detected_lang or detected_lang in test_case['expected_language']:
                    print("✅ 语言匹配成功!")
                else:
                    print(f"⚠️  语言不匹配 (期望: {test_case['expected_language']}, 实际: {detected_lang})")
                    
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"响应: {response.text}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")
        
        # 间隔
        if i < len(test_cases):
            time.sleep(1)
    
    print("\n" + "=" * 80)
    print("✨ 测试完成")
    print("=" * 80)
    
    print("\n💡 说明:")
    print("   • 如果使用 fake LLM provider，答案是预设的，不会根据语言调整")
    print("   • 请使用真实的LLM (OpenAI/OpenRouter) 进行测试")
    print()
    print("   配置示例:")
    print("   export LLM_PROVIDER=openai")
    print("   export LLM_MODEL=gpt-3.5-turbo")
    print("   export OPENAI_API_KEY=your_key")
    print()


if __name__ == "__main__":
    test_language_matching()

