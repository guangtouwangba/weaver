"""API v1 router aggregation."""

from fastapi import APIRouter

from research_agent.api.v1 import (
    canvas,
    chat,
    curriculum,
    documents,
    maintenance,
    projects,
    settings,
    thinking_path,
)

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(canvas.router, tags=["canvas"])
api_router.include_router(
    curriculum.router, prefix="/projects/{project_id}/curriculum", tags=["curriculum"]
)
api_router.include_router(settings.router, tags=["settings"])
api_router.include_router(thinking_path.router, tags=["thinking-path"])
api_router.include_router(maintenance.router, tags=["maintenance"])
# Note: websocket router is mounted at root level in main.py (not under /api/v1)
