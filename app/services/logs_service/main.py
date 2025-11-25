"""
Logs Service - MCP microservice for event logging and auditing.

This service implements real logging infrastructure with:
- Database persistence (PostgreSQL)
- File-based logging (JSON format, rotating)
- Query and analytics APIs
"""

from fastapi import FastAPI, Query, HTTPException
from typing import Optional, Union
from datetime import datetime
from app.common.middleware import setup_logging, RequestIDMiddleware, get_cors_middleware_class, get_logger
from app.common.config import settings
from app.common.exceptions import register_exception_handlers, ServiceException
from app.common.schemas import ErrorResponse
from app.common.db import init_db, is_db_available, create_tables

from .schemas import AppendEventRequest, AppendEventResponse, QueryLogsResponse, AnalyticsResponse
from .repository import LogEventRepository
from .logger_config import setup_file_logging, log_event_to_file

# Configure unified logging
setup_logging()
logger = get_logger(__name__)

# Set up file logging
file_logger = setup_file_logging()

# Initialize database connection (if available)
db_available = init_db()
if db_available:
    logger.info("Database connection initialized for logs service")
    # Create tables if they don't exist
    create_tables()
else:
    logger.info("Database not available, using file-only logging")

# Initialize FastAPI app
app = FastAPI(
    title="Logs Service",
    description="MCP microservice for event logging and auditing",
    version="2.0.0"
)

# Add middleware
app.add_middleware(RequestIDMiddleware)
cors_middleware = get_cors_middleware_class(settings.ENVIRONMENT)
cors_middleware(app)

# Register exception handlers
register_exception_handlers(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "logs_service",
        "data_source": "database" if is_db_available() else "file_only"
    }


@app.post("/append_event", response_model=Union[AppendEventResponse, ErrorResponse])
async def append_event(request: AppendEventRequest) -> Union[AppendEventResponse, ErrorResponse]:
    """
    Append an event to the logs.
    
    This endpoint:
    1. Writes to database (if available)
    2. Writes to rotating log file (JSON format)
    3. Returns event ID
    
    Args:
        request: Event data to log (LogEvent format)
        
    Returns:
        Event ID and status
    """
    try:
        # Parse timestamp
        try:
            event_timestamp = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            event_timestamp = datetime.utcnow()
            logger.warning(f"Invalid timestamp format, using current time: {request.timestamp}")
        
        # Determine log level from success flag
        level = "INFO" if request.success else "ERROR"
        
        # Merge context (request, response, metadata)
        context = {}
        if request.request:
            context["request"] = request.request
        if request.response:
            context["response"] = request.response
        if request.metadata:
            context["metadata"] = request.metadata
        
        # Extract message from context or use default
        message = "Event logged"
        if request.metadata and "message" in request.metadata:
            message = request.metadata["message"]
        elif request.response and "message" in request.response:
            message = request.response["message"]
        
        # Extract correlation_id from metadata if present
        correlation_id = None
        if request.metadata and "correlation_id" in request.metadata:
            correlation_id = request.metadata["correlation_id"]
        elif request.metadata and "request_id" in request.metadata:
            correlation_id = request.metadata["request_id"]
        
        # Write to database
        event_id = None
        if is_db_available():
            event_id = LogEventRepository.create_log_event(
                timestamp=event_timestamp,
                stage=request.stage,
                service=request.service,
                level=level,
                message=message,
                context=context,
                correlation_id=correlation_id,
                success=request.success
            )
        
        # Write to file
        log_event_to_file(
            logger=file_logger,
            timestamp=request.timestamp,
            stage=request.stage,
            service=request.service,
            level=level,
            message=message,
            context=context,
            correlation_id=correlation_id
        )
        
        logger.info(
            f"Logged event: stage={request.stage}, service={request.service}, "
            f"success={request.success}, event_id={event_id}"
        )
        
        return AppendEventResponse(
            status="success",
            event_id=event_id or request.event_id
        )
        
    except Exception as e:
        logger.error(f"Error appending event: {e}", exc_info=True)
        return ErrorResponse(
            status="error",
            error_code="LOG_APPEND_FAILED",
            message=f"Failed to append log event: {str(e)}",
            details={"error_type": type(e).__name__}
        )


@app.get("/logs", response_model=Union[QueryLogsResponse, ErrorResponse])
async def query_logs(
    stage: Optional[str] = Query(None, description="Filter by workflow stage"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    level: Optional[str] = Query(None, description="Filter by log level (INFO, ERROR, WARNING)"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
) -> Union[QueryLogsResponse, ErrorResponse]:
    """
    Query log events with filters.
    
    Supports filtering by:
    - stage: Workflow stage
    - service: Service name
    - correlation_id: Correlation ID for request tracking
    - level: Log level (INFO, ERROR, WARNING)
    - start_time/end_time: Time range (ISO format)
    
    Returns paginated results.
    """
    try:
        # Parse time filters
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return ErrorResponse(
                    status="error",
                    error_code="INVALID_START_TIME",
                    message=f"Invalid start_time format: {start_time}",
                    details={}
                )
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return ErrorResponse(
                    status="error",
                    error_code="INVALID_END_TIME",
                    message=f"Invalid end_time format: {end_time}",
                    details={}
                )
        
        # Query logs
        logs, total_count = LogEventRepository.query_logs(
            stage=stage,
            service=service,
            correlation_id=correlation_id,
            level=level,
            start_time=start_dt,
            end_time=end_dt,
            limit=limit,
            offset=offset
        )
        
        logger.info(
            f"Queried logs: {len(logs)} results (total: {total_count}), "
            f"filters: stage={stage}, service={service}, correlation_id={correlation_id}"
        )
        
        return QueryLogsResponse(
            status="success",
            logs=logs,
            pagination={
                "limit": limit,
                "offset": offset,
                "returned": len(logs),
                "total": total_count
            }
        )
        
    except Exception as e:
        logger.error(f"Error querying logs: {e}", exc_info=True)
        return ErrorResponse(
            status="error",
            error_code="LOG_QUERY_FAILED",
            message=f"Failed to query logs: {str(e)}",
            details={"error_type": type(e).__name__}
        )


@app.get("/analytics", response_model=Union[AnalyticsResponse, ErrorResponse])
async def get_analytics() -> Union[AnalyticsResponse, ErrorResponse]:
    """
    Get aggregated analytics from log events.
    
    Returns counts by:
    - stage: Number of logs per workflow stage
    - service: Number of logs per service
    - levels: Number of logs per log level (INFO, ERROR, WARNING)
    """
    try:
        analytics = LogEventRepository.get_analytics()
        
        logger.info(f"Generated analytics: {sum(analytics['levels'].values())} total logs")
        
        return AnalyticsResponse(
            status="success",
            by_stage=analytics["by_stage"],
            by_service=analytics["by_service"],
            levels=analytics["levels"]
        )
        
    except Exception as e:
        logger.error(f"Error generating analytics: {e}", exc_info=True)
        return ErrorResponse(
            status="error",
            error_code="ANALYTICS_FAILED",
            message=f"Failed to generate analytics: {str(e)}",
            details={"error_type": type(e).__name__}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
