"""API v1 router aggregation."""

from fastapi import APIRouter

from research_agent.api.v1 import canvas, chat, documents, projects

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(canvas.router, tags=["canvas"])

