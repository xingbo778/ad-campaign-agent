"""
Common middleware and logging configuration for all services.

This module provides:
- Unified logging configuration with request ID tracking
- CORS middleware factory
- Request ID middleware for request tracing
"""

import logging
import uuid
import time
from typing import Optional
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextvars import ContextVar

# Context variable for request ID
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request ID to all requests for tracing.
    
    Adds X-Request-ID header to responses and makes request_id available
    in request.state for logging.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        request_id_context.set(request_id)
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        
        return response


class RequestIDFilter(logging.Filter):
    """Logging filter to add request ID to log records."""
    
    def filter(self, record):
        record.request_id = request_id_context.get() or "no-request-id"
        return True


def setup_logging(level: str = "INFO", service_name: Optional[str] = None):
    """
    Configure unified logging format for all services.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Optional service name to include in logs
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter with request ID support
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestIDFilter())
    root_logger.addHandler(console_handler)
    
    # Set service-specific logger if provided
    if service_name:
        service_logger = logging.getLogger(service_name)
        service_logger.setLevel(log_level)
        if not service_logger.handlers:
            service_handler = logging.StreamHandler()
            service_handler.setLevel(log_level)
            service_handler.setFormatter(formatter)
            service_handler.addFilter(RequestIDFilter())
            service_logger.addHandler(service_handler)


def get_cors_middleware_class(allowed_origins: Optional[list] = None):
    """
    Create CORS middleware with environment-aware configuration.
    
    Args:
        allowed_origins: List of allowed origins. If None, uses environment-based defaults.
    
    Returns:
        Factory function that creates CORSMiddleware
    """
    from app.common.config import settings
    
    if allowed_origins is None:
        # Development: allow all origins
        # Production: restrict to specific domains
        if settings.ENVIRONMENT == "development":
            allowed_origins = ["*"]
        else:
            # In production, specify allowed origins
            allowed_origins = [
                "https://yourdomain.com",
                "https://www.yourdomain.com"
            ]
    
    def create_cors_middleware(app):
        """Factory function to create CORS middleware"""
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID", "X-Process-Time"]
        )
        return app
    
    return create_cors_middleware


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with request ID support.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    # Ensure RequestIDFilter is applied
    if not any(isinstance(f, RequestIDFilter) for f in logger.filters):
        logger.addFilter(RequestIDFilter())
    return logger

