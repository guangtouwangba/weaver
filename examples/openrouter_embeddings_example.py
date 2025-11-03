"""OpenRouter Embeddings 使用示例"""

from rag_core.chains.embeddings import OpenRouterEmbeddings

# ============================================================================
# 示例 1: 基本用法 - Google Gemini Embedding
# ============================================================================

print("示例 1: Google Gemini Embedding")
print("=" * 60)

embeddings = OpenRouterEmbeddings(
    model="google/gemini-embedding-001",
    openrouter_api_key="your-openrouter-api-key",
)

# 生成文档 embeddings
texts = ["Hello World", "OpenRouter is amazing", "AI and ML"]
vectors = embeddings.embed_documents(texts)

print(f"生成了 {len(vectors)} 个 embeddings")
print(f"每个 embedding 的维度: {len(vectors[0])}")
print(f"第一个向量的前 5 个值: {vectors[0][:5]}")

# 生成查询 embedding
query = "search query example"
query_vector = embeddings.embed_query(query)
print(f"\n查询向量维度: {len(query_vector)}")
print(f"查询向量前 5 个值: {query_vector[:5]}")

# ============================================================================
# 示例 2: 完整配置 - 使用所有可选参数
# ============================================================================

print("\n\n示例 2: 完整配置")
print("=" * 60)

embeddings_full = OpenRouterEmbeddings(
    model="google/gemini-embedding-001",
    openrouter_api_key="your-openrouter-api-key",
    # OpenRouter 排名（可选）
    site_url="https://yoursite.com",
    site_name="Your App Name",
    # Embedding 参数
    dimensions=768,  # Gemini 默认是 768
    encoding_format="float",
    # 请求参数
    max_retries=3,
    timeout=60.0,
)

texts = ["This is a test"]
vectors = embeddings_full.embed_documents(texts)
print(f"生成了 {len(vectors)} 个 embeddings，维度: {len(vectors[0])}")

# ============================================================================
# 示例 3: 使用不同的模型
# ============================================================================

print("\n\n示例 3: 使用不同模型")
print("=" * 60)

# OpenAI Text Embedding 3 Small
openai_embeddings = OpenRouterEmbeddings(
    model="openai/text-embedding-3-small",
    openrouter_api_key="your-openrouter-api-key",
    dimensions=1536,
)

# Cohere Embed English v3
cohere_embeddings = OpenRouterEmbeddings(
    model="cohere/embed-english-v3.0",
    openrouter_api_key="your-openrouter-api-key",
    dimensions=1024,
)

print("支持的模型示例:")
print("- Google Gemini: google/gemini-embedding-001 (768维)")
print("- OpenAI Small: openai/text-embedding-3-small (1536维)")
print("- OpenAI Large: openai/text-embedding-3-large (3072维)")
print("- Cohere: cohere/embed-english-v3.0 (1024维)")
print("- Voyage: voyage/voyage-2 (1024维)")

# ============================================================================
# 示例 4: 与 LangChain 集成
# ============================================================================

print("\n\n示例 4: 与 LangChain 集成")
print("=" * 60)

from langchain.vectorstores import FAISS
from langchain.schema import Document

# 创建文档
documents = [
    Document(page_content="The sky is blue", metadata={"source": "doc1"}),
    Document(page_content="The grass is green", metadata={"source": "doc2"}),
    Document(page_content="The sun is yellow", metadata={"source": "doc3"}),
]

# 使用 OpenRouter embeddings 创建向量存储
embeddings = OpenRouterEmbeddings(
    model="google/gemini-embedding-001",
    openrouter_api_key="your-openrouter-api-key",
)

# 创建 FAISS 向量存储
vectorstore = FAISS.from_documents(documents, embeddings)

# 搜索
query = "What color is the sky?"
results = vectorstore.similarity_search(query, k=2)

print(f"查询: {query}")
print(f"找到 {len(results)} 个相关文档:")
for i, doc in enumerate(results, 1):
    print(f"{i}. {doc.page_content} (source: {doc.metadata['source']})")

# ============================================================================
# 示例 5: 从环境变量读取配置
# ============================================================================

print("\n\n示例 5: 从环境变量读取配置")
print("=" * 60)

from shared_config.settings import AppSettings
from rag_core.chains.embeddings import build_embedding_function

# 从 .env 文件读取配置
settings = AppSettings()

# 自动根据配置创建相应的 embeddings
embeddings = build_embedding_function(settings)

print(f"Provider: {settings.embedding_provider}")
print(f"Model: {settings.embedding_model}")
print(f"Embeddings type: {type(embeddings).__name__}")

# 使用
texts = ["Test from environment config"]
vectors = embeddings.embed_documents(texts)
print(f"生成了 {len(vectors)} 个 embeddings，维度: {len(vectors[0])}")

# ============================================================================
# 示例 6: 错误处理
# ============================================================================

print("\n\n示例 6: 错误处理")
print("=" * 60)

try:
    embeddings = OpenRouterEmbeddings(
        model="google/gemini-embedding-001",
        openrouter_api_key="invalid-key",
        max_retries=2,
        timeout=10.0,
    )
    vectors = embeddings.embed_documents(["test"])
except Exception as e:
    print(f"捕获到错误: {type(e).__name__}: {str(e)}")
    print("请检查:")
    print("1. API Key 是否正确")
    print("2. 网络连接是否正常")
    print("3. OpenRouter 服务是否可用")

print("\n\n示例完成！")
print("=" * 60)
print("\n配置 .env 文件后运行:")
print("  EMBEDDING_PROVIDER=openrouter")
print("  EMBEDDING_MODEL=google/gemini-embedding-001")
print("  OPENROUTER_API_KEY=your-key-here")

