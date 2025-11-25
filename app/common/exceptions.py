"""
Unified exception handling for all services.

Provides standard exception classes and global exception handlers
for consistent error responses across all services.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.common.schemas import ErrorResponse
from app.common.middleware import get_logger
from typing import Optional, Dict, Any

logger = get_logger(__name__)


class ServiceException(Exception):
    """
    Base exception class for service-specific errors.
    
    All service exceptions should inherit from this class to ensure
    consistent error response format.
    """
    
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize service exception.
        
        Args:
            error_code: Machine-readable error code (e.g., "PRODUCT_NOT_FOUND")
            message: Human-readable error message
            status_code: HTTP status code (default: 500)
            details: Additional error context
        """
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(ServiceException):
    """Exception for resource not found errors (404)."""
    
    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict] = None):
        super().__init__(
            error_code=f"{resource_type.upper()}_NOT_FOUND",
            message=f"{resource_type} with ID '{resource_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {"resource_type": resource_type, "resource_id": resource_id}
        )


class ValidationError(ServiceException):
    """Exception for validation errors (422)."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=error_details
        )


class ExternalServiceError(ServiceException):
    """Exception for external service call failures (502)."""
    
    def __init__(self, service_name: str, message: str, details: Optional[Dict] = None):
        super().__init__(
            error_code=f"{service_name.upper()}_SERVICE_ERROR",
            message=f"Error calling {service_name} service: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details or {"service": service_name}
        )


class AuthenticationError(ServiceException):
    """Exception for authentication failures (401)."""
    
    def __init__(self, message: str = "Authentication required", details: Optional[Dict] = None):
        super().__init__(
            error_code="AUTHENTICATION_ERROR",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details or {}
        )


class AuthorizationError(ServiceException):
    """Exception for authorization failures (403)."""
    
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict] = None):
        super().__init__(
            error_code="AUTHORIZATION_ERROR",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details or {}
        )


async def service_exception_handler(request: Request, exc: ServiceException):
    """
    Handler for ServiceException and its subclasses.
    
    Returns standardized error response format.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        f"[{request_id}] Service error: {exc.error_code} - {exc.message}",
        extra={"error_code": exc.error_code, "details": exc.details}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status="error",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details
        ).model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for Pydantic validation errors.
    
    Converts FastAPI validation errors to standardized format.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        f"[{request_id}] Validation error: {exc.errors()}",
        extra={"errors": exc.errors()}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            status="error",
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": exc.errors()}
        ).model_dump()
    )


async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unexpected errors.
    
    Catches all unhandled exceptions and returns standardized error response.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"[{request_id}] Unexpected error: {exc}",
        exc_info=True,
        extra={"exception_type": type(exc).__name__}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            status="error",
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again later.",
            details={
                "request_id": request_id,
                "exception_type": type(exc).__name__
            }
        ).model_dump()
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(ServiceException, service_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

