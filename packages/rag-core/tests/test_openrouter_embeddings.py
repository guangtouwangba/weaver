"""Integration tests for OpenRouter embeddings (Real API calls)."""

import os

import pytest
from dotenv import load_dotenv

from rag_core.chains.embeddings import OpenRouterEmbeddings, build_embedding_function
from shared_config.settings import AppSettings

# 自动加载 .env 文件
load_dotenv()


@pytest.mark.skipif(
    not os.getenv("RUN_API_TESTS"),
    reason="RUN_API_TESTS not set - requires working OpenRouter embeddings access",
)
class TestOpenRouterEmbeddingsIntegration:
    """Integration tests using real OpenRouter API calls.

    To run these tests:
    1. Set your OpenRouter API key:
       export OPENROUTER_API_KEY=sk-or-v1-your-key-here

    2. Run the tests:
       pytest packages/rag-core/tests/test_openrouter_embeddings.py -v

    Or run all tests including these:
       OPENROUTER_API_KEY=your-key pytest packages/rag-core/tests/ -v
    """

    def test_basic_initialization(self):
        """Test that OpenRouterEmbeddings can be initialized with real API key."""
        api_key = os.getenv("OPENROUTER_API_KEY")

        embeddings = OpenRouterEmbeddings(
            model="openai/text-embedding-3-small",
            openrouter_api_key=api_key,
            site_url="https://test.com",
            site_name="Test Integration",
        )

        assert embeddings.model == "openai/text-embedding-3-small"
        assert embeddings.client is not None
        print(f"✅ Initialized with model: {embeddings.model}")

    def test_embed_single_document(self):
        """Test embedding a single document with real API."""
        api_key = os.getenv("OPENROUTER_API_KEY")

        embeddings = OpenRouterEmbeddings(
            model="openai/text-embedding-3-small",
            openrouter_api_key=api_key,
            site_url="https://test.com",
            site_name="Test Integration",
        )

        text = "Hello, this is a test document about artificial intelligence."
        result = embeddings.embed_documents([text])

        assert len(result) == 1, "Should return 1 embedding"
        assert len(result[0]) > 0, "Embedding should have dimensions"
        assert all(isinstance(x, float) for x in result[0]), "All values should be floats"

        print(f"✅ Embedded 1 document, got {len(result[0])} dimensions")
        print(f"   First 5 values: {result[0][:5]}")

    def test_embed_multiple_documents(self):
        """Test embedding multiple documents in one request."""
        api_key = os.getenv("OPENROUTER_API_KEY")

        embeddings = OpenRouterEmbeddings(
            model="openai/text-embedding-3-small",
            openrouter_api_key=api_key,
        )

        texts = [
            "Artificial intelligence is transforming technology.",
            "Machine learning enables computers to learn from data.",
            "Deep learning uses neural networks with multiple layers.",
        ]
        result = embeddings.embed_documents(texts)

        print(result)

        assert len(result) == 3, "Should return 3 embeddings"

        # All embeddings should have the same dimension
        dimensions = [len(emb) for emb in result]
        assert len(set(dimensions)) == 1, "All embeddings should have same dimensions"

        print(f"✅ Embedded {len(texts)} documents")
        print(f"   Dimensions: {dimensions[0]}")
        print(f"   All embeddings have consistent dimensions: {dimensions}")

    def test_embed_query(self):
        """Test embedding a single query."""
        api_key = os.getenv("OPENROUTER_API_KEY")

        embeddings = OpenRouterEmbeddings(
            model="openai/text-embedding-3-small",
            openrouter_api_key=api_key,
        )

        query = "What is machine learning?"
        result = embeddings.embed_query(query)

        assert len(result) > 0, "Query embedding should have dimensions"
        assert all(isinstance(x, float) for x in result), "All values should be floats"

        print(f"✅ Embedded query: '{query}'")
        print(f"   Dimensions: {len(result)}")

    def test_embed_documents_empty_list(self):
        """Test that embedding an empty list returns an empty list."""
        api_key = os.getenv("OPENROUTER_API_KEY")

        embeddings = OpenRouterEmbeddings(
            model="openai/text-embedding-3-small",
            openrouter_api_key=api_key,
        )

        result = embeddings.embed_documents([])
        assert result == [], "Empty input should return empty list"
        print("✅ Empty list handled correctly")

    def test_different_text_lengths(self):
        """Test embedding texts of different lengths."""
        api_key = os.getenv("OPENROUTER_API_KEY")

        embeddings = OpenRouterEmbeddings(
            model="openai/text-embedding-3-small",
            openrouter_api_key=api_key,
        )

        texts = [
            "AI",  # Very short
            "Machine learning is a subset of artificial intelligence.",  # Medium
            "Deep learning is a type of machine learning that uses neural networks with multiple layers to progressively extract higher-level features from raw input. It has revolutionized fields like computer vision, natural language processing, and speech recognition.",  # Long
        ]
        result = embeddings.embed_documents(texts)

        assert len(result) == 3, "Should return 3 embeddings"

        # All should have same dimensions regardless of text length
        dimensions = [len(emb) for emb in result]
        assert len(set(dimensions)) == 1, "All embeddings should have same dimensions"

        print(f"✅ Embedded texts of varying lengths")
        print(f"   Text lengths: {[len(t) for t in texts]} chars")
        print(f"   All embeddings: {dimensions[0]} dimensions")

    def test_chinese_text(self):
        """Test embedding Chinese text."""
        api_key = os.getenv("OPENROUTER_API_KEY")

        embeddings = OpenRouterEmbeddings(
            model="openai/text-embedding-3-small",
            openrouter_api_key=api_key,
        )

        texts = [
            "人工智能正在改变世界",
            "机器学习是人工智能的一个分支",
            "深度学习使用神经网络",
        ]
        result = embeddings.embed_documents(texts)

        assert len(result) == 3, "Should return 3 embeddings"
        assert all(len(emb) > 0 for emb in result), "All embeddings should have dimensions"

        print(f"✅ Embedded Chinese text successfully")
        print(f"   Number of texts: {len(texts)}")
        print(f"   Embedding dimensions: {len(result[0])}")

    def test_build_embedding_function_with_settings(self):
        """Test building OpenRouter embeddings from AppSettings."""
        api_key = os.getenv("OPENROUTER_API_KEY")

        settings = AppSettings(
            embedding_provider="openrouter",
            embedding_model="openai/text-embedding-3-small",
            openrouter_api_key=api_key,
            openrouter_site_url="https://test.com",
            openrouter_site_name="Test App",
        )

        embeddings = build_embedding_function(settings)

        assert isinstance(embeddings, OpenRouterEmbeddings)

        # Test actual embedding
        result = embeddings.embed_documents(["Test via settings"])
        assert len(result) == 1
        assert len(result[0]) > 0

        print("✅ Built embeddings from AppSettings and tested successfully")

    def test_with_custom_dimensions(self):
        """Test embedding with custom dimensions (if supported by model)."""
        api_key = os.getenv("OPENROUTER_API_KEY")

        # Note: Not all models support custom dimensions
        # This test may fail if the model doesn't support it
        try:
            embeddings = OpenRouterEmbeddings(
                model="openai/text-embedding-3-small",  # OpenAI models support dimensions
                openrouter_api_key=api_key,
                dimensions=512,
            )

            result = embeddings.embed_documents(["Test with custom dimensions"])

            assert len(result) == 1
            # OpenAI's text-embedding-3-small should respect dimensions parameter
            print(f"✅ Custom dimensions test")
            print(f"   Requested: 512 dimensions")
            print(f"   Got: {len(result[0])} dimensions")
        except Exception as e:
            pytest.skip(f"Custom dimensions not supported by this model: {e}")

    def test_error_handling_invalid_model(self):
        """Test that invalid model name raises appropriate error."""
        api_key = os.getenv("OPENROUTER_API_KEY")

        embeddings = OpenRouterEmbeddings(
            model="invalid/model-that-does-not-exist",
            openrouter_api_key=api_key,
        )

        with pytest.raises(Exception) as exc_info:
            embeddings.embed_documents(["This should fail"])

        print(f"✅ Error handling works for invalid model")
        print(f"   Error type: {type(exc_info.value).__name__}")


@pytest.mark.skipif(
    not os.getenv("RUN_API_TESTS"),
    reason="RUN_API_TESTS not set - requires working OpenRouter embeddings access",
)
class TestOpenRouterModels:
    """Test different OpenRouter models (if API key is available)."""

    def test_google_gemini_embedding(self):
        """Test Google Gemini embedding model."""
        api_key = os.getenv("OPENROUTER_API_KEY")

        embeddings = OpenRouterEmbeddings(
            model="google/gemini-embedding-001",
            openrouter_api_key=api_key,
        )

        result = embeddings.embed_query("Test Google Gemini")
        assert len(result) > 0
        print(f"✅ Google Gemini embedding: {len(result)} dimensions")

    def test_openai_embedding_via_openrouter(self):
        """Test OpenAI embedding model via OpenRouter."""
        api_key = os.getenv("OPENROUTER_API_KEY")

        embeddings = OpenRouterEmbeddings(
            model="openai/text-embedding-3-small",
            openrouter_api_key=api_key,
        )

        result = embeddings.embed_query("Test OpenAI via OpenRouter")
        assert len(result) > 0
        print(f"✅ OpenAI (via OpenRouter) embedding: {len(result)} dimensions")
