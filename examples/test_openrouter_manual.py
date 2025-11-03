#!/usr/bin/env python3
"""Manual test script for OpenRouter embeddings.

Run this script directly to test OpenRouter functionality:
    python examples/test_openrouter_manual.py
"""

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test OpenRouter embeddings
from rag_core.chains.embeddings import OpenRouterEmbeddings

print("Testing OpenRouter Embeddings\n" + "=" * 60)

embeddings = OpenRouterEmbeddings(model="google/gemini-embedding-001")

texts = [
    "Hello, world!",
    "LangChain is great for building LLM applications.",
    "Embeddings convert text to vectors.",
]

print(f"Generating embeddings for {len(texts)} texts...")
vectors = embeddings.embed_documents(texts)

print(f"\nResults:")
print(f"- Generated {len(vectors)} embeddings")
print(f"- Vector dimension: {len(vectors[0])}")

for i, (text, embedding) in enumerate(zip(texts, vectors), 1):
    print(f"\n{i}. Text: {text}")
    print(f"   Embedding (first 5 values): {embedding[:5]}")

print("\n" + "=" * 60)
print("✅ OpenRouter embeddings test completed successfully!")

