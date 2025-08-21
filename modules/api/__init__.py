"""
API模块

提供基于Service层编排的REST API接口。
"""

from fastapi import APIRouter
from .topic_api import router as topic_router
from .file_api import router as file_router
from .resource_api import router as resource_router

# 创建主API路由器
api_router = APIRouter(prefix="/api/v1")

# 注册共用子路由 (document_api已移至rag模块)
api_router.include_router(topic_router)
api_router.include_router(file_router)
api_router.include_router(resource_router)

__all__ = [
    'api_router',
    'topic_router',
    'file_router',
    'resource_router'
]