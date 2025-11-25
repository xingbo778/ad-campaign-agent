"""
Pydantic schemas for the logs service.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


class AppendEventRequest(BaseModel):
    """Request to append an event to logs."""
    # Use LogEvent from common/schemas.py
    event_id: Optional[str] = Field(None, description="Optional event ID")
    timestamp: str = Field(..., description="Event timestamp (ISO format)")
    stage: str = Field(..., description="Workflow stage")
    service: str = Field(..., description="Service name")
    request: Optional[Dict[str, Any]] = Field(None, description="Request data")
    response: Optional[Dict[str, Any]] = Field(None, description="Response data")
    success: bool = Field(..., description="Whether operation was successful")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AppendEventResponse(BaseModel):
    """Response after appending an event."""
    status: str = Field(..., description="Operation status")
    event_id: Optional[str] = Field(None, description="Event ID if created")


class QueryLogsResponse(BaseModel):
    """Response for log query."""
    status: str = Field(..., description="Operation status")
    logs: List[Dict[str, Any]] = Field(..., description="List of log events")
    pagination: Dict[str, int] = Field(..., description="Pagination metadata")


class AnalyticsResponse(BaseModel):
    """Response for analytics query."""
    status: str = Field(..., description="Operation status")
    by_stage: Dict[str, int] = Field(..., description="Count by stage")
    by_service: Dict[str, int] = Field(..., description="Count by service")
    levels: Dict[str, int] = Field(..., description="Count by log level")
