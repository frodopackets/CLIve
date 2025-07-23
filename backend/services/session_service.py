"""
Session management service for handling user sessions and conversation history
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from fastapi import HTTPException, status

from backend.models import Session, Message, SessionStatus, MessageType
from backend.services.auth_service import UserContext


logger = logging.getLogger(__name__)


class SessionService:
    """
    Service for managing user sessions and conversation history with DynamoDB storage
    """
    
    def __init__(self):
        # DynamoDB configuration
        self.table_name = os.getenv("DYNAMODB_SESSIONS_TABLE", "ai-assistant-sessions")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        
        # Session configuration
        self.session_timeout_hours = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
        self.max_conversation_history = int(os.getenv("MAX_CONVERSATION_HISTORY", "100"))
        
        # Initialize DynamoDB client
        self._init_dynamodb_client()
    
    def _init_dynamodb_client(self):
        """Initialize DynamoDB client with proper configuration"""
        try:
            # Use environment variables or IAM roles for authentication
            self.dynamodb = boto3.resource(
                'dynamodb',
                region_name=self.region
            )
            self.table = self.dynamodb.Table(self.table_name)
            logger.info(f"Initialized DynamoDB client for table: {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB client: {str(e)}")
            # For development/testing, we'll handle this gracefully
            self.dynamodb = None
            self.table = None
    
    async def create_session(self, user_context: UserContext, knowledge_base_id: Optional[str] = None) -> Session:
        """
        Create a new session for the user
        
        Args:
            user_context: User context from JWT token
            knowledge_base_id: Optional knowledge base to associate with session
            
        Returns:
            Session: Created session object
            
        Raises:
            HTTPException: If session creation fails
        """
        try:
            session = Session(
                session_id=str(uuid4()),
                user_id=user_context.user_id,
                knowledge_base_id=knowledge_base_id,
                status=SessionStatus.ACTIVE
            )
            
            # Store session in DynamoDB
            await self._store_session(session)
            
            logger.info(f"Created new session {session.session_id} for user {user_context.user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create session for user {user_context.user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )
    
    async def get_session(self, session_id: str, user_id: str) -> Optional[Session]:
        """
        Retrieve a session by ID, ensuring it belongs to the user
        
        Args:
            session_id: Session identifier
            user_id: User identifier for authorization
            
        Returns:
            Session: Session object if found and authorized, None otherwise
        """
        try:
            session_data = await self._get_session_from_db(session_id)
            
            if not session_data:
                logger.warning(f"Session {session_id} not found")
                return None
            
            session = Session.from_dict(session_data)
            
            # Verify session belongs to the user
            if session.user_id != user_id:
                logger.warning(f"User {user_id} attempted to access session {session_id} owned by {session.user_id}")
                return None
            
            # Check if session has expired
            if session.is_expired(self.session_timeout_hours):
                logger.info(f"Session {session_id} has expired, marking as expired")
                session.status = SessionStatus.EXPIRED
                await self._store_session(session)
                return None
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to retrieve session {session_id}: {str(e)}")
            return None
    
    async def update_session(self, session: Session) -> bool:
        """
        Update an existing session
        
        Args:
            session: Session object to update
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            await self._store_session(session)
            logger.info(f"Updated session {session.session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update session {session.session_id}: {str(e)}")
            return False
    
    async def add_message_to_session(self, session_id: str, user_id: str, message: Message) -> bool:
        """
        Add a message to a session's conversation history
        
        Args:
            session_id: Session identifier
            user_id: User identifier for authorization
            message: Message to add
            
        Returns:
            bool: True if message added successfully, False otherwise
        """
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                logger.warning(f"Cannot add message to non-existent session {session_id}")
                return False
            
            # Ensure message belongs to the session
            message.session_id = session_id
            
            # Add message to session
            session.add_message(message)
            
            # Trim conversation history if it exceeds maximum
            if len(session.conversation_history) > self.max_conversation_history:
                session.conversation_history = session.conversation_history[-self.max_conversation_history:]
                logger.info(f"Trimmed conversation history for session {session_id}")
            
            # Update session in database
            return await self.update_session(session)
            
        except Exception as e:
            logger.error(f"Failed to add message to session {session_id}: {str(e)}")
            return False
    
    async def get_conversation_history(self, session_id: str, user_id: str, limit: int = 10) -> List[Message]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
            user_id: User identifier for authorization
            limit: Maximum number of messages to return
            
        Returns:
            List[Message]: Recent messages from the conversation
        """
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                return []
            
            return session.get_recent_messages(limit)
            
        except Exception as e:
            logger.error(f"Failed to get conversation history for session {session_id}: {str(e)}")
            return []
    
    async def list_user_sessions(self, user_id: str, active_only: bool = True) -> List[Session]:
        """
        List all sessions for a user
        
        Args:
            user_id: User identifier
            active_only: If True, only return active sessions
            
        Returns:
            List[Session]: User's sessions
        """
        try:
            sessions_data = await self._get_user_sessions_from_db(user_id)
            sessions = []
            
            for session_data in sessions_data:
                session = Session.from_dict(session_data)
                
                # Check if session has expired
                if session.is_expired(self.session_timeout_hours):
                    session.status = SessionStatus.EXPIRED
                    await self._store_session(session)
                
                # Filter based on active_only flag
                if active_only and session.status != SessionStatus.ACTIVE:
                    continue
                
                sessions.append(session)
            
            # Sort by last activity (most recent first)
            sessions.sort(key=lambda s: s.last_activity, reverse=True)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list sessions for user {user_id}: {str(e)}")
            return []
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """
        Delete a session (mark as archived)
        
        Args:
            session_id: Session identifier
            user_id: User identifier for authorization
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                return False
            
            session.status = SessionStatus.ARCHIVED
            return await self.update_session(session)
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {str(e)}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (background task)
        
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            # This would typically be called by a scheduled task
            # For now, we'll implement a simple cleanup
            
            if not self.table:
                logger.warning("DynamoDB table not available for cleanup")
                return 0
            
            # Scan for expired sessions (in production, use a GSI with TTL)
            response = self.table.scan()
            cleaned_count = 0
            
            for item in response.get('Items', []):
                session = Session.from_dict(item)
                
                if session.is_expired(self.session_timeout_hours) and session.status == SessionStatus.ACTIVE:
                    session.status = SessionStatus.EXPIRED
                    await self._store_session(session)
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {str(e)}")
            return 0
    
    async def _store_session(self, session: Session):
        """Store session in DynamoDB"""
        if not self.table:
            # For testing without DynamoDB
            logger.warning("DynamoDB table not available, session not persisted")
            return
        
        try:
            session_data = session.to_dict()
            # Add TTL for automatic cleanup (optional)
            ttl = int((session.last_activity + timedelta(days=30)).timestamp())
            session_data['ttl'] = ttl
            
            self.table.put_item(Item=session_data)
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"DynamoDB error storing session {session.session_id}: {str(e)}")
            raise
    
    async def _get_session_from_db(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session from DynamoDB"""
        if not self.table:
            return None
        
        try:
            response = self.table.get_item(Key={'session_id': session_id})
            return response.get('Item')
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"DynamoDB error retrieving session {session_id}: {str(e)}")
            return None
    
    async def _get_user_sessions_from_db(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve all sessions for a user from DynamoDB"""
        if not self.table:
            return []
        
        try:
            # In production, use a GSI on user_id for better performance
            response = self.table.scan(
                FilterExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
            )
            return response.get('Items', [])
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"DynamoDB error retrieving sessions for user {user_id}: {str(e)}")
            return []


# Global session service instance
session_service = SessionService()