"""
Client for optimizer_service MCP.
"""
from typing import Dict, Any, List
from app.common.http_client import HTTPClient
from app.common.config import settings


class OptimizerClient:
    """Client for interacting with the optimizer service."""
    
    def __init__(self):
        self.client = HTTPClient(settings.OPTIMIZER_SERVICE_URL)
    
    async def summarize_recent_runs(
        self,
        campaign_ids: List[str],
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze recent campaign runs and provide optimization suggestions.
        
        Args:
            campaign_ids: List of campaign IDs to analyze
            lookback_days: Number of days to look back (default: 30)
            
        Returns:
            Dictionary with 'summary' and 'suggestions'
        """
        payload = {
            "campaign_ids": campaign_ids,
            "lookback_days": lookback_days
        }
        
        response = await self.client.post("/summarize_recent_runs", payload)
        return response
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.close()




