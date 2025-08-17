"""
Security middleware for file upload application.

This module provides FastAPI middleware for authentication, authorization,
rate limiting, and security headers.
"""

import logging
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
from fastapi import HTTPException, Request, Response, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .auth import (
    UserContext, JWTTokenManager, RateLimiter, APIKeyManager,
    SecurityValidator, UserRole, Permission
)

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration for the file upload application."""
    
    def __init__(
        self,
        jwt_secret_key: str,
        api_key_secret: str,
        enable_rate_limiting: bool = True,
        enable_cors: bool = True,
        max_upload_rate_per_minute: int = 10,
        max_download_rate_per_minute: int = 60,
        require_https: bool = True
    ):
        self.jwt_secret_key = jwt_secret_key
        self.api_key_secret = api_key_secret
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_cors = enable_cors
        self.max_upload_rate_per_minute = max_upload_rate_per_minute
        self.max_download_rate_per_minute = max_download_rate_per_minute
        self.require_https = require_https
        
        # Initialize managers
        self.jwt_manager = JWTTokenManager(jwt_secret_key)
        self.api_key_manager = APIKeyManager(api_key_secret)
        self.rate_limiter = RateLimiter()


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware for file upload API.
    
    Features:
    - HTTPS enforcement
    - Security headers
    - Request logging
    - Rate limiting
    - Input validation
    """
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security middleware."""
        start_time = datetime.utcnow()
        
        # Skip middleware for health check
        if request.url.path.endswith("/health"):
            return await call_next(request)
        
        try:
            # 1. HTTPS enforcement
            if self.config.require_https and request.headers.get("x-forwarded-proto") != "https":
                if not request.url.scheme == "https":
                    return JSONResponse(
                        status_code=400,
                        content={"error": "HTTPS required"}
                    )
            
            # 2. Rate limiting
            if self.config.enable_rate_limiting:
                rate_limit_result = await self._check_rate_limit(request)
                if not rate_limit_result["allowed"]:
                    return JSONResponse(
                        status_code=429,
                        content={"error": "Rate limit exceeded"},
                        headers={
                            "X-RateLimit-Remaining": str(rate_limit_result["remaining"]),
                            "X-RateLimit-Reset": str(rate_limit_result["reset_time"]),
                            "Retry-After": "60"
                        }
                    )
            
            # 3. Input validation for file operations
            await self._validate_request(request)
            
            # 4. Process request
            response = await call_next(request)
            
            # 5. Add security headers
            self._add_security_headers(response)
            
            # 6. Log request
            await self._log_request(request, response, start_time)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal security error"}
            )
    
    async def _check_rate_limit(self, request: Request) -> Dict[str, Any]:
        """Check rate limiting for the request."""
        # Determine rate limit based on endpoint
        path = request.url.path
        if "/upload" in path:
            limit = self.config.max_upload_rate_per_minute
        elif "/download" in path:
            limit = self.config.max_download_rate_per_minute
        else:
            limit = 100  # General API limit
        
        # Use IP address as identifier (in production, use user ID if available)
        client_ip = request.client.host
        identifier = f"ip:{client_ip}"
        
        is_allowed, metadata = await self.config.rate_limiter.is_allowed(
            identifier, limit, 60  # 60 seconds window
        )
        
        return {
            "allowed": is_allowed,
            "remaining": metadata.get("remaining", 0),
            "reset_time": metadata.get("reset_time", 0)
        }
    
    async def _validate_request(self, request: Request) -> None:
        """Validate request for security issues."""
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > SecurityValidator.MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Request entity too large"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid content-length header"
                )
        
        # Validate content type for file uploads
        if request.method == "POST" and "/upload" in request.url.path:
            content_type = request.headers.get("content-type", "")
            if not SecurityValidator.validate_content_type(content_type):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid content type"
                )
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
            "X-File-Upload-API": "v1.0"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
    
    async def _log_request(
        self, 
        request: Request, 
        response: Response, 
        start_time: datetime
    ) -> None:
        """Log request for security monitoring."""
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        log_data = {
            "timestamp": start_time.isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "status_code": response.status_code,
            "duration_seconds": duration,
            "content_length": response.headers.get("content-length")
        }
        
        # Log as info for successful requests, warning for client errors, error for server errors
        if response.status_code < 400:
            logger.info(f"Request processed: {log_data}")
        elif response.status_code < 500:
            logger.warning(f"Client error: {log_data}")
        else:
            logger.error(f"Server error: {log_data}")


# FastAPI Dependencies for Authentication

security_scheme = HTTPBearer(auto_error=False)

async def get_security_config() -> SecurityConfig:
    """Get security configuration."""
    # In production, this would load from environment variables or config file
    return SecurityConfig(
        jwt_secret_key="your-secret-key-here",  # Use environment variable
        api_key_secret="your-api-key-secret",   # Use environment variable
        enable_rate_limiting=True,
        require_https=False  # Set to True in production
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    config: SecurityConfig = Depends(get_security_config)
) -> Optional[UserContext]:
    """Get current user context if authenticated, None otherwise."""
    if not credentials:
        return None
    
    try:
        # Try JWT token first
        if credentials.scheme.lower() == "bearer":
            user_context = config.jwt_manager.extract_user_context(credentials.credentials)
            return user_context
    except ValueError:
        # Try API key
        try:
            api_key_data = config.api_key_manager.validate_api_key(credentials.credentials)
            # Create service account context
            return UserContext(
                user_id=f"service:{api_key_data['service']}",
                username=api_key_data['service'],
                roles={UserRole.SERVICE},
                groups={"services"},
                permissions={Permission.FILE_READ, Permission.FILE_WRITE}
            )
        except ValueError:
            pass
    
    return None


async def get_current_user(
    user_context: Optional[UserContext] = Depends(get_current_user_optional)
) -> UserContext:
    """Get current authenticated user context (required)."""
    if not user_context:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user_context.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )
    
    return user_context


async def require_admin(
    user_context: UserContext = Depends(get_current_user)
) -> UserContext:
    """Require admin privileges."""
    if not user_context.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    
    return user_context


async def require_permission(permission: Permission):
    """Create a dependency that requires a specific permission."""
    async def _check_permission(
        user_context: UserContext = Depends(get_current_user)
    ) -> UserContext:
        if not user_context.has_permission(permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission {permission.value} required"
            )
        return user_context
    
    return _check_permission


class FileAccessValidator:
    """Validator for file access permissions."""
    
    @staticmethod
    async def validate_file_access(
        file_id: str,
        user_context: Optional[UserContext],
        required_permission: str = "read"
    ) -> bool:
        """
        Validate if user can access a file.
        
        This would typically query the database to check file ownership
        and access permissions. For now, we'll implement basic logic.
        """
        if not user_context:
            # Only public files can be accessed without authentication
            # This would check the file's access level in the database
            return False  # Placeholder
        
        # Admin users can access everything
        if user_context.is_admin:
            return True
        
        # Service accounts have broad access
        if user_context.is_service_account:
            return True
        
        # File owners can access their files
        # This would check file ownership in the database
        # For now, we'll allow access
        return True
    
    @staticmethod
    async def validate_file_modification(
        file_id: str,
        user_context: UserContext
    ) -> bool:
        """Validate if user can modify a file."""
        if not user_context:
            return False
        
        # Admin users can modify everything
        if user_context.is_admin:
            return True
        
        # This would check file ownership in the database
        # For now, we'll allow modification for authenticated users
        return True


def create_file_access_dependency(required_permission: str = "read"):
    """Create a dependency that validates file access."""
    async def _validate_file_access(
        file_id: str,
        user_context: Optional[UserContext] = Depends(get_current_user_optional)
    ) -> UserContext:
        has_access = await FileAccessValidator.validate_file_access(
            file_id, user_context, required_permission
        )
        
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="Access denied to file"
            )
        
        return user_context
    
    return _validate_file_access


# Utility functions for security

def validate_upload_request(filename: str, content_type: str, file_size: int) -> None:
    """Validate file upload request for security."""
    if not SecurityValidator.validate_filename(filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename"
        )
    
    if not SecurityValidator.validate_content_type(content_type):
        raise HTTPException(
            status_code=400,
            detail="Content type not allowed"
        )
    
    if not SecurityValidator.validate_file_size(file_size):
        raise HTTPException(
            status_code=400,
            detail="File size exceeds maximum allowed"
        )


def sanitize_user_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize user input data."""
    sanitized = {}
    
    for key, value in input_data.items():
        if isinstance(value, str):
            # Basic XSS prevention
            sanitized[key] = value.replace("<", "&lt;").replace(">", "&gt;")
        elif isinstance(value, list):
            sanitized[key] = [
                item.replace("<", "&lt;").replace(">", "&gt;") 
                if isinstance(item, str) else item 
                for item in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized