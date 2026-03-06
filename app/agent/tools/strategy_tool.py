"""Tool wrapper for the Strategy Service."""

from typing import Any, Dict
from app.agent.tool import BaseTool
from app.common.config import settings
from app.common.http_client import AsyncMCPClient


class GenerateStrategyTool(BaseTool):
    name = "generate_strategy"
    description = "Generate campaign strategy including budget allocation, targeting, bidding, and adset structure."
    parameters = {
        "type": "object",
        "properties": {
            "campaign_spec": {
                "type": "object",
                "description": "Campaign specification",
            },
        },
        "required": ["campaign_spec"],
    }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        async with AsyncMCPClient(settings.STRATEGY_SERVICE_URL, timeout=settings.SERVICE_TIMEOUT) as client:
            return await client.post("/generate_strategy", kwargs)
