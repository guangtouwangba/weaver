"""
Chat API controller.

Handles HTTP requests for chat operations.
"""

from fastapi import APIRouter, Depends

from ...shared.di.container import Container


class ChatController:
    """Controller for chat-related API endpoints."""
    
    def __init__(self, container: Container):
        self.container = container
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.router.get("/")
        async def list_chat_sessions():
            """List chat sessions."""
            return {"message": "Chat sessions endpoint - TODO: implement"}
        
        @self.router.post("/")
        async def start_chat_session():
            """Start a new chat session."""
            return {"message": "Start chat session - TODO: implement"}