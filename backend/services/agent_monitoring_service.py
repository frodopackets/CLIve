"""
Agent Monitoring Service for AI Assistant CLI Backend
Provides monitoring, metrics, and health checking for agents
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Metrics for agent performance and reliability"""
    agent_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    uptime_percentage: float = 100.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100.0
    
    def update_response_time(self, response_time: float):
        """Update response time metrics"""
        self.response_times.append(response_time)
        if self.response_times:
            self.average_response_time = sum(self.response_times) / len(self.response_times)


class AgentMonitoringService:
    """Service for monitoring agent health and performance"""
    
    def __init__(self):
        """Initialize the monitoring service"""
        self.metrics: Dict[str, AgentMetrics] = {}
        self.health_checks: Dict[str, datetime] = {}
        self.alert_thresholds = {
            "max_response_time": 10.0,  # seconds
            "min_success_rate": 90.0,   # percentage
            "max_error_rate": 10.0      # percentage
        }
        logger.info("Agent monitoring service initialized")
    
    def record_request(self, agent_id: str, success: bool, response_time: float, error_message: str = None):
        """Record a request and its outcome"""
        if agent_id not in self.metrics:
            self.metrics[agent_id] = AgentMetrics(agent_id=agent_id)
        
        metrics = self.metrics[agent_id]
        metrics.total_requests += 1
        metrics.last_request_time = datetime.now()
        metrics.update_response_time(response_time)
        
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
            metrics.last_error = error_message
            metrics.last_error_time = datetime.now()
        
        # Update uptime percentage (simplified calculation)
        metrics.uptime_percentage = metrics.success_rate()
        
        logger.debug(f"Recorded request for {agent_id}: success={success}, response_time={response_time:.2f}s")
    
    def get_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """Get metrics for a specific agent"""
        return self.metrics.get(agent_id)
    
    def get_all_metrics(self) -> Dict[str, AgentMetrics]:
        """Get metrics for all agents"""
        return self.metrics.copy()
    
    def check_agent_health(self, agent_id: str) -> Dict[str, Any]:
        """Check the health status of an agent"""
        metrics = self.metrics.get(agent_id)
        if not metrics:
            return {
                "agent_id": agent_id,
                "status": "unknown",
                "message": "No metrics available",
                "last_check": datetime.now().isoformat()
            }
        
        health_status = "healthy"
        issues = []
        
        # Check response time
        if metrics.average_response_time > self.alert_thresholds["max_response_time"]:
            health_status = "degraded"
            issues.append(f"High response time: {metrics.average_response_time:.2f}s")
        
        # Check success rate
        success_rate = metrics.success_rate()
        if success_rate < self.alert_thresholds["min_success_rate"]:
            health_status = "unhealthy"
            issues.append(f"Low success rate: {success_rate:.1f}%")
        
        # Check for recent errors
        if metrics.last_error_time and metrics.last_error_time > datetime.now() - timedelta(minutes=5):
            if health_status == "healthy":
                health_status = "degraded"
            issues.append(f"Recent error: {metrics.last_error}")
        
        # Check if agent has been inactive
        if metrics.last_request_time and metrics.last_request_time < datetime.now() - timedelta(minutes=30):
            health_status = "inactive"
            issues.append("Agent has been inactive for over 30 minutes")
        
        self.health_checks[agent_id] = datetime.now()
        
        return {
            "agent_id": agent_id,
            "status": health_status,
            "issues": issues,
            "metrics": {
                "total_requests": metrics.total_requests,
                "success_rate": success_rate,
                "average_response_time": metrics.average_response_time,
                "uptime_percentage": metrics.uptime_percentage,
                "last_request": metrics.last_request_time.isoformat() if metrics.last_request_time else None,
                "last_error": metrics.last_error,
                "last_error_time": metrics.last_error_time.isoformat() if metrics.last_error_time else None
            },
            "last_check": datetime.now().isoformat()
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health across all agents"""
        if not self.metrics:
            return {
                "status": "no_agents",
                "message": "No agents registered",
                "agent_count": 0,
                "last_check": datetime.now().isoformat()
            }
        
        agent_healths = []
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0
        inactive_count = 0
        
        for agent_id in self.metrics.keys():
            health = self.check_agent_health(agent_id)
            agent_healths.append(health)
            
            status = health["status"]
            if status == "healthy":
                healthy_count += 1
            elif status == "degraded":
                degraded_count += 1
            elif status == "unhealthy":
                unhealthy_count += 1
            elif status == "inactive":
                inactive_count += 1
        
        # Determine overall system status
        total_agents = len(self.metrics)
        if unhealthy_count > 0:
            system_status = "unhealthy"
        elif degraded_count > 0:
            system_status = "degraded"
        elif inactive_count == total_agents:
            system_status = "inactive"
        else:
            system_status = "healthy"
        
        return {
            "status": system_status,
            "agent_count": total_agents,
            "healthy_agents": healthy_count,
            "degraded_agents": degraded_count,
            "unhealthy_agents": unhealthy_count,
            "inactive_agents": inactive_count,
            "agents": agent_healths,
            "last_check": datetime.now().isoformat()
        }
    
    def get_performance_summary(self, agent_id: str = None) -> Dict[str, Any]:
        """Get performance summary for an agent or all agents"""
        if agent_id:
            metrics = self.metrics.get(agent_id)
            if not metrics:
                return {"error": f"No metrics found for agent {agent_id}"}
            
            return {
                "agent_id": agent_id,
                "total_requests": metrics.total_requests,
                "success_rate": metrics.success_rate(),
                "average_response_time": metrics.average_response_time,
                "recent_response_times": list(metrics.response_times)[-10:],  # Last 10 response times
                "uptime_percentage": metrics.uptime_percentage,
                "last_request": metrics.last_request_time.isoformat() if metrics.last_request_time else None
            }
        else:
            # Summary for all agents
            summaries = {}
            for agent_id, metrics in self.metrics.items():
                summaries[agent_id] = {
                    "total_requests": metrics.total_requests,
                    "success_rate": metrics.success_rate(),
                    "average_response_time": metrics.average_response_time,
                    "uptime_percentage": metrics.uptime_percentage
                }
            
            return {
                "agents": summaries,
                "system_totals": {
                    "total_requests": sum(m.total_requests for m in self.metrics.values()),
                    "total_successful": sum(m.successful_requests for m in self.metrics.values()),
                    "total_failed": sum(m.failed_requests for m in self.metrics.values()),
                    "average_success_rate": sum(m.success_rate() for m in self.metrics.values()) / len(self.metrics) if self.metrics else 0
                }
            }
    
    def reset_metrics(self, agent_id: str = None):
        """Reset metrics for an agent or all agents"""
        if agent_id:
            if agent_id in self.metrics:
                self.metrics[agent_id] = AgentMetrics(agent_id=agent_id)
                logger.info(f"Reset metrics for agent {agent_id}")
        else:
            self.metrics.clear()
            self.health_checks.clear()
            logger.info("Reset all agent metrics")
    
    def set_alert_thresholds(self, thresholds: Dict[str, float]):
        """Update alert thresholds"""
        self.alert_thresholds.update(thresholds)
        logger.info(f"Updated alert thresholds: {self.alert_thresholds}")
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts for all agents"""
        alerts = []
        
        for agent_id, metrics in self.metrics.items():
            agent_alerts = []
            
            # Response time alert
            if metrics.average_response_time > self.alert_thresholds["max_response_time"]:
                agent_alerts.append({
                    "type": "high_response_time",
                    "message": f"Average response time ({metrics.average_response_time:.2f}s) exceeds threshold ({self.alert_thresholds['max_response_time']}s)",
                    "severity": "warning"
                })
            
            # Success rate alert
            success_rate = metrics.success_rate()
            if success_rate < self.alert_thresholds["min_success_rate"]:
                agent_alerts.append({
                    "type": "low_success_rate",
                    "message": f"Success rate ({success_rate:.1f}%) below threshold ({self.alert_thresholds['min_success_rate']}%)",
                    "severity": "critical"
                })
            
            # Recent error alert
            if metrics.last_error_time and metrics.last_error_time > datetime.now() - timedelta(minutes=5):
                agent_alerts.append({
                    "type": "recent_error",
                    "message": f"Recent error: {metrics.last_error}",
                    "severity": "warning"
                })
            
            if agent_alerts:
                alerts.append({
                    "agent_id": agent_id,
                    "alerts": agent_alerts,
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts