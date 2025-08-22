"""
API module

Provides REST API interface based on Service layer orchestration.
"""

from fastapi import APIRouter

from .file_api import router as file_router
from .resource_api import router as resource_router
from .topic_api import router as topic_router

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Register shared sub-routes (document_api moved to rag module)
api_router.include_router(topic_router)
api_router.include_router(file_router)
api_router.include_router(resource_router)

__all__ = ["api_router", "topic_router", "file_router", "resource_router"]
