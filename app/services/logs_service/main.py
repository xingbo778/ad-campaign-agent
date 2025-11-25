"""
Logs Service - MCP microservice for event logging and auditing.

This service handles logging of all campaign-related events for monitoring and debugging.
"""

from fastapi import FastAPI, HTTPException
import sys
import os
import uuid

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.common.middleware import setup_logging, RequestIDMiddleware, get_cors_middleware_class, get_logger
from app.common.config import settings
from app.common.exceptions import register_exception_handlers

from .schemas import AppendEventRequest, AppendEventResponse

# Configure unified logging
setup_logging(level=settings.LOG_LEVEL, service_name="logs_service")
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Logs Service",
    description="MCP microservice for event logging and auditing",
    version="1.0.0"
)

# Add middleware
app.add_middleware(RequestIDMiddleware)
cors_middleware = get_cors_middleware_class()
cors_middleware(app)

# Register exception handlers
register_exception_handlers(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "logs_service"}


@app.post("/append_event", response_model=AppendEventResponse)
async def append_event(request: AppendEventRequest):
    """
    Append an event to the logs.
    
    Args:
        request: Event data to log
        
    Returns:
        Status and event ID
        
    TODO: Implement real logging infrastructure:
    - Store events in a database (PostgreSQL, MongoDB, etc.)
    - Integrate with logging platforms (ELK, Datadog, etc.)
    - Implement log retention policies
    - Add search and filtering capabilities
    - Set up alerting for critical events
    """
    logger.info(f"Logging event: type={request.event_type}, message={request.message}, "
                f"campaign_id={request.campaign_id}")
    
    # Generate mock event ID
    event_id = f"EVENT-{uuid.uuid4().hex[:12].upper()}"
    
    # In production, this would write to a database or logging service
    logger.info(f"Event logged with ID: {event_id}")
    
    return AppendEventResponse(
        status="ok",
        event_id=event_id
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
