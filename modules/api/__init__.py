"""
API模块

提供基于Service层编排的REST API interface。
"""

from fastapi import APIRouter

from .document_api import router as document_router
from .file_api import router as file_router
from .resource_api import router as resource_router
from .topic_api import router as topic_router

# 创建主API route器
api_router = APIRouter(prefix="/api/v1")

# 注册共用子路由
api_router.include_router(topic_router)
api_router.include_router(file_router)
api_router.include_router(resource_router)
api_router.include_router(document_router)

__all__ = [
    "api_router",
    "topic_router",
    "file_router",
    "resource_router",
    "document_router",
]
