"""API v1 router aggregation."""

from fastapi import APIRouter

from research_agent.api.v1 import (
    api_keys,
    canvas,
    chat,
    documents,
    inbox,
    maintenance,
    outputs,
    projects,
    settings,
    tags,
    verify_relation,
)

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(canvas.router, tags=["canvas"])
api_router.include_router(outputs.router, tags=["outputs"])
api_router.include_router(settings.router, tags=["settings"])
api_router.include_router(maintenance.router, tags=["maintenance"])

# New Inbox Routers
api_router.include_router(inbox.router, prefix="/inbox", tags=["inbox"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(api_keys.router, prefix="/settings/api-keys", tags=["api-keys"])
# Note: websocket router is mounted at root level in main.py (not under /api/v1)
