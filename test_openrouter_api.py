#!/usr/bin/env python3
"""测试 OpenRouter API 是否支持 embeddings"""

import os
from openai import OpenAI

api_key = os.getenv("OPENROUTER_API_KEY", "your-key")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

print("测试 OpenRouter Embeddings API...")
print(f"API Key: {api_key[:20]}...")
print()

# 测试1: 标准 embeddings API
print("1️⃣ 测试标准 embeddings endpoint:")
try:
    response = client.embeddings.create(
        model="openai/text-embedding-3-small",
        input=["Hello world"],
    )
    print(f"✅ 成功！维度: {len(response.data[0].embedding)}")
except Exception as e:
    print(f"❌ 失败: {e}")
    print(f"   错误类型: {type(e).__name__}")

print()

# 测试2: 尝试其他模型
print("2️⃣ 测试其他 embedding 模型:")
for model in ["google/text-embedding-004", "cohere/embed-english-v3.0"]:
    try:
        response = client.embeddings.create(model=model, input=["test"])
        print(f"✅ {model} 成功")
    except Exception as e:
        print(f"❌ {model} 失败: {type(e).__name__}")

print()
print("如果全部失败，说明 OpenRouter 不支持 embeddings API")
print("建议使用 EMBEDDING_PROVIDER=fake 或 EMBEDDING_PROVIDER=openai")

