"""Unit tests for user isolation in vector store search."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from research_agent.infrastructure.vector_store.pgvector import PgVectorStore
from research_agent.infrastructure.vector_store.qdrant import QdrantVectorStore


class TestPgVectorStoreUserIsolation:
    """Test user isolation in PgVectorStore."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock(return_value=MagicMock(fetchall=lambda: []))
        session.rollback = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_search_with_user_id_includes_filter(self, mock_session):
        """Test that search with user_id includes user filter in query."""
        store = PgVectorStore(mock_session)

        await store.search(
            query_embedding=[0.1] * 1536,
            project_id=uuid4(),
            limit=5,
            user_id="user-123",
        )

        # Verify execute was called
        mock_session.execute.assert_called_once()
        # The call args should contain user_id in the query
        call_args = mock_session.execute.call_args
        # Get the query text
        query_text = str(call_args[0][0])
        assert "user_id" in query_text

    @pytest.mark.asyncio
    async def test_search_without_user_id_no_filter(self, mock_session, caplog):
        """Test that search without user_id logs warning and doesn't filter."""
        store = PgVectorStore(mock_session)

        with caplog.at_level("WARNING"):
            await store.search(
                query_embedding=[0.1] * 1536,
                project_id=uuid4(),
                limit=5,
                user_id=None,
            )

        # Verify warning was logged
        assert "without user_id" in caplog.text


class TestQdrantVectorStoreUserIsolation:
    """Test user isolation in QdrantVectorStore."""

    @pytest.fixture
    def mock_qdrant_client(self):
        """Create a mock Qdrant client."""
        client = AsyncMock()
        client.query_points = AsyncMock(return_value=MagicMock(points=[]))
        return client

    @pytest.mark.asyncio
    async def test_search_with_user_id_includes_filter(self, mock_qdrant_client):
        """Test that search with user_id includes user filter."""
        store = QdrantVectorStore(client=mock_qdrant_client)

        await store.search(
            query_embedding=[0.1] * 1536,
            project_id=uuid4(),
            limit=5,
            user_id="user-123",
        )

        # Verify query_points was called
        mock_qdrant_client.query_points.assert_called_once()
        # Get the filter from call args
        call_kwargs = mock_qdrant_client.query_points.call_args.kwargs
        query_filter = call_kwargs.get("query_filter")

        # Verify user_id filter is present
        assert query_filter is not None
        must_conditions = query_filter.must
        user_id_conditions = [c for c in must_conditions if c.key == "user_id"]
        assert len(user_id_conditions) == 1
        assert user_id_conditions[0].match.value == "user-123"

    @pytest.mark.asyncio
    async def test_search_without_user_id_no_user_filter(self, mock_qdrant_client):
        """Test that search without user_id doesn't include user filter."""
        store = QdrantVectorStore(client=mock_qdrant_client)

        await store.search(
            query_embedding=[0.1] * 1536,
            project_id=uuid4(),
            limit=5,
            user_id=None,
        )

        # Get the filter from call args
        call_kwargs = mock_qdrant_client.query_points.call_args.kwargs
        query_filter = call_kwargs.get("query_filter")

        # Verify no user_id filter is present
        must_conditions = query_filter.must
        user_id_conditions = [c for c in must_conditions if c.key == "user_id"]
        assert len(user_id_conditions) == 0
