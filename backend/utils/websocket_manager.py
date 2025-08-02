"""
WebSocket Manager for Real-time Log Streaming
"""
import asyncio
import json
import logging
from typing import Dict, Set, List, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from models.schemas.job_log import WebSocketMessage, WebSocketSubscription, LogSearchFilters
from services.job_log_service import JobLogService
from core.dependencies import get_db_session

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time log streaming"""
    
    def __init__(self):
        # Active connections: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Subscriptions: {connection_id: WebSocketSubscription}
        self.subscriptions: Dict[str, WebSocketSubscription] = {}
        
        # Job run subscribers: {job_run_id: Set[connection_id]}
        self.job_run_subscribers: Dict[str, Set[str]] = {}
        
        # Job subscribers: {job_id: Set[connection_id]}
        self.job_subscribers: Dict[str, Set[str]] = {}
        
        # Background task for polling logs
        self._polling_task: Optional[asyncio.Task] = None
        self._stop_polling = False
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connection {connection_id} established")
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if connection_id in self.subscriptions:
            subscription = self.subscriptions[connection_id]
            # Remove from job run subscribers
            if subscription.job_run_id in self.job_run_subscribers:
                self.job_run_subscribers[subscription.job_run_id].discard(connection_id)
                if not self.job_run_subscribers[subscription.job_run_id]:
                    del self.job_run_subscribers[subscription.job_run_id]
            
            del self.subscriptions[connection_id]
        
        logger.info(f"WebSocket connection {connection_id} disconnected")
    
    async def subscribe(self, connection_id: str, subscription: WebSocketSubscription):
        """Subscribe a connection to job run logs"""
        if connection_id not in self.active_connections:
            raise ValueError(f"Connection {connection_id} not found")
        
        self.subscriptions[connection_id] = subscription
        
        # Add to job run subscribers
        if subscription.job_run_id not in self.job_run_subscribers:
            self.job_run_subscribers[subscription.job_run_id] = set()
        self.job_run_subscribers[subscription.job_run_id].add(connection_id)
        
        logger.info(f"Connection {connection_id} subscribed to job run {subscription.job_run_id}")
        
        # Start polling task if not already running
        if self._polling_task is None or self._polling_task.done():
            self._polling_task = asyncio.create_task(self._poll_logs())
    
    async def send_message(self, connection_id: str, message: WebSocketMessage):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message.dict(), default=str))
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast_to_job_run(self, job_run_id: str, message: WebSocketMessage):
        """Broadcast a message to all subscribers of a job run"""
        if job_run_id in self.job_run_subscribers:
            subscribers = self.job_run_subscribers[job_run_id].copy()
            for connection_id in subscribers:
                await self.send_message(connection_id, message)
    
    async def _poll_logs(self):
        """Background task to poll for new logs and broadcast to subscribers"""
        last_check = {}  # {job_run_id: last_timestamp}
        
        while not self._stop_polling and self.active_connections:
            try:
                # Get database session
                db_session = next(get_db_session())
                job_log_service = JobLogService(db_session)
                
                # Check each subscribed job run
                for job_run_id in list(self.job_run_subscribers.keys()):
                    try:
                        # Get last check time for this job run
                        since_time = last_check.get(job_run_id)
                        
                        # Search for new logs
                        filters = LogSearchFilters(
                            job_run_id=job_run_id,
                            start_time=since_time
                        )
                        
                        result = job_log_service.search_logs_elasticsearch(
                            filters=filters,
                            skip=0,
                            limit=100,
                            sort_by="timestamp",
                            sort_order="asc"
                        )
                        
                        # Broadcast new logs
                        for log in result.logs:
                            # Check subscription filters
                            subscribers = self.job_run_subscribers.get(job_run_id, set()).copy()
                            for connection_id in subscribers:
                                subscription = self.subscriptions.get(connection_id)
                                if subscription and self._matches_subscription(log.dict(), subscription):
                                    message = WebSocketMessage(
                                        type="log",
                                        job_run_id=job_run_id,
                                        timestamp=datetime.now(),
                                        data=log.dict()
                                    )
                                    await self.send_message(connection_id, message)
                        
                        # Update last check time
                        if result.logs:
                            last_check[job_run_id] = max(log.timestamp for log in result.logs)
                        elif job_run_id not in last_check:
                            last_check[job_run_id] = datetime.now()
                    
                    except Exception as e:
                        logger.error(f"Error polling logs for job run {job_run_id}: {e}")
                
                # Clean up last_check for unsubscribed job runs
                active_job_runs = set(self.job_run_subscribers.keys())
                for job_run_id in list(last_check.keys()):
                    if job_run_id not in active_job_runs:
                        del last_check[job_run_id]
                
                db_session.close()
                
            except Exception as e:
                logger.error(f"Error in log polling task: {e}")
            
            # Wait before next poll
            await asyncio.sleep(1)
        
        logger.info("Log polling task stopped")
    
    def _matches_subscription(self, log_data: Dict[str, Any], subscription: WebSocketSubscription) -> bool:
        """Check if a log matches subscription filters"""
        if not subscription.filters:
            return True
        
        filters = subscription.filters
        
        # Check level filter
        if filters.level and log_data.get("level") != filters.level.value:
            return False
        
        # Check step filter
        if filters.step and log_data.get("step") != filters.step:
            return False
        
        # Check paper ID filter
        if filters.paper_id and log_data.get("paper_id") != filters.paper_id:
            return False
        
        # Check error code filter
        if filters.error_code and log_data.get("error_code") != filters.error_code:
            return False
        
        # Check text search
        if filters.search:
            message = log_data.get("message", "").lower()
            if filters.search.lower() not in message:
                return False
        
        return True
    
    async def stop(self):
        """Stop the connection manager and close all connections"""
        self._stop_polling = True
        
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for connection_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket {connection_id}: {e}")
        
        self.active_connections.clear()
        self.subscriptions.clear()
        self.job_run_subscribers.clear()
        self.job_subscribers.clear()

# Global connection manager instance
connection_manager = ConnectionManager()

class LogStreamingService:
    """Service for managing real-time log streaming"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def handle_websocket_connection(self, websocket: WebSocket, job_run_id: str):
        """Handle a new WebSocket connection for log streaming"""
        connection_id = f"{job_run_id}_{datetime.now().timestamp()}"
        
        try:
            await self.connection_manager.connect(websocket, connection_id)
            
            # Send initial connection success message
            welcome_message = WebSocketMessage(
                type="connected",
                job_run_id=job_run_id,
                timestamp=datetime.now(),
                data={"message": "Connected to log stream", "connection_id": connection_id}
            )
            await self.connection_manager.send_message(connection_id, welcome_message)
            
            # Handle incoming messages
            while True:
                try:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    if message_data.get("type") == "subscribe":
                        # Handle subscription
                        subscription = WebSocketSubscription(
                            job_run_id=job_run_id,
                            types=message_data.get("types", ["log", "status", "metric"]),
                            filters=LogSearchFilters(**message_data.get("filters", {})) if message_data.get("filters") else None
                        )
                        await self.connection_manager.subscribe(connection_id, subscription)
                        
                        # Send subscription confirmation
                        confirm_message = WebSocketMessage(
                            type="subscribed",
                            job_run_id=job_run_id,
                            timestamp=datetime.now(),
                            data={"subscription": subscription.dict()}
                        )
                        await self.connection_manager.send_message(connection_id, confirm_message)
                    
                    elif message_data.get("type") == "ping":
                        # Handle ping/pong for connection health
                        pong_message = WebSocketMessage(
                            type="pong",
                            job_run_id=job_run_id,
                            timestamp=datetime.now(),
                            data={"message": "pong"}
                        )
                        await self.connection_manager.send_message(connection_id, pong_message)
                
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    error_message = WebSocketMessage(
                        type="error",
                        job_run_id=job_run_id,
                        timestamp=datetime.now(),
                        data={"error": "Invalid JSON message"}
                    )
                    await self.connection_manager.send_message(connection_id, error_message)
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    error_message = WebSocketMessage(
                        type="error",
                        job_run_id=job_run_id,
                        timestamp=datetime.now(),
                        data={"error": str(e)}
                    )
                    await self.connection_manager.send_message(connection_id, error_message)
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.connection_manager.disconnect(connection_id)

# Global service instance
log_streaming_service = LogStreamingService(connection_manager)