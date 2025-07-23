"""
WebSocket router for real-time communication
"""
import json
import logging
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from datetime import datetime, timezone

from ..services.auth_service import auth_service, UserContext

logger = logging.getLogger("ai-assistant-cli")

router = APIRouter(tags=["websocket"])

class ConnectionManager:
    """
    Manages WebSocket connections for real-time communication
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, str] = {}  # session_id -> connection_id
    
    async def connect(self, websocket: WebSocket, session_id: str) -> str:
        """
        Accept a new WebSocket connection and associate it with a session
        """
        await websocket.accept()
        connection_id = f"conn_{datetime.now(timezone.utc).timestamp()}"
        self.active_connections[connection_id] = websocket
        self.session_connections[session_id] = connection_id
        
        logger.info(f"WebSocket connection established: {connection_id} for session {session_id}")
        
        # Send welcome message
        await self.send_message(connection_id, {
            "type": "status",
            "content": "Connected to AI Assistant CLI",
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """
        Remove a WebSocket connection
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
        # Remove from session mapping
        session_to_remove = None
        for session_id, conn_id in self.session_connections.items():
            if conn_id == connection_id:
                session_to_remove = session_id
                break
        
        if session_to_remove:
            del self.session_connections[session_to_remove]
            
        logger.info(f"WebSocket connection disconnected: {connection_id}")
    
    async def send_message(self, connection_id: str, message: dict):
        """
        Send a message to a specific connection
        """
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def send_to_session(self, session_id: str, message: dict):
        """
        Send a message to a specific session
        """
        if session_id in self.session_connections:
            connection_id = self.session_connections[session_id]
            await self.send_message(connection_id, message)
    
    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected clients
        """
        for connection_id in list(self.active_connections.keys()):
            await self.send_message(connection_id, message)
    
    def get_connection_count(self) -> int:
        """
        Get the number of active connections
        """
        return len(self.active_connections)

# Global connection manager instance
manager = ConnectionManager()

@router.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat communication
    """
    connection_id = await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                logger.info(f"Received message from {session_id}: {message.get('type', 'unknown')}")
                
                # Process the message based on type
                await process_websocket_message(session_id, message)
                
            except json.JSONDecodeError:
                # Handle invalid JSON
                await manager.send_message(connection_id, {
                    "type": "error",
                    "content": "Invalid JSON format",
                    "session_id": session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"WebSocket disconnected for session {session_id}")

async def process_websocket_message(session_id: str, message: dict):
    """
    Process incoming WebSocket messages and route them appropriately
    """
    message_type = message.get("type", "unknown")
    content = message.get("content", "")
    
    # Add timestamp and session info
    response_base = {
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if message_type == "command":
        # Handle command messages (AI queries, agent requests, etc.)
        await handle_command_message(session_id, content, message, response_base)
        
    elif message_type == "ping":
        # Handle ping messages for connection health
        await manager.send_to_session(session_id, {
            **response_base,
            "type": "pong",
            "content": "Connection alive"
        })
        
    elif message_type == "knowledge_base_switch":
        # Handle knowledge base switching
        knowledge_base_id = message.get("knowledge_base_id")
        await handle_knowledge_base_switch(session_id, knowledge_base_id, response_base)
        
    else:
        # Handle unknown message types
        await manager.send_to_session(session_id, {
            **response_base,
            "type": "error",
            "content": f"Unknown message type: {message_type}"
        })

async def handle_command_message(session_id: str, content: str, message: dict, response_base: dict):
    """
    Handle command messages (AI queries, agent requests, etc.)
    """
    try:
        # Import here to avoid circular import
        from ..services.integration_service import integration_service
        
        # Extract user context from message (in production, this would come from JWT validation)
        # For now, we'll create a test user context
        user_context = create_test_user_context(message.get("user_id", "test-user"))
        
        # Get knowledge base ID if specified
        knowledge_base_id = message.get("knowledge_base_id")
        
        # Process command through integration service
        async for response in integration_service.process_user_command(
            session_id, content, user_context, knowledge_base_id
        ):
            # Add session info to response
            response.update(response_base)
            await manager.send_to_session(session_id, response)
            
    except Exception as e:
        logger.error(f"Error handling command message: {str(e)}")
        await manager.send_to_session(session_id, {
            **response_base,
            "type": "error",
            "content": f"Failed to process command: {str(e)}"
        })

async def handle_knowledge_base_switch(session_id: str, knowledge_base_id: str, response_base: dict):
    """
    Handle knowledge base switching requests
    """
    try:
        # Import here to avoid circular import
        from ..services.integration_service import integration_service
        
        # Extract user context (in production, this would come from JWT validation)
        user_context = create_test_user_context("test-user")
        
        # Switch knowledge base through integration service
        response = await integration_service.switch_knowledge_base(
            session_id, knowledge_base_id, user_context
        )
        
        # Add session info to response
        response.update(response_base)
        await manager.send_to_session(session_id, response)
        
    except Exception as e:
        logger.error(f"Error switching knowledge base: {str(e)}")
        await manager.send_to_session(session_id, {
            **response_base,
            "type": "error",
            "content": f"Failed to switch knowledge base: {str(e)}"
        })

# Utility functions for other parts of the application
def get_connection_manager() -> ConnectionManager:
    """
    Get the global connection manager instance
    """
    return manager

def create_test_user_context(user_id: str = "test-user") -> UserContext:
    """
    Create a test user context for development/testing
    """
    from datetime import datetime, timezone, timedelta
    
    return UserContext(
        user_id=user_id,
        email=f"{user_id}@example.com",
        name=f"Test User {user_id}",
        groups=["users"],
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        token_id=f"test-token-{user_id}"
    )