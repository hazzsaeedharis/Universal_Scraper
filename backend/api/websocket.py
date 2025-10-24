"""
WebSocket manager for real-time updates.
"""
from typing import Dict, Set
from fastapi import WebSocket
import json
import asyncio

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ConnectionManager:
    """WebSocket connection manager."""
    
    def __init__(self):
        """Initialize the connection manager."""
        # Map job_id to set of connected websockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, job_id: int):
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            job_id: Job ID to subscribe to
        """
        await websocket.accept()
        
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        
        self.active_connections[job_id].add(websocket)
        logger.info(f"WebSocket connected for job {job_id}")
    
    def disconnect(self, websocket: WebSocket, job_id: int):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            job_id: Job ID
        """
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        
        logger.info(f"WebSocket disconnected for job {job_id}")
    
    async def send_update(self, job_id: int, message: dict):
        """
        Send update to all connections for a job.
        
        Args:
            job_id: Job ID
            message: Message dictionary to send
        """
        if job_id not in self.active_connections:
            return
        
        # Convert to JSON
        json_message = json.dumps(message)
        
        # Send to all connected clients
        disconnected = set()
        for connection in self.active_connections[job_id]:
            try:
                await connection.send_text(json_message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, job_id)
    
    async def broadcast_progress(
        self,
        job_id: int,
        status: str,
        urls_discovered: int,
        urls_scraped: int,
        urls_failed: int,
        current_url: str = None
    ):
        """
        Broadcast progress update.
        
        Args:
            job_id: Job ID
            status: Job status
            urls_discovered: URLs discovered
            urls_scraped: URLs scraped
            urls_failed: URLs failed
            current_url: Currently processing URL
        """
        message = {
            "type": "progress",
            "job_id": job_id,
            "status": status,
            "urls_discovered": urls_discovered,
            "urls_scraped": urls_scraped,
            "urls_failed": urls_failed,
            "current_url": current_url
        }
        
        await self.send_update(job_id, message)
    
    async def broadcast_completion(
        self,
        job_id: int,
        status: str,
        message: str,
        stats: dict = None
    ):
        """
        Broadcast job completion.
        
        Args:
            job_id: Job ID
            status: Final status
            message: Completion message
            stats: Optional statistics
        """
        update = {
            "type": "completion",
            "job_id": job_id,
            "status": status,
            "message": message
        }
        
        if stats:
            update["stats"] = stats
        
        await self.send_update(job_id, update)


# Global connection manager
manager = ConnectionManager()

