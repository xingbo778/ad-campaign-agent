"""
Mock data generators for schema_validator_service.
"""
from app.services.schema_validator_service.schemas import ValidateResponse


def create_mock_response() -> ValidateResponse:
    """
    Create a mock response for schema validation.
    
    Returns:
        ValidateResponse with valid=True and empty errors
    """
    return ValidateResponse(valid=True, errors=[])




