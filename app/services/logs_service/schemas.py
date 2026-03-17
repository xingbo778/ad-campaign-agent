"""
Pydantic schemas for logs_service.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AppendEventRequest(BaseModel):
    """Request model for event logging."""
    event_type: str = Field(..., description="Type of event")
    service: str = Field(..., description="Service name that generated the event")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Event data")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")


class AppendEventResponse(BaseModel):
    """Response model for event logging."""
    status: str = Field(default="ok", description="Status of the log operation")




