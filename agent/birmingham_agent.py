"""
Birmingham Weather/Time Agent using strands-agents SDK
Provides time, date, and weather information for Birmingham, Alabama
"""
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import requests
import pytz
from strands import Agent, tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BirminghamAgent(Agent):
    """Agent that provides time, date, and weather information for Birmingham, AL"""
    
    def __init__(self):
        # Initialize with system prompt describing the agent's purpose
        system_prompt = """You are a Birmingham, Alabama information agent. You provide accurate time, date, and weather information for Birmingham, Alabama. You have access to tools that can retrieve current time, date, and weather data for the Birmingham area."""
        
        super().__init__(
            system_prompt=system_prompt
        )
        
        # Birmingham, AL coordinates
        self.latitude = 33.5186
        self.longitude = -86.8104
        self.location_name = "Birmingham, Alabama"
        self.timezone = pytz.timezone('America/Chicago')  # Central Time
        
        # Weather API configuration (using OpenWeatherMap as example)
        self.weather_api_key = os.getenv('OPENWEATHER_API_KEY')
        self.weather_base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    def _handle_error(self, operation: str, error: Exception) -> Dict[str, Any]:
        """Standardized error handling for agent operations"""
        error_msg = f"Error in {operation}: {str(error)}"
        logger.error(error_msg)
        return {
            "error": True,
            "message": error_msg,
            "operation": operation,
            "location": self.location_name
        }
    
    @tool
    def get_current_time(self) -> Dict[str, Any]:
        """Get the current time in Birmingham, Alabama"""
        try:
            # Get current time in Birmingham's timezone
            utc_now = datetime.now(timezone.utc)
            utc_now = pytz.utc.localize(utc_now.replace(tzinfo=None))
            local_time = utc_now.astimezone(self.timezone)
            
            return {
                "success": True,
                "time": local_time.strftime("%I:%M:%S %p"),
                "time_24h": local_time.strftime("%H:%M:%S"),
                "timezone": "Central Time (CT)",
                "timezone_offset": local_time.strftime("%z"),
                "location": self.location_name,
                "timestamp": local_time.isoformat()
            }
        except Exception as e:
            return self._handle_error("get_current_time", e)
    
    @tool
    def get_current_date(self) -> Dict[str, Any]:
        """Get the current date in Birmingham, Alabama"""
        try:
            # Get current date in Birmingham's timezone
            utc_now = datetime.now(timezone.utc)
            utc_now = pytz.utc.localize(utc_now.replace(tzinfo=None))
            local_time = utc_now.astimezone(self.timezone)
            
            return {
                "success": True,
                "date": local_time.strftime("%B %d, %Y"),
                "date_short": local_time.strftime("%m/%d/%Y"),
                "day_of_week": local_time.strftime("%A"),
                "day_of_year": local_time.timetuple().tm_yday,
                "week_of_year": local_time.isocalendar()[1],
                "location": self.location_name,
                "timestamp": local_time.isoformat()
            }
        except Exception as e:
            return self._handle_error("get_current_date", e)
    
    @tool
    def get_weather(self) -> Dict[str, Any]:
        """Get current weather information for Birmingham, Alabama"""
        try:
            if not self.weather_api_key:
                # Return mock data if no API key is configured
                logger.warning("No weather API key configured, returning mock data")
                return {
                    "success": True,
                    "temperature": 72,
                    "temperature_unit": "°F",
                    "condition": "Partly Cloudy",
                    "description": "Few clouds",
                    "humidity": 65,
                    "humidity_unit": "%",
                    "pressure": 30.12,
                    "pressure_unit": "inHg",
                    "wind_speed": 5.2,
                    "wind_speed_unit": "mph",
                    "wind_direction": "SW",
                    "location": self.location_name,
                    "data_source": "mock",
                    "note": "This is mock weather data. Set OPENWEATHER_API_KEY environment variable for real data."
                }
            
            # Make API request to OpenWeatherMap
            params = {
                'lat': self.latitude,
                'lon': self.longitude,
                'appid': self.weather_api_key,
                'units': 'imperial'  # Fahrenheit
            }
            
            response = requests.get(self.weather_base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Convert wind direction from degrees to cardinal direction
            def degrees_to_cardinal(degrees):
                directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                             "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                return directions[round(degrees / 22.5) % 16]
            
            wind_direction = degrees_to_cardinal(data.get('wind', {}).get('deg', 0))
            
            return {
                "success": True,
                "temperature": round(data['main']['temp']),
                "temperature_unit": "°F",
                "feels_like": round(data['main']['feels_like']),
                "condition": data['weather'][0]['main'],
                "description": data['weather'][0]['description'].title(),
                "humidity": data['main']['humidity'],
                "humidity_unit": "%",
                "pressure": round(data['main']['pressure'] * 0.02953, 2),  # Convert hPa to inHg
                "pressure_unit": "inHg",
                "wind_speed": round(data.get('wind', {}).get('speed', 0), 1),
                "wind_speed_unit": "mph",
                "wind_direction": wind_direction,
                "visibility": round(data.get('visibility', 0) * 0.000621371, 1),  # Convert m to miles
                "visibility_unit": "miles",
                "location": self.location_name,
                "data_source": "OpenWeatherMap",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except requests.RequestException as e:
            return self._handle_error("get_weather (API request)", e)
        except KeyError as e:
            return self._handle_error("get_weather (data parsing)", e)
        except Exception as e:
            return self._handle_error("get_weather", e)
    
    @tool
    def get_all_info(self) -> Dict[str, Any]:
        """Get comprehensive time, date, and weather information for Birmingham, Alabama"""
        try:
            time_info = self.get_current_time()
            date_info = self.get_current_date()
            weather_info = self.get_weather()
            
            return {
                "success": True,
                "location": self.location_name,
                "time": time_info,
                "date": date_info,
                "weather": weather_info,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return self._handle_error("get_all_info", e)


if __name__ == "__main__":
    agent = BirminghamAgent()
    print("Birmingham Agent initialized successfully!")
    print("Available tools:")
    print("- get_current_time()")
    print("- get_current_date()")
    print("- get_weather()")
    print("- get_all_info()")
    
    # Demonstrate functionality
    print("\n--- Demo ---")
    time_result = agent.get_current_time()
    print(f"Current time: {time_result.get('time', 'Error')}")
    
    date_result = agent.get_current_date()
    print(f"Current date: {date_result.get('date', 'Error')}")
    
    weather_result = agent.get_weather()
    print(f"Weather: {weather_result.get('condition', 'Error')} - {weather_result.get('temperature', 'N/A')}°F")