"""
Bedrock AI router for Nova Pro model interactions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
import json
import logging

from backend.services.auth_service import auth_service, UserContext
from fastapi.security import HTTPAuthorizationCredentials
from backend.services.bedrock_service import bedrock_service
from backend.services.session_service import session_service
from backend.models import MessageRequest, MessageResponse, MessageType, Message
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bedrock", tags=["bedrock"])


@router.post("/chat")
async def chat_with_bedrock(
    request: MessageRequest,
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> StreamingResponse:
    """
    Chat with Bedrock Nova Pro model with streaming response
    
    Args:
        request: Message request containing user input and session info
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        StreamingResponse: Streaming AI response
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        # Validate session access
        session = await session_service.get_session(request.session_id, current_user.user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Get conversation history for context
        conversation_history = await session_service.get_conversation_history(
            request.session_id, 
            current_user.user_id, 
            limit=10
        )
        
        # Create user message and add to session
        user_message = Message(
            session_id=request.session_id,
            content=request.content,
            message_type=MessageType.USER,
            timestamp=datetime.now(timezone.utc),
            metadata={"user_id": current_user.user_id}
        )
        
        await session_service.add_message_to_session(
            request.session_id, 
            current_user.user_id, 
            user_message
        )
        
        # Generate streaming response
        async def generate_streaming_response():
            """Generate streaming response with proper formatting"""
            try:
                assistant_response = ""
                
                # Stream response from Bedrock
                async for chunk in bedrock_service.generate_response(
                    request.content, 
                    conversation_history,
                    system_prompt=request.system_prompt
                ):
                    assistant_response += chunk
                    
                    # Send chunk as Server-Sent Events format
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
                # Create assistant message and save to session
                assistant_message = bedrock_service.create_assistant_message(
                    assistant_response, 
                    request.session_id
                )
                
                await session_service.add_message_to_session(
                    request.session_id, 
                    current_user.user_id, 
                    assistant_message
                )
                
                # Send completion event
                yield f"data: {json.dumps({'type': 'complete', 'message_id': assistant_message.message_id})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in streaming response: {str(e)}")
                error_data = {
                    'type': 'error', 
                    'error': 'Failed to generate response'
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_streaming_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Bedrock chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )


@router.post("/simple-chat")
async def simple_chat_with_bedrock(
    request: MessageRequest,
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> MessageResponse:
    """
    Simple non-streaming chat with Bedrock Nova Pro model
    
    Args:
        request: Message request containing user input
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        MessageResponse: Complete AI response
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        # Validate session access
        session = await session_service.get_session(request.session_id, current_user.user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Get conversation history for context
        conversation_history = await session_service.get_conversation_history(
            request.session_id, 
            current_user.user_id, 
            limit=10
        )
        
        # Generate response from Bedrock
        response_content = await bedrock_service.generate_simple_response(
            request.content,
            system_prompt=request.system_prompt
        )
        
        # Create and save user message
        user_message = Message(
            session_id=request.session_id,
            content=request.content,
            message_type=MessageType.USER,
            timestamp=datetime.now(timezone.utc),
            metadata={"user_id": current_user.user_id}
        )
        
        await session_service.add_message_to_session(
            request.session_id, 
            current_user.user_id, 
            user_message
        )
        
        # Create and save assistant message
        assistant_message = bedrock_service.create_assistant_message(
            response_content, 
            request.session_id
        )
        
        await session_service.add_message_to_session(
            request.session_id, 
            current_user.user_id, 
            assistant_message
        )
        
        return MessageResponse(
            message_id=assistant_message.message_id,
            session_id=request.session_id,
            content=response_content,
            message_type=MessageType.ASSISTANT,
            timestamp=assistant_message.timestamp,
            metadata=assistant_message.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in simple Bedrock chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )


@router.get("/health")
async def bedrock_health_check(
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> Dict[str, Any]:
    """
    Check Bedrock service health
    
    Args:
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        Dict: Health status information
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        health_status = await bedrock_service.health_check()
        return health_status
        
    except Exception as e:
        logger.error(f"Error in Bedrock health check: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/models")
async def list_available_models(
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> Dict[str, Any]:
    """
    List available Bedrock models (currently just Nova Pro)
    
    Args:
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        Dict: Available models information
    """
    # Get current user from credentials
    current_user = await auth_service.get_current_user(credentials)
    
    return {
        "models": [
            {
                "model_id": bedrock_service.model_id,
                "name": "Amazon Nova Pro",
                "description": "Advanced multimodal foundation model",
                "capabilities": ["text-generation", "conversation", "reasoning"],
                "max_tokens": bedrock_service.max_tokens,
                "current_settings": {
                    "temperature": bedrock_service.temperature,
                    "top_p": bedrock_service.top_p
                }
            }
        ],
        "default_model": bedrock_service.model_id
    }