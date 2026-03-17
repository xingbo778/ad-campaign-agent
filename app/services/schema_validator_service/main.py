"""
Schema Validator Service - FastAPI app for data schema validation.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.services.schema_validator_service.schemas import (
    ValidateRequest,
    ValidateResponse
)
from app.services.schema_validator_service.mock_data import create_mock_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Schema Validator Service",
    description="MCP service for data schema validation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/validate", response_model=ValidateResponse)
async def validate(request: ValidateRequest) -> ValidateResponse:
    """
    Validate campaign data against schema requirements.
    
    This endpoint validates data structures against predefined schemas
    for campaigns, creatives, strategies, and products.
    
    TODO: Replace mock implementation with:
    - JSON Schema validation (jsonschema library)
    - Custom validation rules
    - Business logic validation
    - Cross-field validation
    - Platform-specific schema validation
    - Detailed error messages with field paths
    
    Args:
        request: ValidateRequest with schema_type and data
        
    Returns:
        ValidateResponse with validation result and errors
    """
    logger.info(f"Validating {request.schema_type} schema")
    
    # TODO: Implement real validation logic
    # - Load schema definition for schema_type
    # - Validate data against JSON Schema
    # - Apply custom business rules
    # - Check cross-field constraints
    # - Return detailed error messages
    
    # For now, return mock validation (always valid)
    response = create_mock_response()
    
    logger.info(f"Validation result: valid={response.valid}, errors={len(response.errors)}")
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "schema_validator_service"}


if __name__ == "__main__":
    import uvicorn
    from app.common.config import settings
    
    uvicorn.run(
        "app.services.schema_validator_service.main:app",
        host="0.0.0.0",
        port=settings.SCHEMA_VALIDATOR_SERVICE_PORT,
        reload=settings.DEBUG
    )




