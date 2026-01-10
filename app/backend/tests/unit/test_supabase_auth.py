"""Unit tests for Supabase JWT authentication."""

import base64
import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock, patch

import pytest


def create_test_jwt(payload: dict, secret: str) -> str:
    """Create a valid JWT for testing with HS256 algorithm."""
    # Header
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()

    # Payload
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()

    # Signature
    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        secret.encode(),
        signing_input.encode(),
        hashlib.sha256,
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()

    return f"{header_b64}.{payload_b64}.{signature_b64}"


class TestVerifySupabaseJWT:
    """Tests for verify_supabase_jwt function."""

    @pytest.fixture(autouse=True)
    def setup_settings(self):
        """Mock settings for each test."""
        with patch("research_agent.api.auth.supabase.settings") as mock_settings:
            mock_settings.supabase_jwt_secret = "test-secret-key"
            mock_settings.auth_bypass_enabled = False
            yield mock_settings

    def test_valid_token(self, setup_settings):
        """Test verification of a valid JWT."""
        from research_agent.api.auth.supabase import verify_supabase_jwt

        payload = {
            "sub": "user-123",
            "exp": int(time.time()) + 3600,  # 1 hour from now
            "email": "test@example.com",
        }
        token = create_test_jwt(payload, "test-secret-key")

        is_valid, decoded_payload, error = verify_supabase_jwt(token)

        assert is_valid is True
        assert decoded_payload["sub"] == "user-123"
        assert error is None

    def test_invalid_signature(self, setup_settings):
        """Test rejection of token with wrong signature."""
        from research_agent.api.auth.supabase import verify_supabase_jwt

        payload = {"sub": "user-123", "exp": int(time.time()) + 3600}
        token = create_test_jwt(payload, "wrong-secret")

        is_valid, decoded_payload, error = verify_supabase_jwt(token)

        assert is_valid is False
        assert decoded_payload is None
        assert error == "Invalid JWT signature"

    def test_expired_token(self, setup_settings):
        """Test rejection of expired token."""
        from research_agent.api.auth.supabase import verify_supabase_jwt

        payload = {
            "sub": "user-123",
            "exp": int(time.time()) - 3600,  # 1 hour ago
        }
        token = create_test_jwt(payload, "test-secret-key")

        is_valid, decoded_payload, error = verify_supabase_jwt(token)

        assert is_valid is False
        assert error == "Token expired"

    def test_malformed_token(self, setup_settings):
        """Test rejection of malformed token."""
        from research_agent.api.auth.supabase import verify_supabase_jwt

        is_valid, decoded_payload, error = verify_supabase_jwt("not.a.valid.token")

        assert is_valid is False
        assert decoded_payload is None

    def test_missing_jwt_secret(self):
        """Test error when JWT secret is not configured."""
        with patch("research_agent.api.auth.supabase.settings") as mock_settings:
            mock_settings.supabase_jwt_secret = ""

            from research_agent.api.auth.supabase import verify_supabase_jwt

            is_valid, decoded_payload, error = verify_supabase_jwt("any.token.here")

            assert is_valid is False
            assert error == "JWT secret not configured"


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.fixture(autouse=True)
    def setup_settings(self):
        """Mock settings for each test."""
        with patch("research_agent.api.auth.supabase.settings") as mock_settings:
            mock_settings.supabase_jwt_secret = "test-secret-key"
            mock_settings.auth_bypass_enabled = False
            yield mock_settings

    @pytest.mark.asyncio
    async def test_valid_authorization(self, setup_settings):
        """Test successful user extraction from valid token."""
        from research_agent.api.auth.supabase import get_current_user

        payload = {"sub": "user-uuid-123", "exp": int(time.time()) + 3600}
        token = create_test_jwt(payload, "test-secret-key")

        user_id = await get_current_user(authorization=f"Bearer {token}")

        assert user_id == "user-uuid-123"

    @pytest.mark.asyncio
    async def test_missing_authorization(self, setup_settings):
        """Test 401 when authorization header is missing."""
        from fastapi import HTTPException
        from research_agent.api.auth.supabase import get_current_user

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=None)

        assert exc_info.value.status_code == 401
        assert "Missing Authorization header" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_authorization_format(self, setup_settings):
        """Test 401 when authorization header has wrong format."""
        from fastapi import HTTPException
        from research_agent.api.auth.supabase import get_current_user

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="Basic abc123")

        assert exc_info.value.status_code == 401
        assert "Invalid Authorization header format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_auth_bypass_enabled(self):
        """Test dev bypass mode returns mock user."""
        with patch("research_agent.api.auth.supabase.settings") as mock_settings:
            mock_settings.auth_bypass_enabled = True

            from research_agent.api.auth.supabase import get_current_user

            user_id = await get_current_user(authorization=None)

            assert user_id == "dev-user-bypass"


class TestGetOptionalUser:
    """Tests for get_optional_user dependency."""

    @pytest.fixture(autouse=True)
    def setup_settings(self):
        """Mock settings for each test."""
        with patch("research_agent.api.auth.supabase.settings") as mock_settings:
            mock_settings.supabase_jwt_secret = "test-secret-key"
            mock_settings.auth_bypass_enabled = False
            yield mock_settings

    @pytest.mark.asyncio
    async def test_authenticated_user(self, setup_settings):
        """Test extraction of authenticated user."""
        from research_agent.api.auth.supabase import get_optional_user

        payload = {"sub": "user-uuid-456", "exp": int(time.time()) + 3600}
        token = create_test_jwt(payload, "test-secret-key")

        mock_request = MagicMock()
        mock_request.headers = {"user-agent": "TestBrowser/1.0"}

        user_ctx = await get_optional_user(
            request=mock_request,
            authorization=f"Bearer {token}",
        )

        assert user_ctx.user_id == "user-uuid-456"
        assert user_ctx.is_anonymous is False

    @pytest.mark.asyncio
    async def test_anonymous_user(self, setup_settings):
        """Test anonymous user gets session ID."""
        from research_agent.api.auth.supabase import get_optional_user

        mock_request = MagicMock()
        mock_request.headers = {"user-agent": "TestBrowser/1.0"}

        user_ctx = await get_optional_user(
            request=mock_request,
            authorization=None,
        )

        assert user_ctx.user_id.startswith("anon-")
        assert user_ctx.is_anonymous is True

    @pytest.mark.asyncio
    async def test_auth_bypass_enabled(self):
        """Test dev bypass mode."""
        with patch("research_agent.api.auth.supabase.settings") as mock_settings:
            mock_settings.auth_bypass_enabled = True

            from research_agent.api.auth.supabase import get_optional_user

            mock_request = MagicMock()
            mock_request.headers = {}

            user_ctx = await get_optional_user(
                request=mock_request,
                authorization=None,
            )

            assert user_ctx.user_id == "dev-user-bypass"
            assert user_ctx.is_anonymous is False
