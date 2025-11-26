"""
Common configuration module for the ad-campaign agent system.
Loads environment variables and provides centralized configuration.

Usage:
    - Local development: Uses default localhost URLs
    - Production deployment: Set environment variables to override URLs
    
Example for production (.env or environment variables):
    PRODUCT_SERVICE_URL=https://product-service.example.com
    CREATIVE_SERVICE_URL=https://creative-service.example.com
    # ... etc
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Service URLs:
        - Default values use localhost for local development
        - Override with environment variables for production deployment
        - Environment variables take precedence over defaults
    """
    
    # Service URLs - Default to localhost for local development
    # Override with environment variables for production
    PRODUCT_SERVICE_URL: str = "http://localhost:8001"
    CREATIVE_SERVICE_URL: str = "http://localhost:8002"
    STRATEGY_SERVICE_URL: str = "http://localhost:8003"
    META_SERVICE_URL: str = "http://localhost:8004"
    LOGS_SERVICE_URL: str = "http://localhost:8005"
    # SCHEMA_VALIDATOR_SERVICE_URL removed - validation now uses local Pydantic models
    # See app.common.validators for validation utilities
    OPTIMIZER_SERVICE_URL: str = "http://localhost:8007"
    
    # LLM settings (OpenAI is preferred, Gemini as fallback)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4.1-mini"  # OpenAI model for text generation
    
    # Gemini settings (fallback if OpenAI not available)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"  # Text generation model
    GEMINI_IMAGE_MODEL: str = "gemini-1.5-flash"  # Image generation model
    
    # General settings
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    
    # Database settings
    DATABASE_URL: Optional[str] = None
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow environment variables to override defaults
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
