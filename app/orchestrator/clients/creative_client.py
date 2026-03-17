"""
Client for creative_service MCP.
"""
from typing import Dict, Any, List
from app.common.http_client import HTTPClient
from app.common.config import settings


class CreativeClient:
    """Client for interacting with the creative service."""
    
    def __init__(self):
        self.client = HTTPClient(settings.CREATIVE_SERVICE_URL)
    
    async def generate_creatives(
        self,
        products: List[Dict[str, Any]],
        campaign_objective: str,
        platform: str,
        target_audience: Dict[str, Any] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate ad creatives (text, images, videos) for campaigns.
        
        Args:
            products: List of product objects
            campaign_objective: Campaign objective
            platform: Target platform ('facebook', 'instagram', 'meta')
            target_audience: Optional audience information
            
        Returns:
            Dictionary with 'creatives' list containing creative objects
        """
        payload = {
            "products": products,
            "campaign_objective": campaign_objective,
            "platform": platform
        }
        if target_audience:
            payload["target_audience"] = target_audience
        
        response = await self.client.post("/generate_creatives", payload)
        return response
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.close()




