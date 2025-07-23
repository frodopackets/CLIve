"""
Session management router for handling user sessions
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
import logging

from backend.services.auth_service import auth_service
from backend.services.session_service import session_service
from backend.services.knowledge_base_service import knowledge_base_service
from backend.models import (
    SessionCreateRequest, 
    SessionResponse, 
    ConversationHistoryResponse,
    MessageResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.get("/")
async def list_sessions(
    active_only: bool = True,
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> List[SessionResponse]:
    """
    List all sessions for the authenticated user
    
    Args:
        active_only: If True, only return active sessions
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        List[SessionResponse]: User's sessions
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        # Get user sessions
        sessions = await session_service.list_user_sessions(current_user.user_id, active_only)
        
        # Convert to response format
        return [
            SessionResponse(
                session_id=session.session_id,
                user_id=session.user_id,
                created_at=session.created_at,
                last_activity=session.last_activity,
                knowledge_base_id=session.knowledge_base_id,
                status=session.status,
                message_count=len(session.conversation_history)
            )
            for session in sessions
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sessions"
        )


@router.post("/")
async def create_session(
    request: SessionCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> SessionResponse:
    """
    Create a new session for the authenticated user
    
    Args:
        request: Session creation request
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        SessionResponse: Created session details
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        # Validate knowledge base if provided
        if request.knowledge_base_id:
            kb = await knowledge_base_service.get_knowledge_base(request.knowledge_base_id, current_user)
            if not kb:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Knowledge base not found"
                )
            if not kb.is_active():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Knowledge base is not active"
                )
        
        # Create session
        session = await session_service.create_session(current_user, request.knowledge_base_id)
        
        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at,
            last_activity=session.last_activity,
            knowledge_base_id=session.knowledge_base_id,
            status=session.status,
            message_count=len(session.conversation_history)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> SessionResponse:
    """
    Get details for a specific session
    
    Args:
        session_id: Session identifier
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        SessionResponse: Session details
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        # Get session
        session = await session_service.get_session(session_id, current_user.user_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at,
            last_activity=session.last_activity,
            knowledge_base_id=session.knowledge_base_id,
            status=session.status,
            message_count=len(session.conversation_history)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session"
        )


@router.put("/{session_id}/knowledge-base")
async def switch_knowledge_base(
    session_id: str,
    request: Dict[str, Optional[str]],
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> SessionResponse:
    """
    Switch the knowledge base for a session
    
    Args:
        session_id: Session identifier
        request: Request containing 'knowledge_base_id' (can be null to clear)
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        SessionResponse: Updated session details
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        # Get session
        session = await session_service.get_session(session_id, current_user.user_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get new knowledge base ID from request
        new_kb_id = request.get('knowledge_base_id')
        
        # Validate knowledge base if provided
        if new_kb_id:
            kb = await knowledge_base_service.get_knowledge_base(new_kb_id, current_user)
            if not kb:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Knowledge base not found"
                )
            if not kb.is_active():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Knowledge base is not active"
                )
        
        # Update session knowledge base
        session.knowledge_base_id = new_kb_id
        
        # Save updated session
        success = await session_service.update_session(session)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update session"
            )
        
        logger.info(f"Switched knowledge base for session {session_id} to {new_kb_id}")
        
        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at,
            last_activity=session.last_activity,
            knowledge_base_id=session.knowledge_base_id,
            status=session.status,
            message_count=len(session.conversation_history)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching knowledge base for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to switch knowledge base"
        )


@router.get("/{session_id}/history")
async def get_conversation_history(
    session_id: str,
    limit: int = 10,
    page: int = 1,
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> ConversationHistoryResponse:
    """
    Get conversation history for a session
    
    Args:
        session_id: Session identifier
        limit: Number of messages per page (max 50)
        page: Page number (1-based)
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        ConversationHistoryResponse: Conversation history
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        # Validate parameters
        if limit < 1 or limit > 50:
            limit = 10
        if page < 1:
            page = 1
        
        # Get conversation history
        messages = await session_service.get_conversation_history(
            session_id, 
            current_user.user_id, 
            limit * page  # Get enough messages for pagination
        )
        
        if not messages:
            return ConversationHistoryResponse(
                session_id=session_id,
                messages=[],
                total_count=0,
                page=page,
                page_size=limit
            )
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_messages = messages[start_idx:end_idx]
        
        # Convert to response format
        message_responses = [
            MessageResponse(
                message_id=msg.message_id,
                session_id=msg.session_id,
                content=msg.content,
                message_type=msg.message_type,
                timestamp=msg.timestamp,
                metadata=msg.metadata
            )
            for msg in paginated_messages
        ]
        
        return ConversationHistoryResponse(
            session_id=session_id,
            messages=message_responses,
            total_count=len(messages),
            page=page,
            page_size=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation history"
        )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> Dict[str, Any]:
    """
    Delete a specific session (mark as archived)
    
    Args:
        session_id: Session identifier
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        Dict: Deletion confirmation
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        # Delete session
        success = await session_service.delete_session(session_id, current_user.user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        from datetime import datetime, timezone
        return {
            "session_id": session_id,
            "status": "deleted",
            "deleted_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )