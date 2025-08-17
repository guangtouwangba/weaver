"""
Authentication and Authorization utilities for file upload application.

This module provides JWT-based authentication, role-based access control,
and security validation for file operations.
"""

import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass
from enum import Enum

from ..domain.value_objects import AccessLevel


class UserRole(str, Enum):
    """User roles for authorization."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    SERVICE = "service"


class Permission(str, Enum):
    """System permissions."""
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_DELETE = "file:delete"
    FILE_ADMIN = "file:admin"
    USER_ADMIN = "user:admin"
    SYSTEM_ADMIN = "system:admin"


@dataclass
class UserContext:
    """User context for authorization decisions."""
    user_id: str
    username: str
    roles: Set[UserRole]
    groups: Set[str]
    permissions: Set[Permission]
    is_authenticated: bool = True
    is_active: bool = True
    last_login: Optional[datetime] = None
    session_id: Optional[str] = None
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return UserRole.ADMIN in self.roles
    
    @property
    def is_service_account(self) -> bool:
        """Check if this is a service account."""
        return UserRole.SERVICE in self.roles
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions or self.is_admin
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def can_access_file(self, file_owner_id: str, access_level: AccessLevel) -> bool:
        """Check if user can access a file based on ownership and access level."""
        # Owner always has access
        if self.user_id == file_owner_id:
            return True
        
        # Admin always has access
        if self.is_admin:
            return True
        
        # Public files are accessible to all authenticated users
        if access_level == AccessLevel.PUBLIC_READ:
            return self.is_authenticated
        
        # Authenticated level requires authentication
        if access_level == AccessLevel.AUTHENTICATED:
            return self.is_authenticated
        
        # Private and shared files require explicit permission
        return False
    
    def can_modify_file(self, file_owner_id: str) -> bool:
        """Check if user can modify a file."""
        return (
            self.user_id == file_owner_id or 
            self.is_admin or 
            self.has_permission(Permission.FILE_ADMIN)
        )
    
    def can_delete_file(self, file_owner_id: str) -> bool:
        """Check if user can delete a file."""
        return (
            self.user_id == file_owner_id or 
            self.is_admin or 
            self.has_permission(Permission.FILE_DELETE)
        )


class JWTTokenManager:
    """JWT token management for authentication."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def create_access_token(
        self, 
        user_context: UserContext,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_context.user_id,
            "username": user_context.username,
            "roles": [role.value for role in user_context.roles],
            "groups": list(user_context.groups),
            "permissions": [perm.value for perm in user_context.permissions],
            "session_id": user_context.session_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a JWT refresh token."""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)  # Unique token ID
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    def extract_user_context(self, token: str) -> UserContext:
        """Extract user context from a JWT token."""
        payload = self.verify_token(token)
        
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        
        return UserContext(
            user_id=payload["sub"],
            username=payload.get("username", ""),
            roles={UserRole(role) for role in payload.get("roles", [])},
            groups=set(payload.get("groups", [])),
            permissions={Permission(perm) for perm in payload.get("permissions", [])},
            session_id=payload.get("session_id")
        )
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Create a new access token from a refresh token."""
        payload = self.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type for refresh")
        
        user_id = payload["sub"]
        # In a real implementation, you would fetch user data from database
        # For now, create a basic user context
        user_context = UserContext(
            user_id=user_id,
            username="", # Would be fetched from database
            roles={UserRole.USER},
            groups=set(),
            permissions=set()
        )
        
        return self.create_access_token(user_context)


class SecurityValidator:
    """Security validation utilities."""
    
    ALLOWED_FILE_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.txt', '.rtf',
        '.jpg', '.jpeg', '.png', '.gif', '.svg',
        '.mp3', '.mp4', '.avi', '.wav',
        '.zip', '.tar', '.gz',
        '.json', '.xml', '.csv'
    }
    
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.scr', '.pif',
        '.js', '.vbs', '.com', '.msi', '.jar'
    }
    
    MAX_FILENAME_LENGTH = 255
    MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
    
    @classmethod
    def validate_filename(cls, filename: str) -> bool:
        """Validate filename for security."""
        if not filename or len(filename) > cls.MAX_FILENAME_LENGTH:
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        if any(char in filename for char in dangerous_chars):
            return False
        
        # Check for path traversal attempts
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            return False
        
        # Check for dangerous extensions
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if f'.{file_ext}' in cls.DANGEROUS_EXTENSIONS:
            return False
        
        return True
    
    @classmethod
    def validate_file_size(cls, file_size: int) -> bool:
        """Validate file size."""
        return 0 < file_size <= cls.MAX_FILE_SIZE
    
    @classmethod
    def validate_content_type(cls, content_type: str) -> bool:
        """Validate content type."""
        if not content_type:
            return False
        
        # Block potentially dangerous content types
        dangerous_types = [
            'application/x-executable',
            'application/x-msdownload',
            'application/x-msdos-program',
            'text/javascript',
            'application/javascript'
        ]
        
        return content_type not in dangerous_types
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename by removing dangerous characters."""
        # Remove dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        sanitized = filename
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove path components
        sanitized = sanitized.replace('..', '').replace('/', '_').replace('\\', '_')
        
        # Truncate if too long
        if len(sanitized) > cls.MAX_FILENAME_LENGTH:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            max_name_length = cls.MAX_FILENAME_LENGTH - len(ext) - 1
            sanitized = f"{name[:max_name_length]}.{ext}" if ext else name[:cls.MAX_FILENAME_LENGTH]
        
        return sanitized
    
    @classmethod
    def generate_file_hash(cls, content: bytes) -> str:
        """Generate SHA256 hash of file content."""
        return hashlib.sha256(content).hexdigest()
    
    @classmethod
    def validate_file_hash(cls, content: bytes, expected_hash: str) -> bool:
        """Validate file content against expected hash."""
        actual_hash = cls.generate_file_hash(content)
        return actual_hash == expected_hash


class RateLimiter:
    """Rate limiting for API endpoints."""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self._in_memory_store = {}  # Fallback for when Redis is not available
    
    async def is_allowed(
        self, 
        identifier: str, 
        limit: int, 
        window_seconds: int
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed under rate limit.
        
        Returns (is_allowed, metadata)
        """
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=window_seconds)
        
        if self.redis_client:
            return await self._redis_rate_limit(identifier, limit, window_seconds, current_time)
        else:
            return self._memory_rate_limit(identifier, limit, window_start, current_time)
    
    async def _redis_rate_limit(
        self, 
        identifier: str, 
        limit: int, 
        window_seconds: int, 
        current_time: datetime
    ) -> tuple[bool, Dict[str, Any]]:
        """Redis-based rate limiting."""
        # This would implement Redis sliding window rate limiting
        # For now, return a placeholder
        return True, {"remaining": limit, "reset_time": current_time.timestamp() + window_seconds}
    
    def _memory_rate_limit(
        self, 
        identifier: str, 
        limit: int, 
        window_start: datetime, 
        current_time: datetime
    ) -> tuple[bool, Dict[str, Any]]:
        """In-memory rate limiting (for testing/development)."""
        if identifier not in self._in_memory_store:
            self._in_memory_store[identifier] = []
        
        # Clean old requests
        self._in_memory_store[identifier] = [
            req_time for req_time in self._in_memory_store[identifier]
            if req_time > window_start
        ]
        
        # Check limit
        current_count = len(self._in_memory_store[identifier])
        if current_count >= limit:
            return False, {
                "remaining": 0,
                "reset_time": (current_time + timedelta(seconds=60)).timestamp()
            }
        
        # Record this request
        self._in_memory_store[identifier].append(current_time)
        
        return True, {
            "remaining": limit - current_count - 1,
            "reset_time": (current_time + timedelta(seconds=60)).timestamp()
        }


class APIKeyManager:
    """API key management for service-to-service authentication."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_api_key(self, service_name: str, expires_at: Optional[datetime] = None) -> str:
        """Generate an API key for a service."""
        key_data = {
            "service": service_name,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "random": secrets.token_urlsafe(32)
        }
        
        # Create a signed API key
        token = jwt.encode(key_data, self.secret_key, algorithm="HS256")
        return f"fileapi_{token}"
    
    def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Validate an API key."""
        if not api_key.startswith("fileapi_"):
            raise ValueError("Invalid API key format")
        
        token = api_key[8:]  # Remove "fileapi_" prefix
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Check expiration
            if payload.get("expires_at"):
                expires_at = datetime.fromisoformat(payload["expires_at"])
                if datetime.utcnow() > expires_at:
                    raise ValueError("API key has expired")
            
            return payload
            
        except jwt.InvalidTokenError:
            raise ValueError("Invalid API key")