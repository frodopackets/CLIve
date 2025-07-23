"""
Agent Response data model for AI Assistant CLI
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, Any

from .enums import AgentResponseType


@dataclass
class AgentResponse:
    """
    Represents a response from an AI agent
    """
    agent_id: str
    response_type: AgentResponseType
    data: Dict[str, Any]
    location: str = "Birmingham, Alabama"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def __post_init__(self):
        """Validate agent response data after initialization"""
        if not self.agent_id:
            raise ValueError("agent_id is required")
        
        if not self.data:
            raise ValueError("data cannot be empty")
        
        if self.timestamp > datetime.now(UTC):
            raise ValueError("timestamp cannot be in the future")
        
        # Validate response type specific data
        self._validate_response_data()
    
    def _validate_response_data(self) -> None:
        """Validate response data based on response type"""
        if self.response_type == AgentResponseType.TIME:
            required_fields = ["time", "timezone"]
        elif self.response_type == AgentResponseType.DATE:
            required_fields = ["date", "day_of_week"]
        elif self.response_type == AgentResponseType.WEATHER:
            required_fields = ["temperature", "condition"]
        elif self.response_type == AgentResponseType.COMBINED:
            # For combined responses, we expect at least one of the data types
            if not any(key in self.data for key in ["time", "date", "weather"]):
                raise ValueError("Combined response must contain at least one of: time, date, weather")
        elif self.response_type == AgentResponseType.ERROR:
            required_fields = ["error_message"]
        else:
            return  # No specific validation for unknown types
        
        if self.response_type != AgentResponseType.COMBINED:
            missing_fields = [field for field in required_fields if field not in self.data]
            if missing_fields:
                raise ValueError(f"Missing required fields for {self.response_type.value}: {missing_fields}")
    
    def get_formatted_response(self) -> str:
        """Get a formatted string representation of the response"""
        if self.response_type == AgentResponseType.TIME:
            return f"Current time in {self.location}: {self.data['time']} ({self.data['timezone']})"
        
        elif self.response_type == AgentResponseType.DATE:
            return f"Current date in {self.location}: {self.data['day_of_week']}, {self.data['date']}"
        
        elif self.response_type == AgentResponseType.WEATHER:
            temp = self.data['temperature']
            condition = self.data['condition']
            humidity = self.data.get('humidity', '')
            humidity_str = f", Humidity: {humidity}" if humidity else ""
            return f"Weather in {self.location}: {temp}, {condition}{humidity_str}"
        
        elif self.response_type == AgentResponseType.COMBINED:
            parts = []
            if "time" in self.data and isinstance(self.data["time"], dict):
                time_data = self.data["time"]
                if "time" in time_data and "timezone" in time_data:
                    parts.append(f"Time: {time_data['time']} ({time_data['timezone']})")
            
            if "date" in self.data and isinstance(self.data["date"], dict):
                date_data = self.data["date"]
                if "date" in date_data and "day_of_week" in date_data:
                    parts.append(f"Date: {date_data['day_of_week']}, {date_data['date']}")
            
            if "weather" in self.data and isinstance(self.data["weather"], dict):
                weather_data = self.data["weather"]
                if "temperature" in weather_data and "condition" in weather_data:
                    temp = weather_data["temperature"]
                    condition = weather_data["condition"]
                    humidity = weather_data.get("humidity", "")
                    humidity_str = f", Humidity: {humidity}" if humidity else ""
                    parts.append(f"Weather: {temp}, {condition}{humidity_str}")
            
            if parts:
                return f"Birmingham, Alabama - {' | '.join(parts)}"
            else:
                return f"Combined data for {self.location}"
        
        elif self.response_type == AgentResponseType.ERROR:
            return f"Agent Error: {self.data['error_message']}"
        
        else:
            return f"Agent Response: {self.data}"
    
    def is_successful(self) -> bool:
        """Check if the agent response indicates success"""
        return self.response_type != AgentResponseType.ERROR
    
    def get_data_value(self, key: str, default: Any = None) -> Any:
        """Get a specific value from the response data"""
        return self.data.get(key, default)
    
    def to_dict(self) -> dict:
        """Convert agent response to dictionary"""
        return {
            "agent_id": self.agent_id,
            "response_type": self.response_type.value,
            "data": self.data,
            "location": self.location,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AgentResponse":
        """Create agent response from dictionary"""
        return cls(
            agent_id=data["agent_id"],
            response_type=AgentResponseType(data["response_type"]),
            data=data["data"],
            location=data.get("location", "Birmingham, Alabama"),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )
    
    @classmethod
    def create_time_response(cls, agent_id: str, time_str: str, timezone: str) -> "AgentResponse":
        """Create a time response"""
        return cls(
            agent_id=agent_id,
            response_type=AgentResponseType.TIME,
            data={"time": time_str, "timezone": timezone}
        )
    
    @classmethod
    def create_date_response(cls, agent_id: str, date_str: str, day_of_week: str) -> "AgentResponse":
        """Create a date response"""
        return cls(
            agent_id=agent_id,
            response_type=AgentResponseType.DATE,
            data={"date": date_str, "day_of_week": day_of_week}
        )
    
    @classmethod
    def create_weather_response(cls, agent_id: str, temperature: str, condition: str, humidity: str = None) -> "AgentResponse":
        """Create a weather response"""
        data = {"temperature": temperature, "condition": condition}
        if humidity:
            data["humidity"] = humidity
        
        return cls(
            agent_id=agent_id,
            response_type=AgentResponseType.WEATHER,
            data=data
        )
    
    @classmethod
    def create_combined_response(cls, agent_id: str, time_data: dict = None, date_data: dict = None, weather_data: dict = None) -> "AgentResponse":
        """Create a combined response with time, date, and weather data"""
        data = {}
        if time_data:
            data["time"] = time_data
        if date_data:
            data["date"] = date_data
        if weather_data:
            data["weather"] = weather_data
        
        return cls(
            agent_id=agent_id,
            response_type=AgentResponseType.COMBINED,
            data=data
        )
    
    @classmethod
    def create_error_response(cls, agent_id: str, error_message: str) -> "AgentResponse":
        """Create an error response"""
        return cls(
            agent_id=agent_id,
            response_type=AgentResponseType.ERROR,
            data={"error_message": error_message}
        )