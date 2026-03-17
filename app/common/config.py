"""
Configuration management using environment variables.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service URLs
    PRODUCT_SERVICE_URL: str = "http://localhost:8001"
    CREATIVE_SERVICE_URL: str = "http://localhost:8002"
    STRATEGY_SERVICE_URL: str = "http://localhost:8003"
    META_SERVICE_URL: str = "http://localhost:8004"
    LOGS_SERVICE_URL: str = "http://localhost:8005"
    SCHEMA_VALIDATOR_SERVICE_URL: str = "http://localhost:8006"
    OPTIMIZER_SERVICE_URL: str = "http://localhost:8007"
    AMP_SERVICE_URL: str = "http://localhost:8008"
    
    # Gemini API (for orchestrator and creative_service later)
    GEMINI_API_KEY: Optional[str] = None
    
    # Service ports (for running services)
    PRODUCT_SERVICE_PORT: int = 8001
    CREATIVE_SERVICE_PORT: int = 8002
    STRATEGY_SERVICE_PORT: int = 8003
    META_SERVICE_PORT: int = 8004
    LOGS_SERVICE_PORT: int = 8005
    SCHEMA_VALIDATOR_SERVICE_PORT: int = 8006
    OPTIMIZER_SERVICE_PORT: int = 8007
    AMP_SERVICE_PORT: int = 8008
    
    # General settings
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()




