"""
Shared validation utilities for the Advertising Campaign Agent system.

This module provides validation functions that can be used directly within services,
avoiding the overhead of HTTP calls for data validation.

All validation uses Pydantic models from app.common.schemas, leveraging FastAPI's
built-in validation mechanisms.
"""

from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, ValidationError
import logging

from .schemas import (
    CampaignSpec,
    Product,
    ProductGroup,
    Creative,
    AbstractStrategy,
    PlatformStrategy,
    ErrorResponse,
    LogEvent,
)

logger = logging.getLogger(__name__)

# Schema mapping for validation
SCHEMA_MODELS: Dict[str, Type[BaseModel]] = {
    "campaign_spec": CampaignSpec,
    "product": Product,
    "product_group": ProductGroup,
    "creative": Creative,
    "abstract_strategy": AbstractStrategy,
    "platform_strategy": PlatformStrategy,
    "error_response": ErrorResponse,
    "log_event": LogEvent,
}


class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(self, valid: bool, errors: List[Dict[str, Any]] = None):
        self.valid = valid
        self.errors = errors or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "valid": self.valid,
            "errors": self.errors
        }


def validate_data(schema_name: str, data: Dict[str, Any]) -> ValidationResult:
    """
    Validate data against a schema using Pydantic models.
    
    This function replaces the HTTP-based schema_validator_service,
    providing fast, in-process validation.
    
    Args:
        schema_name: Name of the schema to validate against
        data: Data dictionary to validate
        
    Returns:
        ValidationResult with validation status and any errors
        
    Example:
        >>> from app.common.middleware import get_logger
        >>> logger = get_logger(__name__)
        >>> result = validate_data("campaign_spec", {"platform": "meta", "budget": 1000})
        >>> if result.valid:
        ...     logger.info("Validation passed")
    """
    if schema_name not in SCHEMA_MODELS:
        logger.warning(f"Unknown schema name: {schema_name}")
        return ValidationResult(
            valid=False,
            errors=[{
                "field": "schema_name",
                "error": f"Unknown schema: {schema_name}",
                "value": schema_name
            }]
        )
    
    model_class = SCHEMA_MODELS[schema_name]
    
    try:
        # Attempt to create model instance - Pydantic will validate
        instance = model_class(**data)
        logger.debug(f"Validation passed for schema: {schema_name}")
        return ValidationResult(valid=True, errors=[])
    
    except ValidationError as e:
        # Extract validation errors
        errors = []
        for error in e.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error.get("loc", [])),
                "error": error.get("msg", "Validation error"),
                "value": error.get("input")
            })
        
        logger.warning(f"Validation failed for schema {schema_name}: {len(errors)} errors")
        return ValidationResult(valid=False, errors=errors)
    
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}", exc_info=True)
        return ValidationResult(
            valid=False,
            errors=[{
                "field": "validation",
                "error": f"Unexpected validation error: {str(e)}",
                "value": None
            }]
        )


def validate_campaign_spec(data: Dict[str, Any]) -> ValidationResult:
    """Convenience function to validate CampaignSpec."""
    return validate_data("campaign_spec", data)


def validate_product(data: Dict[str, Any]) -> ValidationResult:
    """Convenience function to validate Product."""
    return validate_data("product", data)


def validate_creative(data: Dict[str, Any]) -> ValidationResult:
    """Convenience function to validate Creative."""
    return validate_data("creative", data)


def validate_list(schema_name: str, data_list: List[Dict[str, Any]]) -> ValidationResult:
    """
    Validate a list of items against a schema.
    
    Args:
        schema_name: Name of the schema to validate against
        data_list: List of data dictionaries to validate
        
    Returns:
        ValidationResult with validation status and all errors
    """
    all_errors = []
    all_valid = True
    
    for idx, item in enumerate(data_list):
        result = validate_data(schema_name, item)
        if not result.valid:
            all_valid = False
            # Prefix errors with index
            for error in result.errors:
                error["field"] = f"[{idx}].{error['field']}"
                all_errors.append(error)
    
    return ValidationResult(valid=all_valid, errors=all_errors)

