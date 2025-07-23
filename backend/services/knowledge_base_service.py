"""
Knowledge Base service for AWS Bedrock Knowledge Base integration
"""

import logging
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from fastapi import HTTPException, status

from backend.config import settings
from backend.models import KnowledgeBase, KnowledgeBaseStatus
from backend.services.auth_service import UserContext


logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """
    Service for interacting with AWS Bedrock Knowledge Bases
    Provides discovery, selection, and RAG query capabilities
    """
    
    def __init__(self):
        self.region = settings.bedrock_region
        
        # Initialize Bedrock clients
        self._init_bedrock_clients()
    
    def _init_bedrock_clients(self):
        """Initialize Bedrock clients for knowledge base operations"""
        try:
            # Bedrock Agent client for knowledge base management
            self.bedrock_agent = boto3.client(
                'bedrock-agent',
                region_name=self.region
            )
            
            # Bedrock Agent Runtime client for RAG queries
            self.bedrock_agent_runtime = boto3.client(
                'bedrock-agent-runtime',
                region_name=self.region
            )
            
            logger.info(f"Initialized Bedrock Knowledge Base clients for region: {self.region}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock Knowledge Base clients: {str(e)}")
            self.bedrock_agent = None
            self.bedrock_agent_runtime = None
    
    async def list_knowledge_bases(self, user_context: UserContext) -> List[KnowledgeBase]:
        """
        List all available knowledge bases for the user
        
        Args:
            user_context: User context for authorization
            
        Returns:
            List[KnowledgeBase]: Available knowledge bases
            
        Raises:
            HTTPException: If listing fails
        """
        if not self.bedrock_agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Knowledge Base service not available"
            )
        
        try:
            logger.info(f"Listing knowledge bases for user: {user_context.user_id}")
            
            # List knowledge bases from Bedrock
            response = self.bedrock_agent.list_knowledge_bases(
                maxResults=50  # Limit to reasonable number
            )
            
            knowledge_bases = []
            for kb_summary in response.get('knowledgeBaseSummaries', []):
                try:
                    # Get detailed information for each knowledge base
                    kb_detail = await self._get_knowledge_base_details(kb_summary['knowledgeBaseId'])
                    if kb_detail:
                        knowledge_bases.append(kb_detail)
                except Exception as e:
                    logger.warning(f"Failed to get details for KB {kb_summary['knowledgeBaseId']}: {str(e)}")
                    continue
            
            logger.info(f"Found {len(knowledge_bases)} knowledge bases")
            return knowledge_bases
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"Bedrock ClientError listing knowledge bases: {error_code} - {error_message}")
            
            if error_code == 'AccessDeniedException':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to knowledge bases"
                )
            elif error_code == 'ThrottlingException':
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Knowledge base service is throttling requests"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to list knowledge bases"
                )
                
        except BotoCoreError as e:
            logger.error(f"Bedrock BotoCoreError listing knowledge bases: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AWS service connection error"
            )
        except Exception as e:
            logger.error(f"Unexpected error listing knowledge bases: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_knowledge_base(self, knowledge_base_id: str, user_context: UserContext) -> Optional[KnowledgeBase]:
        """
        Get details for a specific knowledge base
        
        Args:
            knowledge_base_id: Knowledge base identifier
            user_context: User context for authorization
            
        Returns:
            KnowledgeBase: Knowledge base details if found, None otherwise
        """
        if not self.bedrock_agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Knowledge Base service not available"
            )
        
        try:
            return await self._get_knowledge_base_details(knowledge_base_id)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'ResourceNotFoundException':
                return None
            elif error_code == 'AccessDeniedException':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to knowledge base"
                )
            else:
                logger.error(f"Error getting knowledge base {knowledge_base_id}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get knowledge base"
                )
        except Exception as e:
            logger.error(f"Unexpected error getting knowledge base {knowledge_base_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def _get_knowledge_base_details(self, knowledge_base_id: str) -> Optional[KnowledgeBase]:
        """
        Get detailed information for a knowledge base
        
        Args:
            knowledge_base_id: Knowledge base identifier
            
        Returns:
            KnowledgeBase: Knowledge base details if found
        """
        try:
            response = self.bedrock_agent.get_knowledge_base(
                knowledgeBaseId=knowledge_base_id
            )
            
            kb_data = response['knowledgeBase']
            
            # Convert Bedrock response to our KnowledgeBase model
            return KnowledgeBase(
                knowledge_base_id=kb_data['knowledgeBaseId'],
                name=kb_data['name'],
                description=kb_data.get('description', ''),
                status=KnowledgeBaseStatus(kb_data['status']),
                created_date=kb_data['createdAt'],
                updated_date=kb_data['updatedAt']
            )
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return None
            raise
    
    async def query_knowledge_base(
        self, 
        knowledge_base_id: str, 
        query: str, 
        user_context: UserContext,
        max_results: int = 5
    ) -> AsyncGenerator[str, None]:
        """
        Query a knowledge base using RetrieveAndGenerate API with streaming
        
        Args:
            knowledge_base_id: Knowledge base to query
            query: User's question/query
            user_context: User context for authorization
            max_results: Maximum number of results to retrieve
            
        Yields:
            str: Streaming response chunks from the knowledge base
            
        Raises:
            HTTPException: If query fails
        """
        if not self.bedrock_agent_runtime:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Knowledge Base runtime service not available"
            )
        
        try:
            logger.info(f"Querying knowledge base {knowledge_base_id} for user {user_context.user_id}")
            
            # Prepare the retrieve and generate request
            request_body = {
                'input': {
                    'text': query
                },
                'retrieveAndGenerateConfiguration': {
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': knowledge_base_id,
                        'modelArn': f'arn:aws:bedrock:{self.region}::foundation-model/{settings.bedrock_model_id}',
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': max_results
                            }
                        }
                    }
                }
            }
            
            # Use streaming retrieve and generate
            response = self.bedrock_agent_runtime.retrieve_and_generate_stream(**request_body)
            
            # Process streaming response
            async for chunk in self._process_rag_streaming_response(response):
                yield chunk
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"Bedrock ClientError querying KB {knowledge_base_id}: {error_code} - {error_message}")
            
            if error_code == 'ResourceNotFoundException':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Knowledge base not found"
                )
            elif error_code == 'AccessDeniedException':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to knowledge base"
                )
            elif error_code == 'ValidationException':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid query parameters: {error_message}"
                )
            elif error_code == 'ThrottlingException':
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Knowledge base service is throttling requests"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to query knowledge base"
                )
                
        except BotoCoreError as e:
            logger.error(f"Bedrock BotoCoreError querying KB {knowledge_base_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AWS service connection error"
            )
        except Exception as e:
            logger.error(f"Unexpected error querying KB {knowledge_base_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def _process_rag_streaming_response(self, response) -> AsyncGenerator[str, None]:
        """
        Process streaming response from RetrieveAndGenerate API
        
        Args:
            response: Bedrock streaming response
            
        Yields:
            str: Content chunks from the response
        """
        try:
            stream = response.get('stream')
            if not stream:
                logger.error("No response stream from RetrieveAndGenerate")
                return
            
            for event in stream:
                if 'chunk' in event:
                    chunk_data = event['chunk']
                    
                    # Handle different chunk types
                    if 'bytes' in chunk_data:
                        # Decode the chunk content
                        import json
                        chunk_content = json.loads(chunk_data['bytes'].decode())
                        
                        # Extract text from the chunk
                        if 'outputText' in chunk_content:
                            yield chunk_content['outputText']
                        elif 'text' in chunk_content:
                            yield chunk_content['text']
                
                elif 'metadata' in event:
                    # Handle metadata (citations, sources, etc.)
                    metadata = event['metadata']
                    logger.debug(f"RAG query metadata: {metadata}")
                
                elif 'internalServerException' in event:
                    error_msg = event['internalServerException'].get('message', 'Internal server error')
                    logger.error(f"RAG streaming error: {error_msg}")
                    raise Exception(f"Knowledge base streaming error: {error_msg}")
                
                elif 'validationException' in event:
                    error_msg = event['validationException'].get('message', 'Validation error')
                    logger.error(f"RAG validation error: {error_msg}")
                    raise Exception(f"Knowledge base validation error: {error_msg}")
                        
        except Exception as e:
            logger.error(f"Error processing RAG streaming response: {str(e)}")
            raise
    
    async def query_knowledge_base_simple(
        self, 
        knowledge_base_id: str, 
        query: str, 
        user_context: UserContext,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Query a knowledge base using RetrieveAndGenerate API (non-streaming)
        
        Args:
            knowledge_base_id: Knowledge base to query
            query: User's question/query
            user_context: User context for authorization
            max_results: Maximum number of results to retrieve
            
        Returns:
            Dict: Complete response with answer and citations
        """
        if not self.bedrock_agent_runtime:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Knowledge Base runtime service not available"
            )
        
        try:
            logger.info(f"Simple query to knowledge base {knowledge_base_id} for user {user_context.user_id}")
            
            # Prepare the retrieve and generate request
            response = self.bedrock_agent_runtime.retrieve_and_generate(
                input={
                    'text': query
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': knowledge_base_id,
                        'modelArn': f'arn:aws:bedrock:{self.region}::foundation-model/{settings.bedrock_model_id}',
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': max_results
                            }
                        }
                    }
                }
            )
            
            # Extract response data
            output = response.get('output', {})
            citations = response.get('citations', [])
            
            return {
                'answer': output.get('text', ''),
                'citations': citations,
                'session_id': response.get('sessionId'),
                'knowledge_base_id': knowledge_base_id
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Error in simple KB query: {error_code}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to query knowledge base"
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if Knowledge Base service is available
        
        Returns:
            Dict: Health status information
        """
        try:
            if not self.bedrock_agent or not self.bedrock_agent_runtime:
                return {
                    "status": "unhealthy",
                    "error": "Knowledge Base clients not initialized"
                }
            
            # Try to list knowledge bases as a health check
            response = self.bedrock_agent.list_knowledge_bases(maxResults=1)
            
            return {
                "status": "healthy",
                "region": self.region,
                "available_knowledge_bases": len(response.get('knowledgeBaseSummaries', []))
            }
            
        except Exception as e:
            logger.error(f"Knowledge Base health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global Knowledge Base service instance
knowledge_base_service = KnowledgeBaseService()