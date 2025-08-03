"""
Analysis WebSocket Manager for Real-time Analysis Progress
"""
import asyncio
import json
import logging
import uuid
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class AnalysisProgressMessage(BaseModel):
    """Message for analysis progress updates"""
    type: str  # "progress", "papers", "agent_insight", "completed", "error"
    analysis_id: str
    timestamp: datetime
    data: Dict[str, Any]

class AnalysisSubscription(BaseModel):
    """Subscription to analysis progress"""
    analysis_id: str
    connection_id: str
    subscribed_at: datetime

class AnalysisConnectionManager:
    """Manages WebSocket connections for real-time analysis progress"""
    
    def __init__(self):
        # Active connections: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Analysis subscribers: {analysis_id: Set[connection_id]}
        self.analysis_subscribers: Dict[str, Set[str]] = {}
        
        # Connection to analysis mapping: {connection_id: analysis_id}
        self.connection_analysis: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, analysis_id: str) -> str:
        """Accept a new WebSocket connection for analysis tracking"""
        connection_id = f"analysis_{analysis_id}_{uuid.uuid4().hex[:8]}"
        
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_analysis[connection_id] = analysis_id
        
        # Add to analysis subscribers
        if analysis_id not in self.analysis_subscribers:
            self.analysis_subscribers[analysis_id] = set()
        self.analysis_subscribers[analysis_id].add(connection_id)
        
        logger.info(f"Analysis WebSocket connection {connection_id} established for analysis {analysis_id}")
        
        # Send welcome message
        welcome_message = AnalysisProgressMessage(
            type="connected",
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            data={"message": "Connected to analysis progress stream", "connection_id": connection_id}
        )
        await self.send_message(connection_id, welcome_message)
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from analysis subscribers
        if connection_id in self.connection_analysis:
            analysis_id = self.connection_analysis[connection_id]
            if analysis_id in self.analysis_subscribers:
                self.analysis_subscribers[analysis_id].discard(connection_id)
                if not self.analysis_subscribers[analysis_id]:
                    del self.analysis_subscribers[analysis_id]
            del self.connection_analysis[connection_id]
        
        logger.info(f"Analysis WebSocket connection {connection_id} disconnected")
    
    async def send_message(self, connection_id: str, message: AnalysisProgressMessage):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message.dict(), default=str))
            except Exception as e:
                logger.error(f"Failed to send analysis message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast_to_analysis(self, analysis_id: str, message: AnalysisProgressMessage):
        """Broadcast a message to all subscribers of an analysis"""
        if analysis_id in self.analysis_subscribers:
            subscribers = self.analysis_subscribers[analysis_id].copy()
            for connection_id in subscribers:
                await self.send_message(connection_id, message)
    
    async def send_progress_update(self, analysis_id: str, step: str, progress: int, 
                                 current_papers: Optional[list] = None, agent_insights: Optional[dict] = None):
        """Send a progress update to all subscribers of an analysis"""
        message = AnalysisProgressMessage(
            type="progress",
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            data={
                "step": step,
                "progress": progress,
                "current_papers": current_papers or [],
                "agent_insights": agent_insights or {}
            }
        )
        await self.broadcast_to_analysis(analysis_id, message)
    
    async def send_papers_found(self, analysis_id: str, papers: list):
        """Send papers found update"""
        message = AnalysisProgressMessage(
            type="papers",
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            data={"papers": papers}
        )
        await self.broadcast_to_analysis(analysis_id, message)
    
    async def send_agent_insight(self, analysis_id: str, agent_name: str, insight: str):
        """Send agent insight update"""
        message = AnalysisProgressMessage(
            type="agent_insight",
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            data={"agent_name": agent_name, "insight": insight}
        )
        await self.broadcast_to_analysis(analysis_id, message)
    
    async def send_analysis_completed(self, analysis_id: str, final_results: dict):
        """Send analysis completion message"""
        message = AnalysisProgressMessage(
            type="completed",
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            data=final_results
        )
        await self.broadcast_to_analysis(analysis_id, message)
    
    async def send_error(self, analysis_id: str, error_message: str):
        """Send error message"""
        message = AnalysisProgressMessage(
            type="error",
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            data={"error": error_message}
        )
        await self.broadcast_to_analysis(analysis_id, message)
    
    def get_subscriber_count(self, analysis_id: str) -> int:
        """Get number of subscribers for an analysis"""
        return len(self.analysis_subscribers.get(analysis_id, set()))
    
    async def handle_websocket_connection(self, websocket: WebSocket, analysis_id: str):
        """Handle a new WebSocket connection for analysis tracking"""
        connection_id = None
        try:
            connection_id = await self.connect(websocket, analysis_id)
            
            # Handle incoming messages (mainly for ping/pong)
            while True:
                try:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    if message_data.get("type") == "ping":
                        # Handle ping/pong for connection health
                        pong_message = AnalysisProgressMessage(
                            type="pong",
                            analysis_id=analysis_id,
                            timestamp=datetime.now(),
                            data={"message": "pong"}
                        )
                        await self.send_message(connection_id, pong_message)
                
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    error_message = AnalysisProgressMessage(
                        type="error",
                        analysis_id=analysis_id,
                        timestamp=datetime.now(),
                        data={"error": "Invalid JSON message"}
                    )
                    await self.send_message(connection_id, error_message)
                except Exception as e:
                    logger.error(f"Error handling analysis WebSocket message: {e}")
        
        except WebSocketDisconnect:
            logger.info(f"Analysis WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"Analysis WebSocket error: {e}")
        finally:
            if connection_id:
                self.disconnect(connection_id)

# Global analysis connection manager instance
analysis_connection_manager = AnalysisConnectionManager()