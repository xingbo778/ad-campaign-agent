"""Tool wrapper for the Optimizer Service."""

from typing import Any, Dict
from app.agent.tool import BaseTool
from app.common.config import settings
from app.common.http_client import AsyncMCPClient


class SummarizeRunsTool(BaseTool):
    name = "summarize_recent_runs"
    description = "Analyze recent campaign performance and get optimization suggestions."
    parameters = {
        "type": "object",
        "properties": {
            "campaign_ids": {"type": "array", "description": "Campaign IDs to analyze"},
            "days": {"type": "integer", "description": "Number of days to look back"},
        },
    }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        async with AsyncMCPClient(settings.OPTIMIZER_SERVICE_URL, timeout=settings.SERVICE_TIMEOUT) as client:
            return await client.post("/summarize_recent_runs", kwargs)
