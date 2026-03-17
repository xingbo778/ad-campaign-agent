"""
Client for meta_service MCP.
"""
from typing import Dict, Any, List
from datetime import datetime
from app.common.http_client import HTTPClient
from app.common.config import settings


class MetaClient:
    """Client for interacting with the meta service."""
    
    def __init__(self):
        self.client = HTTPClient(settings.META_SERVICE_URL)
    
    async def create_campaign(
        self,
        strategy: Dict[str, Any],
        creatives: List[Dict[str, Any]],
        budget: float,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Create and deploy campaigns to Meta platforms.
        
        Args:
            strategy: Strategy object
            creatives: List of creative objects
            budget: Campaign budget
            start_date: Optional campaign start date
            end_date: Optional campaign end date
            
        Returns:
            Dictionary with 'campaign_id' and 'ad_ids'
        """
        payload = {
            "strategy": strategy,
            "creatives": creatives,
            "budget": budget
        }
        if start_date:
            payload["start_date"] = start_date.isoformat()
        if end_date:
            payload["end_date"] = end_date.isoformat()
        
        response = await self.client.post("/create_campaign", payload)
        return response
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.close()




