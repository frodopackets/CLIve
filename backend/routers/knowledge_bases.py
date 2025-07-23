"""
Knowledge base router for managing Bedrock Knowledge Bases
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Dict, Any
import json
import logging

from backend.services.auth_service import auth_service, UserContext
from backend.services.knowledge_base_service import knowledge_base_service
from backend.models import KnowledgeBaseResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge-bases", tags=["knowledge-bases"])


@router.get("/")
async def list_knowledge_bases(
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> List[KnowledgeBaseResponse]:
    """
    List all available Bedrock Knowledge Bases
    
    Args:
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        List[KnowledgeBaseResponse]: Available knowledge bases
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        # Get knowledge bases from service
        knowledge_bases = await knowledge_base_service.list_knowledge_bases(current_user)
        
        # Convert to response format
        return [
            KnowledgeBaseResponse(
                knowledge_base_id=kb.knowledge_base_id,
                name=kb.name,
                description=kb.description,
                status=kb.status,
                created_date=kb.created_date,
                updated_date=kb.updated_date,
                is_active=kb.is_active(),
                display_name=kb.get_display_name()
            )
            for kb in knowledge_bases
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing knowledge bases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list knowledge bases"
        )


@router.get("/{knowledge_base_id}")
async def get_knowledge_base(
    knowledge_base_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> KnowledgeBaseResponse:
    """
    Get details for a specific knowledge base
    
    Args:
        knowledge_base_id: Knowledge base identifier
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        KnowledgeBaseResponse: Knowledge base details
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        # Get knowledge base from service
        kb = await knowledge_base_service.get_knowledge_base(knowledge_base_id, current_user)
        
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        return KnowledgeBaseResponse(
            knowledge_base_id=kb.knowledge_base_id,
            name=kb.name,
            description=kb.description,
            status=kb.status,
            created_date=kb.created_date,
            updated_date=kb.updated_date,
            is_active=kb.is_active(),
            display_name=kb.get_display_name()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge base {knowledge_base_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get knowledge base"
        )


@router.post("/{knowledge_base_id}/query")
async def query_knowledge_base(
    knowledge_base_id: str,
    query_request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> StreamingResponse:
    """
    Query a knowledge base using RAG (Retrieve and Generate)
    
    Args:
        knowledge_base_id: Knowledge base to query
        query_request: Query request containing 'query' and optional 'max_results'
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        StreamingResponse: Streaming RAG response
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        # Extract query parameters
        query = query_request.get('query', '').strip()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query text is required"
            )
        
        max_results = query_request.get('max_results', 5)
        if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
            max_results = 5
        
        # Generate streaming response
        async def generate_streaming_response():
            """Generate streaming RAG response"""
            try:
                async for chunk in knowledge_base_service.query_knowledge_base(
                    knowledge_base_id, 
                    query, 
                    current_user,
                    max_results
                ):
                    # Send chunk as Server-Sent Events format
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
                # Send completion event
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in RAG streaming response: {str(e)}")
                error_data = {
                    'type': 'error', 
                    'error': 'Failed to query knowledge base'
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
        logger.error(f"Error querying knowledge base {knowledge_base_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query knowledge base"
        )


@router.post("/{knowledge_base_id}/query-simple")
async def query_knowledge_base_simple(
    knowledge_base_id: str,
    query_request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> Dict[str, Any]:
    """
    Query a knowledge base using RAG (non-streaming)
    
    Args:
        knowledge_base_id: Knowledge base to query
        query_request: Query request containing 'query' and optional 'max_results'
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        Dict: Complete RAG response with answer and citations
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        # Extract query parameters
        query = query_request.get('query', '').strip()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query text is required"
            )
        
        max_results = query_request.get('max_results', 5)
        if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
            max_results = 5
        
        # Query knowledge base
        result = await knowledge_base_service.query_knowledge_base_simple(
            knowledge_base_id, 
            query, 
            current_user,
            max_results
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in simple knowledge base query {knowledge_base_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query knowledge base"
        )


@router.get("/health")
async def knowledge_base_health_check(
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.security)
) -> Dict[str, Any]:
    """
    Check Knowledge Base service health
    
    Args:
        credentials: HTTP Bearer credentials for authentication
        
    Returns:
        Dict: Health status information
    """
    try:
        # Get current user from credentials
        current_user = await auth_service.get_current_user(credentials)
        
        health_status = await knowledge_base_service.health_check()
        return health_status
        
    except Exception as e:
        logger.error(f"Error in Knowledge Base health check: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }