"""
Agent router for AI Assistant CLI Backend
Provides REST API endpoints for agent interactions
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..services.agent_service import AgentService
from ..services.agent_monitoring_service import AgentMonitoringService
from ..models.agent_response import AgentResponse

logger = logging.getLogger("ai-assistant-cli")

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])

# Request/Response models
class AgentCommandRequest(BaseModel):
    """Request model for agent commands"""
    command: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "command": "time"
            }
        }

class AgentStatusResponse(BaseModel):
    """Response model for agent status"""
    agent_id: str
    status: str
    location: str
    available_commands: list[str]
    last_check: str
    error: str = None

# Dependency to get agent service
async def get_agent_service() -> AgentService:
    """Get agent service instance"""
    return AgentService()

@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status(agent_service: AgentService = Depends(get_agent_service)):
    """
    Get the current status of the Birmingham agent
    """
    try:
        logger.info("Getting agent status")
        status_info = agent_service.get_agent_status()
        
        return AgentStatusResponse(
            agent_id=status_info["agent_id"],
            status=status_info["status"],
            location=status_info.get("location", "Birmingham, Alabama"),
            available_commands=status_info.get("available_commands", []),
            last_check=status_info["last_check"],
            error=status_info.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")

@router.post("/invoke")
async def invoke_agent(
    request: AgentCommandRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> Dict[str, Any]:
    """
    Invoke the Birmingham agent with a specific command
    
    Available commands:
    - time: Get current time
    - date: Get current date  
    - weather: Get current weather
    - all: Get all information
    """
    try:
        logger.info(f"Invoking agent with command: {request.command}")
        
        response = await agent_service.invoke_agent(request.command)
        
        return {
            "success": response.is_successful(),
            "agent_id": response.agent_id,
            "response_type": response.response_type.value,
            "data": response.data,
            "location": response.location,
            "timestamp": response.timestamp.isoformat(),
            "formatted_response": response.get_formatted_response()
        }
        
    except Exception as e:
        logger.error(f"Error invoking agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to invoke agent: {str(e)}")

@router.get("/time")
async def get_current_time(agent_service: AgentService = Depends(get_agent_service)) -> Dict[str, Any]:
    """
    Get current time from Birmingham agent
    """
    try:
        logger.info("Getting current time from agent")
        response = await agent_service.get_current_time()
        
        return {
            "success": response.is_successful(),
            "agent_id": response.agent_id,
            "response_type": response.response_type.value,
            "data": response.data,
            "location": response.location,
            "timestamp": response.timestamp.isoformat(),
            "formatted_response": response.get_formatted_response()
        }
        
    except Exception as e:
        logger.error(f"Error getting time from agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get time: {str(e)}")

@router.get("/date")
async def get_current_date(agent_service: AgentService = Depends(get_agent_service)) -> Dict[str, Any]:
    """
    Get current date from Birmingham agent
    """
    try:
        logger.info("Getting current date from agent")
        response = await agent_service.get_current_date()
        
        return {
            "success": response.is_successful(),
            "agent_id": response.agent_id,
            "response_type": response.response_type.value,
            "data": response.data,
            "location": response.location,
            "timestamp": response.timestamp.isoformat(),
            "formatted_response": response.get_formatted_response()
        }
        
    except Exception as e:
        logger.error(f"Error getting date from agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get date: {str(e)}")

@router.get("/weather")
async def get_weather(agent_service: AgentService = Depends(get_agent_service)) -> Dict[str, Any]:
    """
    Get current weather from Birmingham agent
    """
    try:
        logger.info("Getting weather from agent")
        response = await agent_service.get_weather()
        
        return {
            "success": response.is_successful(),
            "agent_id": response.agent_id,
            "response_type": response.response_type.value,
            "data": response.data,
            "location": response.location,
            "timestamp": response.timestamp.isoformat(),
            "formatted_response": response.get_formatted_response()
        }
        
    except Exception as e:
        logger.error(f"Error getting weather from agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get weather: {str(e)}")

@router.get("/all")
async def get_all_info(agent_service: AgentService = Depends(get_agent_service)) -> Dict[str, Any]:
    """
    Get comprehensive information (time, date, weather) from Birmingham agent
    """
    try:
        logger.info("Getting all info from agent")
        responses = await agent_service.get_all_info()
        
        # Format the combined response
        result = {
            "success": all(resp.is_successful() for resp in responses.values()),
            "agent_id": "birmingham_agent",
            "location": "Birmingham, Alabama",
            "timestamp": max(resp.timestamp for resp in responses.values()).isoformat(),
            "data": {},
            "formatted_responses": {}
        }
        
        for key, response in responses.items():
            result["data"][key] = response.data
            result["formatted_responses"][key] = response.get_formatted_response()
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting all info from agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get all info: {str(e)}")

@router.get("/metrics")
async def get_agent_metrics(agent_service: AgentService = Depends(get_agent_service)) -> Dict[str, Any]:
    """
    Get performance metrics for the Birmingham agent
    """
    try:
        logger.info("Getting agent metrics")
        metrics = agent_service.monitoring_service.get_agent_metrics("birmingham_agent")
        
        if not metrics:
            return {
                "agent_id": "birmingham_agent",
                "message": "No metrics available yet",
                "metrics": None
            }
        
        return {
            "agent_id": "birmingham_agent",
            "metrics": {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": metrics.success_rate(),
                "average_response_time": metrics.average_response_time,
                "uptime_percentage": metrics.uptime_percentage,
                "last_request_time": metrics.last_request_time.isoformat() if metrics.last_request_time else None,
                "last_error": metrics.last_error,
                "last_error_time": metrics.last_error_time.isoformat() if metrics.last_error_time else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting agent metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent metrics: {str(e)}")

@router.get("/health")
async def get_agent_health(agent_service: AgentService = Depends(get_agent_service)) -> Dict[str, Any]:
    """
    Get health status of the Birmingham agent
    """
    try:
        logger.info("Getting agent health status")
        health = agent_service.monitoring_service.check_agent_health("birmingham_agent")
        return health
        
    except Exception as e:
        logger.error(f"Error getting agent health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent health: {str(e)}")

@router.get("/alerts")
async def get_agent_alerts(agent_service: AgentService = Depends(get_agent_service)) -> Dict[str, Any]:
    """
    Get current alerts for agents
    """
    try:
        logger.info("Getting agent alerts")
        alerts = agent_service.monitoring_service.get_alerts()
        return {
            "alerts": alerts,
            "alert_count": len(alerts)
        }
        
    except Exception as e:
        logger.error(f"Error getting agent alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent alerts: {str(e)}")

@router.get("/performance")
async def get_performance_summary(agent_service: AgentService = Depends(get_agent_service)) -> Dict[str, Any]:
    """
    Get performance summary for the Birmingham agent
    """
    try:
        logger.info("Getting agent performance summary")
        performance = agent_service.monitoring_service.get_performance_summary("birmingham_agent")
        return performance
        
    except Exception as e:
        logger.error(f"Error getting agent performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent performance: {str(e)}")