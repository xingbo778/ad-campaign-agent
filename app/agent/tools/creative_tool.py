"""Tool wrapper for the Creative Service."""

from typing import Any, Dict
from app.agent.tool import BaseTool
from app.common.config import settings
from app.common.http_client import AsyncMCPClient


class GenerateCreativesTool(BaseTool):
    name = "generate_creatives"
    description = "Generate ad creatives (headlines, copy, images) for selected products with A/B variants."
    parameters = {
        "type": "object",
        "properties": {
            "campaign_spec": {
                "type": "object",
                "description": "Campaign specification",
            },
            "products": {
                "type": "array",
                "description": "List of product objects to generate creatives for",
            },
            "ab_config": {
                "type": "object",
                "description": "A/B test config: variants_per_product, max_creatives, enable_image_generation",
            },
        },
        "required": ["campaign_spec", "products"],
    }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        if "ab_config" not in kwargs:
            kwargs["ab_config"] = {"variants_per_product": 2, "max_creatives": 10, "enable_image_generation": True}
        async with AsyncMCPClient(settings.CREATIVE_SERVICE_URL, timeout=settings.SERVICE_TIMEOUT) as client:
            return await client.post("/generate_creatives", kwargs)
