"""
Client for amp_service MCP.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.common.http_client import HTTPClient
from app.common.config import settings


class AMPClient:
    """Client for interacting with the AMP service."""

    def __init__(self):
        self.client = HTTPClient(settings.AMP_SERVICE_URL)

    async def publish_to_amp(
        self,
        agent_creatives: List[Dict[str, Any]],
        budget: float,
        bidding_strategy: str = "cost_per_recommendation",
        target_agent_categories: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Publish product listings to the Agent Marketing Platform.

        Args:
            agent_creatives: List of agent creative objects
            budget: AMP channel budget
            bidding_strategy: Bidding model (cost_per_recommendation, cost_per_query_match, cost_per_action, flat_rate)
            target_agent_categories: Categories of agents to target
            start_date: Optional campaign start date
            end_date: Optional campaign end date

        Returns:
            Dictionary with 'campaign_id', 'listings', and 'status'
        """
        payload: Dict[str, Any] = {
            "agent_creatives": agent_creatives,
            "budget": budget,
            "bidding_strategy": bidding_strategy,
        }
        if target_agent_categories:
            payload["target_agent_categories"] = target_agent_categories
        if start_date:
            payload["start_date"] = start_date.isoformat()
        if end_date:
            payload["end_date"] = end_date.isoformat()

        response = await self.client.post("/publish_to_amp", payload)
        return response

    async def close(self):
        """Close the HTTP client."""
        await self.client.close()
