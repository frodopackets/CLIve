"""
Agent Service for AI Assistant CLI Backend
Integrates with the Birmingham weather/time agent
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from ..models.agent_response import AgentResponse
from ..models.enums import AgentResponseType
from .agent_monitoring_service import AgentMonitoringService

# Import the Birmingham agent
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from agent.birmingham_agent import BirminghamAgent

logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing AI agent interactions"""
    
    def __init__(self, monitoring_service: Optional[AgentMonitoringService] = None):
        """Initialize the agent service"""
        self.birmingham_agent = BirminghamAgent()
        self.agent_id = "birmingham_agent"
        self.monitoring_service = monitoring_service or AgentMonitoringService()
        logger.info("Agent service initialized with Birmingham agent")
    
    async def get_current_time(self) -> AgentResponse:
        """Get current time from Birmingham agent"""
        start_time = time.time()
        try:
            logger.info("Requesting current time from Birmingham agent")
            result = self.birmingham_agent.get_current_time()
            response_time = time.time() - start_time
            
            if result.get("error"):
                logger.error(f"Agent error getting time: {result.get('message')}")
                error_message = result.get("message", "Unknown error getting time")
                self.monitoring_service.record_request(self.agent_id, False, response_time, error_message)
                return AgentResponse.create_error_response(
                    agent_id=self.agent_id,
                    error_message=error_message
                )
            
            self.monitoring_service.record_request(self.agent_id, True, response_time)
            return AgentResponse.create_time_response(
                agent_id=self.agent_id,
                time_str=result["time"],
                timezone=result["timezone"]
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            error_message = f"Failed to get current time: {str(e)}"
            logger.error(f"Exception in get_current_time: {str(e)}")
            self.monitoring_service.record_request(self.agent_id, False, response_time, error_message)
            return AgentResponse.create_error_response(
                agent_id=self.agent_id,
                error_message=error_message
            )
    
    async def get_current_date(self) -> AgentResponse:
        """Get current date from Birmingham agent"""
        start_time = time.time()
        try:
            logger.info("Requesting current date from Birmingham agent")
            result = self.birmingham_agent.get_current_date()
            response_time = time.time() - start_time
            
            if result.get("error"):
                logger.error(f"Agent error getting date: {result.get('message')}")
                error_message = result.get("message", "Unknown error getting date")
                self.monitoring_service.record_request(self.agent_id, False, response_time, error_message)
                return AgentResponse.create_error_response(
                    agent_id=self.agent_id,
                    error_message=error_message
                )
            
            self.monitoring_service.record_request(self.agent_id, True, response_time)
            return AgentResponse.create_date_response(
                agent_id=self.agent_id,
                date_str=result["date"],
                day_of_week=result["day_of_week"]
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            error_message = f"Failed to get current date: {str(e)}"
            logger.error(f"Exception in get_current_date: {str(e)}")
            self.monitoring_service.record_request(self.agent_id, False, response_time, error_message)
            return AgentResponse.create_error_response(
                agent_id=self.agent_id,
                error_message=error_message
            )
    
    async def get_weather(self) -> AgentResponse:
        """Get weather information from Birmingham agent"""
        start_time = time.time()
        try:
            logger.info("Requesting weather from Birmingham agent")
            result = self.birmingham_agent.get_weather()
            response_time = time.time() - start_time
            
            if result.get("error"):
                logger.error(f"Agent error getting weather: {result.get('message')}")
                error_message = result.get("message", "Unknown error getting weather")
                self.monitoring_service.record_request(self.agent_id, False, response_time, error_message)
                return AgentResponse.create_error_response(
                    agent_id=self.agent_id,
                    error_message=error_message
                )
            
            # Format temperature with unit
            temp_str = f"{result['temperature']}{result.get('temperature_unit', '°F')}"
            humidity_str = f"{result['humidity']}{result.get('humidity_unit', '%')}" if result.get('humidity') else None
            
            self.monitoring_service.record_request(self.agent_id, True, response_time)
            return AgentResponse.create_weather_response(
                agent_id=self.agent_id,
                temperature=temp_str,
                condition=result["condition"],
                humidity=humidity_str
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            error_message = f"Failed to get weather: {str(e)}"
            logger.error(f"Exception in get_weather: {str(e)}")
            self.monitoring_service.record_request(self.agent_id, False, response_time, error_message)
            return AgentResponse.create_error_response(
                agent_id=self.agent_id,
                error_message=error_message
            )
    
    async def get_all_info(self) -> Dict[str, AgentResponse]:
        """Get comprehensive information from Birmingham agent"""
        try:
            logger.info("Requesting all info from Birmingham agent")
            result = self.birmingham_agent.get_all_info()
            
            if result.get("error"):
                logger.error(f"Agent error getting all info: {result.get('message')}")
                error_response = AgentResponse.create_error_response(
                    agent_id=self.agent_id,
                    error_message=result.get("message", "Unknown error getting all info")
                )
                return {
                    "time": error_response,
                    "date": error_response,
                    "weather": error_response
                }
            
            responses = {}
            
            # Process time data
            time_data = result.get("time", {})
            if time_data.get("success"):
                responses["time"] = AgentResponse.create_time_response(
                    agent_id=self.agent_id,
                    time_str=time_data["time"],
                    timezone=time_data["timezone"]
                )
            else:
                responses["time"] = AgentResponse.create_error_response(
                    agent_id=self.agent_id,
                    error_message="Failed to get time data"
                )
            
            # Process date data
            date_data = result.get("date", {})
            if date_data.get("success"):
                responses["date"] = AgentResponse.create_date_response(
                    agent_id=self.agent_id,
                    date_str=date_data["date"],
                    day_of_week=date_data["day_of_week"]
                )
            else:
                responses["date"] = AgentResponse.create_error_response(
                    agent_id=self.agent_id,
                    error_message="Failed to get date data"
                )
            
            # Process weather data
            weather_data = result.get("weather", {})
            if weather_data.get("success"):
                temp_str = f"{weather_data['temperature']}{weather_data.get('temperature_unit', '°F')}"
                humidity_str = f"{weather_data['humidity']}{weather_data.get('humidity_unit', '%')}" if weather_data.get('humidity') else None
                
                responses["weather"] = AgentResponse.create_weather_response(
                    agent_id=self.agent_id,
                    temperature=temp_str,
                    condition=weather_data["condition"],
                    humidity=humidity_str
                )
            else:
                responses["weather"] = AgentResponse.create_error_response(
                    agent_id=self.agent_id,
                    error_message="Failed to get weather data"
                )
            
            return responses
            
        except Exception as e:
            logger.error(f"Exception in get_all_info: {str(e)}")
            error_response = AgentResponse.create_error_response(
                agent_id=self.agent_id,
                error_message=f"Failed to get all info: {str(e)}"
            )
            return {
                "time": error_response,
                "date": error_response,
                "weather": error_response
            }
    
    async def invoke_agent(self, command: str) -> AgentResponse:
        """
        Invoke agent based on command string
        
        Args:
            command: Command string (e.g., "time", "date", "weather", "all")
            
        Returns:
            AgentResponse object
        """
        try:
            command = command.lower().strip()
            logger.info(f"Invoking agent with command: {command}")
            
            if command in ["time", "current_time", "get_time"]:
                return await self.get_current_time()
            elif command in ["date", "current_date", "get_date"]:
                return await self.get_current_date()
            elif command in ["weather", "current_weather", "get_weather"]:
                return await self.get_weather()
            elif command in ["all", "all_info", "everything"]:
                # For "all" command, return a combined response
                all_responses = await self.get_all_info()
                
                # Extract data from successful responses
                time_data = None
                date_data = None
                weather_data = None
                
                if "time" in all_responses and all_responses["time"].is_successful():
                    time_data = all_responses["time"].data
                
                if "date" in all_responses and all_responses["date"].is_successful():
                    date_data = all_responses["date"].data
                
                if "weather" in all_responses and all_responses["weather"].is_successful():
                    weather_data = all_responses["weather"].data
                
                return AgentResponse.create_combined_response(
                    agent_id=self.agent_id,
                    time_data=time_data,
                    date_data=date_data,
                    weather_data=weather_data
                )
            else:
                return AgentResponse.create_error_response(
                    agent_id=self.agent_id,
                    error_message=f"Unknown command: {command}. Available commands: time, date, weather, all"
                )
                
        except Exception as e:
            logger.error(f"Exception in invoke_agent: {str(e)}")
            return AgentResponse.create_error_response(
                agent_id=self.agent_id,
                error_message=f"Failed to invoke agent: {str(e)}"
            )
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status information about the agent"""
        try:
            # Try to access agent properties that might fail
            location = getattr(self.birmingham_agent, 'location_name', 'Birmingham, Alabama')
            
            # Test if agent is responsive by trying a simple method call
            test_result = self.birmingham_agent.get_current_time()
            if test_result.get("error"):
                raise Exception(f"Agent not responsive: {test_result.get('message', 'Unknown error')}")
            
            return {
                "agent_id": self.agent_id,
                "status": "active",
                "location": location,
                "available_commands": ["time", "date", "weather", "all"],
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Exception getting agent status: {str(e)}")
            return {
                "agent_id": self.agent_id,
                "status": "error",
                "location": "Unknown",
                "available_commands": [],
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }