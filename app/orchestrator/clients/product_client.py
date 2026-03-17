"""
Client for product_service MCP.
"""
from typing import Dict, Any, List
from app.common.http_client import HTTPClient
from app.common.config import settings


class ProductClient:
    """Client for interacting with the product service."""
    
    def __init__(self):
        self.client = HTTPClient(settings.PRODUCT_SERVICE_URL)
    
    async def select_products(
        self,
        campaign_objective: str,
        target_audience: Dict[str, Any],
        budget_range: Dict[str, float] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Select and group products based on campaign requirements.
        
        Args:
            campaign_objective: One of 'awareness', 'conversions', 'engagement'
            target_audience: Audience demographics and interests
            budget_range: Optional budget constraints
            
        Returns:
            Dictionary with product_groups (high, medium, low priority)
        """
        payload = {
            "campaign_objective": campaign_objective,
            "target_audience": target_audience
        }
        if budget_range:
            payload["budget_range"] = budget_range
        
        response = await self.client.post("/select_products", payload)
        return response
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.close()




