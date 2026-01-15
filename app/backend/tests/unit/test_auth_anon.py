"""Tests for anonymous session ID generation security."""

import hashlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request

from research_agent.api.auth.supabase import get_optional_user


class TestAnonymousSessionSecurity:
    """Tests for secure anonymous session generation."""

    @pytest.fixture(autouse=True)
    def setup_settings(self):
        """Mock settings for each test."""
        with patch("research_agent.api.auth.supabase.settings") as mock_settings:
            mock_settings.supabase_jwt_secret = "test-secret-key"
            mock_settings.auth_bypass_enabled = False
            yield mock_settings

    @pytest.mark.asyncio
    async def test_header_based_id_generation(self):
        """Test that X-Anonymous-ID header generates unique IDs for same User-Agent."""
        # Two requests with same User-Agent but different anonymous IDs
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

        # Request 1
        req1 = MagicMock(spec=Request)
        req1.headers = {
            "user-agent": user_agent,
            "x-anonymous-id": "uuid-1234-5678"
        }

        # Request 2
        req2 = MagicMock(spec=Request)
        req2.headers = {
            "user-agent": user_agent,
            "x-anonymous-id": "uuid-8765-4321"
        }

        user1 = await get_optional_user(request=req1, authorization=None)
        user2 = await get_optional_user(request=req2, authorization=None)

        assert user1.is_anonymous is True
        assert user2.is_anonymous is True
        assert user1.user_id != user2.user_id

        # Verify format (anon-HASH)
        assert user1.user_id.startswith("anon-")

        # Verify hash correctness
        expected_hash = hashlib.sha256(b"uuid-1234-5678").hexdigest()[:16]
        assert user1.user_id == f"anon-{expected_hash}"

    @pytest.mark.asyncio
    async def test_fallback_to_user_agent(self):
        """Test fallback to User-Agent when X-Anonymous-ID is missing."""
        user_agent = "Mozilla/5.0 (Legacy)"

        req = MagicMock(spec=Request)
        req.headers = {
            "user-agent": user_agent
        }

        user = await get_optional_user(request=req, authorization=None)

        assert user.is_anonymous is True

        # Verify it uses UA hash
        expected_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]
        assert user.user_id == f"anon-{expected_hash}"

    @pytest.mark.asyncio
    async def test_empty_user_agent_fallback(self):
        """Test fallback with empty UA."""
        req = MagicMock(spec=Request)
        req.headers = {}

        user = await get_optional_user(request=req, authorization=None)

        assert user.is_anonymous is True
        # Hash of empty string
        expected_hash = hashlib.sha256(b"").hexdigest()[:16]
        assert user.user_id == f"anon-{expected_hash}"
