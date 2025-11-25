"""
Client for interacting with the Meta Service.
"""

from typing import Dict, Any, List, Optional
from app.common.http_client import MCPClient
from app.common.config import settings


class MetaClient:
    """Client for the Meta Service MCP."""
    
    def __init__(self):
        """Initialize the meta service client."""
        self.client = MCPClient(settings.META_SERVICE_URL)
    
    def create_campaign(
        self,
        campaign_name: str,
        objective: str,
        daily_budget: float,
        targeting: Dict[str, Any],
        creatives: List[Dict[str, Any]],
        start_date: str,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a campaign on Meta platforms.
        
        Args:
            campaign_name: Campaign name
            objective: Campaign objective
            daily_budget: Daily budget
            targeting: Targeting criteria
            creatives: Ad creatives to use
            start_date: Campaign start date (ISO format)
            end_date: Campaign end date (ISO format)
            
        Returns:
            Created campaign, ad set, and ad IDs
        """
        request_data = {
            "campaign_name": campaign_name,
            "objective": objective,
            "daily_budget": daily_budget,
            "targeting": targeting,
            "creatives": creatives,
            "start_date": start_date
        }
        
        if end_date:
            request_data["end_date"] = end_date
        
        return self.client.post("/create_campaign", request_data)
    
    def close(self) -> None:
        """Close the client connection."""
        self.client.close()


if __name__ == "__main__":
    # Example usage
    from app.common.middleware import get_logger
    logger = get_logger(__name__)
    
    client = MetaClient()
    try:
        result = client.create_campaign(
            campaign_name="Test Campaign",
            objective="CONVERSIONS",
            daily_budget=100.0,
            targeting={"age_range": "25-45", "location": "US"},
            creatives=[
                {
                    "creative_id": "CREATIVE-001",
                    "headline": "Test Headline",
                    "body_text": "Test Body",
                    "call_to_action": "Shop Now"
                }
            ],
            start_date="2024-01-01T00:00:00Z"
        )
        logger.info(f"Created campaign: {result}")
    finally:
        client.close()
