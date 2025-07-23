"""
Integration service that orchestrates all backend services for end-to-end request/response flow
"""

import logging
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timezone

from fastapi import HTTPException, status

from backend.models import Message, MessageType, Session
from backend.services.auth_service import UserContext, auth_service
from backend.services.session_service import session_service
from backend.services.bedrock_service import bedrock_service
from backend.services.knowledge_base_service import knowledge_base_service
from backend.services.agent_service import AgentService
from backend.services.agent_monitoring_service import AgentMonitoringService
from backend.middleware.integration_error_handling import (
    IntegrationErrorHandler, 
    handle_integration_errors,
    with_circuit_breaker,
    bedrock_circuit_breaker,
    knowledge_base_circuit_breaker,
    agent_circuit_breaker
)


logger = logging.getLogger(__name__)


class IntegrationService:
    """
    Service that orchestrates all backend services for complete request/response flows
    Handles authentication, session management, AI services, and agent integration
    """
    
    def __init__(self):
        self.agent_service = AgentService(AgentMonitoringService())
        
        # Command patterns for routing
        self.agent_commands = {
            'time', 'current_time', 'get_time',
            'date', 'current_date', 'get_date', 
            'weather', 'current_weather', 'get_weather',
            'all', 'all_info', 'everything'
        }
        
        self.knowledge_base_indicators = {
            'kb:', 'knowledge:', 'search:', 'find:', 'lookup:'
        }
        
        logger.info("Integration service initialized")
    
    @handle_integration_errors("integration")
    async def process_user_command(
        self, 
        session_id: str, 
        user_message: str, 
        user_context: UserContext,
        knowledge_base_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a user command through the complete system flow
        
        Args:
            session_id: Session identifier
            user_message: User's input message
            user_context: Authenticated user context
            knowledge_base_id: Optional knowledge base to use for RAG
            
        Yields:
            Dict: Streaming response messages
        """
        # Get or create session
        session = await self._get_or_create_session(session_id, user_context, knowledge_base_id)
        if not session:
            yield IntegrationErrorHandler.create_error_response("Failed to create or retrieve session")
            return
        
        # Store user message
        user_msg = Message(
            session_id=session_id,
            content=user_message,
            message_type=MessageType.USER,
            timestamp=datetime.now(timezone.utc),
            metadata={"user_id": user_context.user_id}
        )
        
        await session_service.add_message_to_session(session_id, user_context.user_id, user_msg)
        
        # Send acknowledgment
        yield self._create_status_response("Processing your request...")
        
        # Route command based on content
        command_type = self._classify_command(user_message)
        
        if command_type == "agent":
            async for response in self._handle_agent_command(session, user_message, user_context):
                yield response
        elif command_type == "knowledge_base":
            async for response in self._handle_knowledge_base_query(session, user_message, user_context):
                yield response
        else:
            async for response in self._handle_general_ai_query(session, user_message, user_context):
                yield response
    
    async def _get_or_create_session(
        self, 
        session_id: str, 
        user_context: UserContext,
        knowledge_base_id: Optional[str] = None
    ) -> Optional[Session]:
        """Get existing session or create new one"""
        try:
            # Try to get existing session
            session = await session_service.get_session(session_id, user_context.user_id)
            
            if not session:
                # Create new session
                session = await session_service.create_session(user_context, knowledge_base_id)
                logger.info(f"Created new session {session.session_id} for user {user_context.user_id}")
            else:
                # Update knowledge base if provided
                if knowledge_base_id and session.knowledge_base_id != knowledge_base_id:
                    session.knowledge_base_id = knowledge_base_id
                    await session_service.update_session(session)
                    logger.info(f"Updated session {session_id} knowledge base to {knowledge_base_id}")
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to get or create session: {str(e)}")
            return None
    
    def _classify_command(self, user_message: str) -> str:
        """Classify user command to determine routing"""
        message_lower = user_message.lower().strip()
        
        # Check for agent commands
        if any(cmd in message_lower for cmd in self.agent_commands):
            return "agent"
        
        # Check for knowledge base indicators
        if any(indicator in message_lower for indicator in self.knowledge_base_indicators):
            return "knowledge_base"
        
        # Default to general AI query
        return "general_ai"
    
    @with_circuit_breaker(agent_circuit_breaker)
    async def _handle_agent_command(
        self, 
        session: Session, 
        user_message: str, 
        user_context: UserContext
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle agent-specific commands"""
        yield self._create_status_response("Contacting Birmingham agent...")
        
        # Extract agent command
        message_lower = user_message.lower().strip()
        agent_command = "all"  # default
        
        for cmd in self.agent_commands:
            if cmd in message_lower:
                agent_command = cmd
                break
        
        # Invoke agent
        agent_response = await self.agent_service.invoke_agent(agent_command)
        
        if agent_response.is_successful():
            # Format agent response for display
            formatted_response = self._format_agent_response(agent_response)
            
            # Store agent response as message
            agent_msg = Message(
                session_id=session.session_id,
                content=formatted_response,
                message_type=MessageType.AGENT,
                timestamp=datetime.now(timezone.utc),
                metadata={
                    "agent_id": agent_response.agent_id,
                    "response_type": agent_response.response_type.value,
                    "location": agent_response.location
                }
            )
            
            await session_service.add_message_to_session(
                session.session_id, 
                user_context.user_id, 
                agent_msg
            )
            
            yield self._create_agent_response(formatted_response, agent_response.to_dict())
        else:
            error_msg = f"Agent error: {agent_response.data.get('error_message', 'Unknown error')}"
            yield IntegrationErrorHandler.create_error_response(error_msg, "agent_error")
    
    @with_circuit_breaker(knowledge_base_circuit_breaker)
    async def _handle_knowledge_base_query(
        self, 
        session: Session, 
        user_message: str, 
        user_context: UserContext
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle knowledge base queries using RAG"""
        # Determine knowledge base to use
        kb_id = session.knowledge_base_id
        if not kb_id:
            # Get default knowledge base
            kb_list = await knowledge_base_service.list_knowledge_bases(user_context)
            if kb_list:
                kb_id = kb_list[0].knowledge_base_id
                session.knowledge_base_id = kb_id
                await session_service.update_session(session)
            else:
                yield IntegrationErrorHandler.create_error_response("No knowledge bases available", "no_knowledge_bases")
                return
        
        yield self._create_status_response(f"Searching knowledge base...")
        
        # Clean up query (remove indicators)
        clean_query = user_message
        for indicator in self.knowledge_base_indicators:
            clean_query = clean_query.replace(indicator, "").strip()
        
        # Query knowledge base with streaming
        response_content = ""
        async for chunk in knowledge_base_service.query_knowledge_base(
            kb_id, clean_query, user_context
        ):
            response_content += chunk
            yield self._create_streaming_response(chunk)
        
        # Store complete response
        if response_content:
            kb_msg = Message(
                session_id=session.session_id,
                content=response_content,
                message_type=MessageType.ASSISTANT,
                timestamp=datetime.now(timezone.utc),
                metadata={
                    "knowledge_base_id": kb_id,
                    "query_type": "rag",
                    "original_query": user_message
                }
            )
            
            await session_service.add_message_to_session(
                session.session_id, 
                user_context.user_id, 
                kb_msg
            )
    
    @with_circuit_breaker(bedrock_circuit_breaker)
    async def _handle_general_ai_query(
        self, 
        session: Session, 
        user_message: str, 
        user_context: UserContext
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle general AI queries using Bedrock"""
        yield self._create_status_response("Thinking...")
        
        # Get conversation history
        conversation_history = await session_service.get_conversation_history(
            session.session_id, user_context.user_id, limit=10
        )
        
        # Generate response with streaming
        response_content = ""
        async for chunk in bedrock_service.generate_response(
            user_message, conversation_history
        ):
            response_content += chunk
            yield self._create_streaming_response(chunk)
        
        # Store complete response
        if response_content:
            ai_msg = bedrock_service.create_assistant_message(
                response_content, session.session_id
            )
            
            await session_service.add_message_to_session(
                session.session_id, 
                user_context.user_id, 
                ai_msg
            )
    
    def _format_agent_response(self, agent_response) -> str:
        """Format agent response for display"""
        if agent_response.response_type.value == "TIME":
            return f"Current time in {agent_response.location}: {agent_response.data['time']} ({agent_response.data['timezone']})"
        elif agent_response.response_type.value == "DATE":
            return f"Current date in {agent_response.location}: {agent_response.data['date']} ({agent_response.data['day_of_week']})"
        elif agent_response.response_type.value == "WEATHER":
            weather_info = f"Weather in {agent_response.location}: {agent_response.data['condition']}, {agent_response.data['temperature']}"
            if agent_response.data.get('humidity'):
                weather_info += f", Humidity: {agent_response.data['humidity']}"
            return weather_info
        elif agent_response.response_type.value == "COMBINED":
            parts = []
            if agent_response.data.get('time'):
                parts.append(f"Time: {agent_response.data['time']['time']} ({agent_response.data['time']['timezone']})")
            if agent_response.data.get('date'):
                parts.append(f"Date: {agent_response.data['date']['date']} ({agent_response.data['date']['day_of_week']})")
            if agent_response.data.get('weather'):
                weather = agent_response.data['weather']
                weather_str = f"Weather: {weather['condition']}, {weather['temperature']}"
                if weather.get('humidity'):
                    weather_str += f", Humidity: {weather['humidity']}"
                parts.append(weather_str)
            
            return f"Birmingham, Alabama Information:\n" + "\n".join(parts)
        else:
            return str(agent_response.data)
    
    def _create_streaming_response(self, content: str) -> Dict[str, Any]:
        """Create streaming response message"""
        return {
            "type": "response",
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "streaming": True
        }
    
    def _create_status_response(self, message: str) -> Dict[str, Any]:
        """Create status response message"""
        return {
            "type": "status",
            "content": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response message"""
        return {
            "type": "error",
            "content": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _create_agent_response(self, content: str, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create agent response message"""
        return {
            "type": "agent_response",
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "agent_data": agent_data
            }
        }
    
    async def switch_knowledge_base(
        self, 
        session_id: str, 
        knowledge_base_id: str, 
        user_context: UserContext
    ) -> Dict[str, Any]:
        """Switch knowledge base for a session"""
        try:
            session = await session_service.get_session(session_id, user_context.user_id)
            if not session:
                return self._create_error_response("Session not found")
            
            # Verify knowledge base exists
            kb = await knowledge_base_service.get_knowledge_base(knowledge_base_id, user_context)
            if not kb:
                return self._create_error_response("Knowledge base not found")
            
            # Update session
            session.knowledge_base_id = knowledge_base_id
            success = await session_service.update_session(session)
            
            if success:
                return {
                    "type": "status",
                    "content": f"Switched to knowledge base: {kb.name}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "knowledge_base_id": knowledge_base_id,
                        "knowledge_base_name": kb.name
                    }
                }
            else:
                return self._create_error_response("Failed to update session")
                
        except Exception as e:
            logger.error(f"Error switching knowledge base: {str(e)}")
            return self._create_error_response(f"Failed to switch knowledge base: {str(e)}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Check all services
            bedrock_health = await bedrock_service.health_check()
            kb_health = await knowledge_base_service.health_check()
            agent_status = self.agent_service.get_agent_status()
            
            return {
                "status": "healthy" if all([
                    bedrock_health.get("status") == "healthy",
                    kb_health.get("status") == "healthy",
                    agent_status.get("status") == "active"
                ]) else "degraded",
                "services": {
                    "bedrock": bedrock_health,
                    "knowledge_base": kb_health,
                    "agent": agent_status
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# Global integration service instance
integration_service = IntegrationService()