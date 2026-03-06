"""Tool wrapper for the Meta Service."""

from typing import Any, Dict
from app.agent.tool import BaseTool
from app.common.config import settings
from app.common.http_client import AsyncMCPClient


class CreateCampaignTool(BaseTool):
    name = "create_campaign"
    description = "Deploy a campaign to Meta platforms (Facebook/Instagram). This is a high-risk action."
    parameters = {
        "type": "object",
        "properties": {
            "campaign_name": {"type": "string", "description": "Campaign name"},
            "objective": {"type": "string", "description": "Campaign objective"},
            "budget": {"type": "number", "description": "Campaign budget"},
            "target_audience": {"type": "string", "description": "Target audience description"},
            "creatives": {"type": "array", "description": "List of creative IDs to use"},
        },
        "required": ["campaign_name", "objective", "budget"],
    }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        async with AsyncMCPClient(settings.META_SERVICE_URL, timeout=settings.SERVICE_TIMEOUT) as client:
            return await client.post("/create_campaign", kwargs)
