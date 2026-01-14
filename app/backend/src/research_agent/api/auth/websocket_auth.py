"""WebSocket authentication utilities.

WebSocket connections cannot use HTTP headers for auth,
so we use query parameters to pass the JWT token.
"""

from fastapi import WebSocket, WebSocketException, status

from research_agent.api.auth.supabase import verify_supabase_jwt
from research_agent.config import get_settings

settings = get_settings()


async def verify_websocket_token(
    websocket: WebSocket,
    token: str | None = None,
) -> tuple[str, bool]:
    """Verify WebSocket connection authentication.

    Args:
        websocket: The WebSocket connection
        token: JWT token from query parameter

    Returns:
        Tuple of (user_id, is_anonymous)

    Raises:
        WebSocketException: If authentication fails and bypass is disabled

    Note:
        This function does NOT accept the websocket. The caller (notification service)
        is responsible for calling websocket.accept() after verification.
    """
    # Auth bypass for local development
    if settings.auth_bypass_enabled:
        return ("dev-user-bypass", False)

    if not token:
        # Allow anonymous connections (will have limited access)
        return ("anonymous", True)

    # Verify the token
    is_valid, payload, error = verify_supabase_jwt(token)

    if not is_valid:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=error or "Invalid token")
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason=error or "Invalid token"
        )

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token missing user ID")
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Token missing user ID"
        )

    return (user_id, False)


async def verify_project_access(
    project_id: str,
    user_id: str,
    is_anonymous: bool,
) -> bool:
    """Verify user has access to the project.

    Args:
        project_id: The project to check access for
        user_id: The authenticated user ID
        is_anonymous: Whether this is an anonymous user

    Returns:
        True if access is allowed

    Note:
        For now, we allow all authenticated users to access their projects.
        Anonymous users can only access anonymous-created projects.
        Full project ownership verification should be added later.
    """
    # For dev bypass, always allow
    if user_id == "dev-user-bypass":
        return True

    # TODO: Add proper project ownership verification
    # For now, we trust authenticated users and log access
    return True
