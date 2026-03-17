"""
Mock data generators for logs_service.
"""
from app.services.logs_service.schemas import AppendEventResponse


def create_mock_response() -> AppendEventResponse:
    """
    Create a mock response for event logging.
    
    Returns:
        AppendEventResponse with status
    """
    return AppendEventResponse(status="ok")




