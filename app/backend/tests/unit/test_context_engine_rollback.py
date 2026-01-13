from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from research_agent.application.use_cases.chat.context_engine import ContextEngine


@pytest.mark.asyncio
async def test_fetch_url_metadata_rolls_back_on_failure():
    session = AsyncMock()
    session.rollback = AsyncMock()

    engine = ContextEngine(session)

    url_id = str(uuid4())
    repo = MagicMock()
    repo.get_by_id = AsyncMock(side_effect=Exception("db error"))

    with patch(
        "research_agent.infrastructure.database.repositories.sqlalchemy_url_content_repo.SQLAlchemyUrlContentRepository",
        return_value=repo,
    ):
        urls = await engine._fetch_url_metadata([url_id])

    session.rollback.assert_awaited()
    assert urls == [{"id": url_id, "title": "URL"}]


@pytest.mark.asyncio
async def test_resolve_canvas_context_rolls_back_on_failure():
    session = AsyncMock()
    session.rollback = AsyncMock()

    engine = ContextEngine(session)

    repo = MagicMock()
    repo.find_by_project = AsyncMock(side_effect=Exception("db error"))

    with patch(
        "research_agent.infrastructure.database.repositories.sqlalchemy_canvas_repo.SQLAlchemyCanvasRepository",
        return_value=repo,
    ):
        text, count = await engine._resolve_canvas_context(
            project_id=uuid4(),
            context_nodes=None,
            context_node_ids=["node-1"],
        )

    session.rollback.assert_awaited()
    assert text == ""
    assert count == 0

