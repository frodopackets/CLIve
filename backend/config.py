"""
Configuration settings for the AI Assistant CLI backend
"""
import os
from typing import List, Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings with environment variable support
    """
    
    # Application settings
    app_name: str = "AI Assistant CLI Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # AWS settings
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Bedrock settings
    bedrock_model_id: str = "amazon.nova-pro-v1:0"
    bedrock_region: str = "us-east-1"
    bedrock_max_tokens: int = 4096
    bedrock_temperature: float = 0.7
    bedrock_top_p: float = 0.9
    
    # DynamoDB settings
    dynamodb_table_name: str = "ai-assistant-sessions"
    dynamodb_region: str = "us-east-1"
    
    # JWT settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.amazonaws.com"
    ]
    
    # Logging settings
    log_level: str = "INFO"
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

# Global settings instance
settings = Settings()