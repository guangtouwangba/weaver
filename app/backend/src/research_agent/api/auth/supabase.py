"""Supabase JWT authentication for FastAPI.

This module provides JWT verification and user extraction for Supabase Auth tokens.
"""

import hashlib
import time
from typing import Optional, Tuple

from fastapi import Depends, Header, HTTPException, Request
from pydantic import BaseModel

from research_agent.config import get_settings

settings = get_settings()


class UserContext(BaseModel):
    """User context extracted from JWT or anonymous session."""

    user_id: str
    is_anonymous: bool = False


def _decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without verification (for extracting claims).

    Note: We still verify the signature separately using the JWT secret.
    This is a simple implementation that doesn't require PyJWT dependency.
    """
    import base64
    import json

    try:
        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")

        # Decode payload (middle part)
        # Add padding if necessary
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes)
    except Exception as e:
        raise ValueError(f"Failed to decode JWT: {e}")


def _verify_jwt_signature(token: str, secret: str) -> bool:
    """Verify JWT signature using HMAC-SHA256.

    Supabase uses HS256 (HMAC-SHA256) for JWT signing.
    """
    import base64
    import hmac

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False

        # Create the signing input
        signing_input = f"{parts[0]}.{parts[1]}"

        # Decode the provided signature
        signature_b64 = parts[2]
        padding = 4 - len(signature_b64) % 4
        if padding != 4:
            signature_b64 += "=" * padding
        provided_signature = base64.urlsafe_b64decode(signature_b64)

        # Compute expected signature
        expected_signature = hmac.new(
            secret.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        # Constant-time comparison
        return hmac.compare_digest(provided_signature, expected_signature)
    except Exception:
        return False


def verify_supabase_jwt(token: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    """Verify a Supabase JWT and return the payload.

    Returns:
        Tuple of (is_valid, payload, error_message)
    """
    if not settings.supabase_jwt_secret:
        return False, None, "JWT secret not configured"

    # Verify signature
    if not _verify_jwt_signature(token, settings.supabase_jwt_secret):
        return False, None, "Invalid JWT signature"

    # Decode and validate payload
    try:
        payload = _decode_jwt_payload(token)
    except ValueError as e:
        return False, None, str(e)

    # Check expiration
    exp = payload.get("exp")
    if exp and time.time() > exp:
        return False, None, "Token expired"

    return True, payload, None


def _generate_anon_session_id(request: Request) -> str:
    """Generate a deterministic anonymous session ID from request headers."""
    # Check for client-provided anonymous ID (more secure/unique)
    client_anon_id = request.headers.get("x-anonymous-id")
    if client_anon_id:
        # Hash it to ensure uniform format and prevent injection
        session_hash = hashlib.sha256(client_anon_id.encode()).hexdigest()[:16]
        return f"anon-{session_hash}"

    # Fallback: Use a combination of headers to create a semi-stable session ID
    # Note: This is less secure as users with same UA share session
    user_agent = request.headers.get("user-agent", "")
    # For anonymous users, we use a simple hash - not for security, just identification
    session_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]
    return f"anon-{session_hash}"


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """FastAPI dependency to get authenticated user ID from JWT.

    Raises HTTPException 401 if not authenticated.
    Returns the Supabase user UUID (from JWT 'sub' claim).
    """
    # Auth bypass for local development
    if settings.auth_bypass_enabled:
        return "dev-user-bypass"

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = authorization[7:]  # Remove "Bearer " prefix
    is_valid, payload, error = verify_supabase_jwt(token)

    if not is_valid:
        raise HTTPException(status_code=401, detail=error or "Invalid token")

    # Extract user ID from 'sub' claim
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing user ID")

    return user_id


async def get_optional_user(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> UserContext:
    """FastAPI dependency to get user context, allowing anonymous users.

    Returns UserContext with:
    - Authenticated user: user_id from JWT, is_anonymous=False
    - Anonymous user: anon-{session_id}, is_anonymous=True
    - Dev bypass: dev-user-bypass, is_anonymous=False
    """
    # Auth bypass for local development
    if settings.auth_bypass_enabled:
        return UserContext(user_id="dev-user-bypass", is_anonymous=False)

    # Try to extract authenticated user
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        is_valid, payload, error = verify_supabase_jwt(token)

        # Debug logging
        print(f"[Auth Debug] Token present: True, Token length: {len(token)}")
        print(f"[Auth Debug] JWT secret configured: {bool(settings.supabase_jwt_secret)}")
        print(f"[Auth Debug] is_valid: {is_valid}, error: {error}")

        if is_valid and payload:
            user_id = payload.get("sub")
            print(f"[Auth Debug] Extracted user_id from JWT: {user_id}")
            if user_id:
                return UserContext(user_id=user_id, is_anonymous=False)
    else:
        print(
            f"[Auth Debug] No Bearer token found. Authorization header: {authorization[:50] if authorization else 'None'}..."
        )

    # Fall back to anonymous session
    anon_id = _generate_anon_session_id(request)
    print(f"[Auth Debug] Falling back to anonymous: {anon_id}")
    return UserContext(user_id=anon_id, is_anonymous=True)


# Re-export existing API key auth for backward compatibility
from research_agent.api.auth import get_api_key, hash_api_key

__all__ = [
    "UserContext",
    "verify_supabase_jwt",
    "get_current_user",
    "get_optional_user",
    "get_api_key",
    "hash_api_key",
]
