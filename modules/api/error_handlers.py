"""
API错误处理器

自定义错误处理器来处理各种API错误情况，包括Unicode解码错误。
"""

import logging
from typing import Any, Dict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

logger = logging.getLogger(__name__)

async def unicode_decode_error_handler(request: Request, exc: UnicodeDecodeError) -> JSONResponse:
    """处理Unicode解码错误"""
    logger.warning(f"Unicode decode error at {request.url}: {exc}")
    
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": "请求数据编码错误",
            "error": {
                "type": "EncodingError",
                "detail": "请求包含无法解码的字符数据，请检查文件编码或数据格式",
                "suggestion": "请确保上传的文件使用正确的编码格式，或使用正确的Content-Type头"
            }
        }
    )

async def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理Request validation错误，特别是multipart数据错误"""
    logger.warning(f"Request validation error at {request.url}: {exc}")
    
    # 检查是否是编码相关的错误
    error_details = []
    encoding_error = False
    
    for error in exc.errors():
        error_dict = {
            "field": error.get("loc", [])[-1] if error.get("loc") else "unknown",
            "type": error.get("type", "unknown"),
            "message": error.get("msg", "validation error")
        }
        
        # 检查是否是编码错误
        if ("decode" in str(error).lower() or 
            "encoding" in str(error).lower() or 
            "utf-8" in str(error).lower()):
            encoding_error = True
        
        error_details.append(error_dict)
    
    if encoding_error:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "请求数据编码错误",
                "error": {
                    "type": "RequestEncodingError",
                    "detail": "请求数据包含无法处理的字符编码",
                    "suggestion": "请检查请求的Content-Type是否正确，确保文件数据使用正确的编码格式",
                    "errors": error_details
                }
            }
        )
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "请求Parameter validation失败",
            "error": {
                "type": "ValidationError",
                "detail": "Request parameters不符合API要求",
                "errors": error_details
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理一般异常"""
    logger.error(f"Unhandled error at {request.url}: {type(exc).__name__}: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "error": {
                "type": type(exc).__name__,
                "detail": "服务器处理请求时发生错误，请稍后重试或联系技术支持"
            }
        }
    )

def safe_encode_errors(errors: Any) -> Any:
    """
    安全编码错误信息，避免Unicode解码错误
    """
    if isinstance(errors, bytes):
        try:
            return errors.decode('utf-8', errors='replace')
        except:
            return str(errors)
    elif isinstance(errors, list):
        return [safe_encode_errors(item) for item in errors]
    elif isinstance(errors, dict):
        return {key: safe_encode_errors(value) for key, value in errors.items()}
    else:
        return errors