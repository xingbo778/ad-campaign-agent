"""
Client for interacting with the Optimizer Service.
"""

from typing import Dict, Any, List, Optional
from app.common.http_client import MCPClient
from app.common.config import settings


class OptimizerClient:
    """Client for the Optimizer Service MCP."""
    
    def __init__(self):
        """Initialize the optimizer service client."""
        self.client = MCPClient(settings.OPTIMIZER_SERVICE_URL)
    
    def summarize_recent_runs(
        self,
        campaign_ids: Optional[List[str]] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Summarize recent campaign performance and get optimization suggestions.
        
        Args:
            campaign_ids: Specific campaign IDs to analyze
            days: Number of days to look back
            
        Returns:
            Performance summary and optimization suggestions
        """
        request_data = {
            "days": days
        }
        
        if campaign_ids:
            request_data["campaign_ids"] = campaign_ids
        
        return self.client.post("/summarize_recent_runs", request_data)
    
    def close(self) -> None:
        """Close the client connection."""
        self.client.close()


if __name__ == "__main__":
    # Example usage
    from app.common.middleware import get_logger
    logger = get_logger(__name__)
    
    client = OptimizerClient()
    try:
        result = client.summarize_recent_runs(days=7)
        logger.info(f"Optimization summary: {result}")
    finally:
        client.close()
