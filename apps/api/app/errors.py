"""Unified error handling and response formatting."""

from typing import Any, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    success: bool = False
    error: ErrorDetail
    request_id: Optional[str] = None


# Error codes and their user-friendly messages
ERROR_MESSAGES = {
    # Document errors
    "DOCUMENT_NOT_FOUND": "找不到指定的文档",
    "DOCUMENT_UPLOAD_FAILED": "文档上传失败",
    "DOCUMENT_PROCESSING_FAILED": "文档处理失败，请检查文件格式",
    "VECTOR_STORE_EMPTY": "向量库为空，请先上传并处理文档",
    
    # Topic errors
    "TOPIC_NOT_FOUND": "找不到指定的主题",
    "TOPIC_CREATION_FAILED": "创建主题失败",
    
    # Conversation errors
    "CONVERSATION_NOT_FOUND": "找不到指定的对话",
    "CONVERSATION_CREATION_FAILED": "创建对话失败，请确保主题存在",
    "MESSAGE_CREATION_FAILED": "保存消息失败",
    
    # Validation errors
    "INVALID_INPUT": "输入数据格式不正确",
    "MISSING_REQUIRED_FIELD": "缺少必填字段",
    "INVALID_FILE_TYPE": "不支持的文件类型",
    "FILE_TOO_LARGE": "文件大小超过限制",
    
    # LLM errors
    "LLM_API_ERROR": "AI服务暂时不可用，请稍后重试",
    "LLM_TIMEOUT": "AI响应超时，请重试或简化问题",
    "LLM_RATE_LIMIT": "请求过于频繁，请稍后再试",
    
    # Database errors
    "DATABASE_ERROR": "数据库操作失败",
    "FOREIGN_KEY_VIOLATION": "相关数据不存在",
    "UNIQUE_CONSTRAINT_VIOLATION": "数据已存在",
    
    # General errors
    "INTERNAL_ERROR": "服务器内部错误",
    "SERVICE_UNAVAILABLE": "服务暂时不可用",
    "UNAUTHORIZED": "未授权访问",
    "FORBIDDEN": "没有权限执行此操作",
}


def get_user_friendly_message(code: str, default: str = "操作失败") -> str:
    """Get user-friendly error message for error code."""
    return ERROR_MESSAGES.get(code, default)


def create_error_response(
    code: str,
    message: Optional[str] = None,
    field: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> JSONResponse:
    """Create a standardized error response."""
    user_message = message or get_user_friendly_message(code)
    
    error_detail = ErrorDetail(
        code=code,
        message=user_message,
        field=field,
        details=details,
    )
    
    error_response = ErrorResponse(error=error_detail)
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(exclude_none=True),
    )


# Custom exceptions
class AppException(Exception):
    """Base exception for application errors."""
    
    def __init__(
        self,
        code: str,
        message: Optional[str] = None,
        field: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        self.code = code
        self.message = message or get_user_friendly_message(code)
        self.field = field
        self.details = details
        self.status_code = status_code
        super().__init__(self.message)


class DocumentNotFoundError(AppException):
    """Document not found exception."""
    
    def __init__(self, document_id: str):
        super().__init__(
            code="DOCUMENT_NOT_FOUND",
            details={"document_id": document_id},
            status_code=status.HTTP_404_NOT_FOUND,
        )


class TopicNotFoundError(AppException):
    """Topic not found exception."""
    
    def __init__(self, topic_id: str):
        super().__init__(
            code="TOPIC_NOT_FOUND",
            details={"topic_id": topic_id},
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConversationNotFoundError(AppException):
    """Conversation not found exception."""
    
    def __init__(self, conversation_id: str):
        super().__init__(
            code="CONVERSATION_NOT_FOUND",
            details={"conversation_id": conversation_id},
            status_code=status.HTTP_404_NOT_FOUND,
        )


class VectorStoreEmptyError(AppException):
    """Vector store is empty exception."""
    
    def __init__(self):
        super().__init__(
            code="VECTOR_STORE_EMPTY",
            status_code=status.HTTP_404_NOT_FOUND,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    return create_error_response(
        code=exc.code,
        message=exc.message,
        field=exc.field,
        details=exc.details,
        status_code=exc.status_code,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    # Map HTTP status codes to error codes
    code_mapping = {
        404: "RESOURCE_NOT_FOUND",
        400: "INVALID_INPUT",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    
    code = code_mapping.get(exc.status_code, "UNKNOWN_ERROR")
    message = str(exc.detail) if exc.detail else get_user_friendly_message(code)
    
    return create_error_response(
        code=code,
        message=message,
        status_code=exc.status_code,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    import traceback
    
    # Log the error for debugging
    print(f"❌ Unhandled exception: {exc}")
    print(traceback.format_exc())
    
    # Return user-friendly error
    return create_error_response(
        code="INTERNAL_ERROR",
        message="服务器处理请求时发生错误，我们正在调查此问题",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

