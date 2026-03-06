"""Tool wrapper for the Product Service."""

from typing import Any, Dict
from app.agent.tool import BaseTool
from app.common.config import settings
from app.common.http_client import AsyncMCPClient


class SelectProductsTool(BaseTool):
    name = "select_products"
    description = "Select and score products for an ad campaign based on objectives, budget, and category."
    parameters = {
        "type": "object",
        "properties": {
            "campaign_spec": {
                "type": "object",
                "description": "Campaign specification with fields: user_query, platform, budget, objective, category",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of products to return",
            },
        },
        "required": ["campaign_spec"],
    }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        async with AsyncMCPClient(settings.PRODUCT_SERVICE_URL, timeout=settings.SERVICE_TIMEOUT) as client:
            return await client.post("/select_products", kwargs)
