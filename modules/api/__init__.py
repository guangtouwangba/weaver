"""
API模块

提供基于Service层编排的REST API接口。
"""

from fastapi import APIRouter
from .topic_api import router as topic_router
from .file_api import router as file_router
from .document_api import router as document_router
from .resource_api import router as resource_router

# 创建主API路由器
api_router = APIRouter(prefix="/api/v1")

# 注册各个子路由
api_router.include_router(topic_router)
api_router.include_router(file_router)
api_router.include_router(document_router)
api_router.include_router(resource_router)

__all__ = [
    'api_router',
    'topic_router',
    'file_router', 
    'document_router',
    'resource_router'
]