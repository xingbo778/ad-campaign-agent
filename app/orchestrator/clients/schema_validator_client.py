"""
Client for schema_validator_service MCP.
"""
from typing import Dict, Any
from app.common.http_client import HTTPClient
from app.common.config import settings


class SchemaValidatorClient:
    """Client for interacting with the schema validator service."""
    
    def __init__(self):
        self.client = HTTPClient(settings.SCHEMA_VALIDATOR_SERVICE_URL)
    
    async def validate(
        self,
        schema_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate campaign data against schema requirements.
        
        Args:
            schema_type: One of 'campaign', 'creative', 'strategy', 'product'
            data: Data to validate
            
        Returns:
            Dictionary with 'valid' boolean and 'errors' list
        """
        payload = {
            "schema_type": schema_type,
            "data": data
        }
        
        response = await self.client.post("/validate", payload)
        return response
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.close()




