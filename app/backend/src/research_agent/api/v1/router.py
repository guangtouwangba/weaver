"""API v1 router aggregation."""

from fastapi import APIRouter

from research_agent.api.v1 import canvas, chat, curriculum, documents, projects, settings, websocket

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
api_router.include_router(websocket.router, tags=["websocket"])
