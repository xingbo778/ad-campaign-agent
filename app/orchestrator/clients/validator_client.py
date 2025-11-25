"""
Validator client - now uses local validation instead of HTTP service.

This client has been refactored to use app.common.validators for fast,
in-process validation, eliminating the need for a separate HTTP service.
"""

from typing import Dict, Any
from app.common.validators import validate_data, ValidationResult


class ValidatorClient:
    """
    Validator client using local Pydantic validation.
    
    This replaces the HTTP-based schema_validator_service with fast,
    in-process validation using Pydantic models.
    """
    
    def __init__(self):
        """Initialize the validator client (no HTTP connection needed)."""
        pass
    
    def validate(
        self,
        schema_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate data against a schema using local Pydantic validation.
        
        Args:
            schema_name: Name of the schema to validate against
            data: Data to validate
            
        Returns:
            Validation result dictionary with 'valid' and 'errors' keys
        """
        result = validate_data(schema_name, data)
        return result.to_dict()
    
    def close(self) -> None:
        """Close the client (no-op for local validation)."""
        pass


if __name__ == "__main__":
    # Example usage
    from app.common.middleware import get_logger
    logger = get_logger(__name__)
    
    client = ValidatorClient()
    try:
        result = client.validate(
            schema_name="campaign",
            data={"name": "Test Campaign", "budget": 1000}
        )
        logger.info(f"Validation result: {result}")
    finally:
        client.close()
