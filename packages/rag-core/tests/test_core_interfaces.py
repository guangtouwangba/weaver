"""Test core interfaces and implementations."""

import pytest

from rag_core.core.exceptions import ConfigurationException, RetrieverException
from rag_core.core.interfaces import RetrieverInterface
from rag_core.core.models import Document
from rag_core.retrievers.factory import RetrieverFactory
from rag_core.retrievers.vector_retriever import VectorRetriever


def test_document_model():
    """Test Document model creation and validation."""
    doc = Document(
        page_content="Python is a programming language.",
        metadata={"source": "test.txt", "page": 1},
        score=0.95,
        id="doc_1",
    )

    assert doc.page_content == "Python is a programming language."
    assert doc.metadata["source"] == "test.txt"
    assert doc.score == 0.95
    assert doc.id == "doc_1"


def test_document_default_values():
    """Test Document model with default values."""
    doc = Document(page_content="Test content")

    assert doc.page_content == "Test content"
    assert doc.metadata == {}
    assert doc.score == 0.0
    assert doc.id is None


def test_document_str_representation():
    """Test Document string representation."""
    doc = Document(page_content="Short text", score=0.8)

    assert "Short text" in str(doc)
    assert "0.80" in str(doc)


def test_vector_retriever_initialization():
    """Test VectorRetriever can be initialized."""
    retriever = VectorRetriever(top_k=5, search_type="similarity")

    assert isinstance(retriever, RetrieverInterface)
    assert retriever.top_k == 5
    assert retriever.search_type == "similarity"


def test_vector_retriever_config():
    """Test VectorRetriever configuration."""
    retriever = VectorRetriever(top_k=10, search_type="mmr")

    config = retriever.get_config()

    assert config["type"] == "vector"
    assert config["top_k"] == 10
    assert config["search_type"] == "mmr"
    assert config["vector_store_initialized"] is False


def test_vector_retriever_no_vector_store():
    """Test VectorRetriever raises exception when vector store not initialized."""
    retriever = VectorRetriever()

    with pytest.raises(RetrieverException) as exc_info:
        retriever.retrieve_sync("test query")

    assert "not initialized" in str(exc_info.value).lower()


def test_retriever_factory_create_vector():
    """Test RetrieverFactory creates VectorRetriever."""
    retriever = RetrieverFactory.create(retriever_type="vector", config={"top_k": 3})

    assert isinstance(retriever, VectorRetriever)
    assert retriever.top_k == 3


def test_retriever_factory_invalid_type():
    """Test RetrieverFactory raises exception for unknown type."""
    with pytest.raises(ConfigurationException) as exc_info:
        RetrieverFactory.create(retriever_type="unknown_type")

    assert "unknown retriever type" in str(exc_info.value).lower()


def test_retriever_factory_from_settings():
    """Test RetrieverFactory.create_from_settings."""
    from shared_config.settings import AppSettings

    settings = AppSettings()  # type: ignore[arg-type]
    retriever = RetrieverFactory.create_from_settings(settings)

    assert isinstance(retriever, VectorRetriever)
    assert retriever.top_k == settings.retriever.top_k


def test_retriever_set_vector_store():
    """Test setting vector store on retriever."""
    retriever = VectorRetriever()

    assert retriever.get_vector_store() is None

    # Create a mock vector store (just an object for testing)
    mock_store = object()
    retriever.set_vector_store(mock_store)  # type: ignore[arg-type]

    assert retriever.get_vector_store() is mock_store


def test_document_score_validation():
    """Test Document score validation (should be 0-1)."""
    # Valid scores
    doc1 = Document(page_content="Test", score=0.0)
    doc2 = Document(page_content="Test", score=1.0)
    doc3 = Document(page_content="Test", score=0.5)

    assert doc1.score == 0.0
    assert doc2.score == 1.0
    assert doc3.score == 0.5

    # Invalid scores should be caught by pydantic
    with pytest.raises(Exception):  # Pydantic validation error
        Document(page_content="Test", score=-0.1)

    with pytest.raises(Exception):  # Pydantic validation error
        Document(page_content="Test", score=1.1)


def test_exception_with_details():
    """Test RAG exceptions with details."""
    exc = RetrieverException(
        "Retrieval failed", details={"query": "test", "error_code": 500}
    )

    assert exc.message == "Retrieval failed"
    assert exc.details["query"] == "test"
    assert exc.details["error_code"] == 500
    assert "Details:" in str(exc)

