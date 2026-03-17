"""
Client for strategy_service MCP.
"""
from typing import Dict, Any, List
from app.common.http_client import HTTPClient
from app.common.config import settings


class StrategyClient:
    """Client for interacting with the strategy service."""
    
    def __init__(self):
        self.client = HTTPClient(settings.STRATEGY_SERVICE_URL)
    
    async def generate_strategy(
        self,
        creatives: List[Dict[str, Any]],
        campaign_objective: str,
        budget: float,
        target_audience: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive ad strategy including platform-specific approaches.
        
        Args:
            creatives: List of creative objects
            campaign_objective: Campaign objective
            budget: Campaign budget
            target_audience: Optional audience information
            
        Returns:
            Dictionary with 'abstract_strategy' and 'platform_strategies'
        """
        payload = {
            "creatives": creatives,
            "campaign_objective": campaign_objective,
            "budget": budget
        }
        if target_audience:
            payload["target_audience"] = target_audience
        
        response = await self.client.post("/generate_strategy", payload)
        return response
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.close()




