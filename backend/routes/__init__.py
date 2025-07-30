"""
Routes package.

Contains FastAPI route handlers (thin delegation layer to controllers).
"""

from .cronjob_routes import router as cronjob_router
from .research_routes import router as research_router

__all__ = [
    "cronjob_router",
    "research_router"
]