#!/usr/bin/env python3
"""诊断脚本：测试OpenRouter各种API endpoint"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY 未设置")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

print("=" * 80)
print("OpenRouter API 诊断")
print("=" * 80)

# Test 1: Chat Completions (这个通常都能工作)
print("\n1️⃣  测试 Chat Completions API:")
print("-" * 80)
try:
    response = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'test successful'"}],
        max_tokens=10,
    )
    print(f"✅ Chat API 工作正常")
    print(f"   响应: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Chat API 失败: {e}")

# Test 2: Embeddings API (你当前的问题)
print("\n2️⃣  测试 Embeddings API (openai/text-embedding-3-small):")
print("-" * 80)
try:
    response = client.embeddings.create(
        model="openai/text-embedding-3-small",
        input=["Hello, world!"],
        encoding_format="float",
    )
    print(f"✅ Embeddings API 工作正常")
    print(f"   响应数据: {response}")
    if response.data:
        print(f"   向量维度: {len(response.data[0].embedding)}")
    else:
        print(f"   ⚠️  response.data 为 None")
        print(f"   完整响应: {response}")
except Exception as e:
    print(f"❌ Embeddings API 失败: {e}")

# Test 3: 尝试不带 provider prefix 的模型名
print("\n3️⃣  测试 Embeddings API (text-embedding-3-small - 不带 openai/ 前缀):")
print("-" * 80)
try:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=["Hello, world!"],
        encoding_format="float",
    )
    print(f"✅ Embeddings API (无前缀) 工作正常")
    print(f"   响应数据: {response}")
    if response.data:
        print(f"   向量维度: {len(response.data[0].embedding)}")
except Exception as e:
    print(f"❌ Embeddings API (无前缀) 失败: {e}")

# Test 4: 检查账户信息
print("\n4️⃣  建议检查:")
print("-" * 80)
print("   • 访问 https://openrouter.ai/ 登录你的账户")
print("   • 检查账户余额和充值状态")
print("   • 查看 API Keys 权限设置")
print("   • 确认 embeddings 功能是否对你的账户可用")

print("\n" + "=" * 80)
print("诊断完成")
print("=" * 80)

