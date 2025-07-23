"""
AWS Bedrock service for Nova Pro model integration with streaming support
"""

import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from fastapi import HTTPException, status

from backend.config import settings
from backend.models import Message, MessageType


logger = logging.getLogger(__name__)


class BedrockService:
    """
    Service for interacting with AWS Bedrock Nova Pro model
    Provides streaming response handling and error management
    """
    
    def __init__(self):
        self.model_id = settings.bedrock_model_id
        self.region = settings.bedrock_region
        self.max_tokens = settings.bedrock_max_tokens
        self.temperature = settings.bedrock_temperature
        self.top_p = settings.bedrock_top_p
        
        # Initialize Bedrock client
        self._init_bedrock_client()
    
    def _init_bedrock_client(self):
        """Initialize Bedrock runtime client"""
        try:
            self.bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=self.region
            )
            logger.info(f"Initialized Bedrock client for region: {self.region}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {str(e)}")
            self.bedrock_runtime = None
    
    async def generate_response(
        self, 
        user_message: str, 
        conversation_history: list[Message] = None,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response from Nova Pro model
        
        Args:
            user_message: User's input message
            conversation_history: Previous messages for context
            system_prompt: Optional system prompt to guide the model
            
        Yields:
            str: Streaming response chunks
            
        Raises:
            HTTPException: If Bedrock service fails
        """
        if not self.bedrock_runtime:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bedrock service not available"
            )
        
        try:
            # Prepare the request payload for Nova Pro
            request_body = self._prepare_nova_pro_request(
                user_message, 
                conversation_history, 
                system_prompt
            )
            
            logger.info(f"Sending request to Nova Pro model: {self.model_id}")
            
            # Invoke model with streaming
            response = self.bedrock_runtime.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Process streaming response
            async for chunk in self._process_streaming_response(response):
                yield chunk
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"Bedrock ClientError: {error_code} - {error_message}")
            
            if error_code == 'ValidationException':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid request to Bedrock: {error_message}"
                )
            elif error_code == 'ThrottlingException':
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Bedrock service is throttling requests"
                )
            elif error_code == 'ModelNotReadyException':
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Nova Pro model is not ready"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Bedrock service error"
                )
                
        except BotoCoreError as e:
            logger.error(f"Bedrock BotoCoreError: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AWS service connection error"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Bedrock service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def _prepare_nova_pro_request(
        self, 
        user_message: str, 
        conversation_history: list[Message] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare request payload for Nova Pro model
        
        Args:
            user_message: User's input message
            conversation_history: Previous messages for context
            system_prompt: Optional system prompt
            
        Returns:
            Dict: Request payload for Nova Pro
        """
        # Build messages array for Nova Pro
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Limit to last 10 messages
                if msg.message_type == MessageType.USER:
                    messages.append({
                        "role": "user",
                        "content": msg.content
                    })
                elif msg.message_type == MessageType.ASSISTANT:
                    messages.append({
                        "role": "assistant",
                        "content": msg.content
                    })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Nova Pro request format
        request_body = {
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stop_sequences": []
        }
        
        return request_body
    
    async def _process_streaming_response(self, response) -> AsyncGenerator[str, None]:
        """
        Process streaming response from Bedrock
        
        Args:
            response: Bedrock streaming response
            
        Yields:
            str: Content chunks from the response
        """
        try:
            stream = response.get('body')
            if not stream:
                logger.error("No response body from Bedrock")
                return
            
            for event in stream:
                chunk = event.get('chunk')
                if chunk:
                    chunk_data = json.loads(chunk.get('bytes').decode())
                    
                    # Handle different event types from Nova Pro
                    if 'type' in chunk_data:
                        if chunk_data['type'] == 'content_block_delta':
                            # Extract text content from delta
                            delta = chunk_data.get('delta', {})
                            if 'text' in delta:
                                yield delta['text']
                        elif chunk_data['type'] == 'message_stop':
                            # End of message
                            break
                        elif chunk_data['type'] == 'error':
                            # Handle streaming errors
                            error_msg = chunk_data.get('message', 'Unknown streaming error')
                            logger.error(f"Streaming error from Nova Pro: {error_msg}")
                            raise Exception(f"Model streaming error: {error_msg}")
                    
                    # Fallback for different response formats
                    elif 'completion' in chunk_data:
                        yield chunk_data['completion']
                    elif 'text' in chunk_data:
                        yield chunk_data['text']
                        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode streaming response: {str(e)}")
            raise Exception("Invalid response format from Bedrock")
        except Exception as e:
            logger.error(f"Error processing streaming response: {str(e)}")
            raise
    
    async def generate_simple_response(
        self, 
        user_message: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a simple non-streaming response (for testing)
        
        Args:
            user_message: User's input message
            system_prompt: Optional system prompt
            
        Returns:
            str: Complete response from the model
        """
        full_response = ""
        async for chunk in self.generate_response(user_message, [], system_prompt):
            full_response += chunk
        
        return full_response.strip()
    
    def create_assistant_message(self, content: str, session_id: str) -> Message:
        """
        Create a Message object for assistant responses
        
        Args:
            content: Response content from the model
            session_id: Session identifier
            
        Returns:
            Message: Formatted assistant message
        """
        return Message(
            session_id=session_id,
            content=content,
            message_type=MessageType.ASSISTANT,
            timestamp=datetime.now(timezone.utc),
            metadata={
                "model_id": self.model_id,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if Bedrock service is available
        
        Returns:
            Dict: Health status information
        """
        try:
            if not self.bedrock_runtime:
                return {
                    "status": "unhealthy",
                    "error": "Bedrock client not initialized"
                }
            
            # Try a simple test request
            test_response = await self.generate_simple_response(
                "Hello", 
                "Respond with just 'OK' to confirm you're working."
            )
            
            return {
                "status": "healthy",
                "model_id": self.model_id,
                "region": self.region,
                "test_response_length": len(test_response)
            }
            
        except HTTPException as e:
            logger.error(f"Bedrock health check failed: {e.detail}")
            return {
                "status": "unhealthy",
                "error": e.detail
            }
        except Exception as e:
            logger.error(f"Bedrock health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global Bedrock service instance
bedrock_service = BedrockService()