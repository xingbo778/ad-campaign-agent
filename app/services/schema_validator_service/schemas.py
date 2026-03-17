"""
Pydantic schemas for schema_validator_service.
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ValidateRequest(BaseModel):
    """Request model for schema validation."""
    schema_type: str = Field(
        ...,
        description="Type of schema: campaign, creative, strategy, or product"
    )
    data: Dict[str, Any] = Field(..., description="Data to validate")


class ValidateResponse(BaseModel):
    """Response model for schema validation."""
    valid: bool = Field(..., description="Whether the data is valid")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")




