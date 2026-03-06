"""Tool wrapper for the Logs Service."""

from typing import Any, Dict
from app.agent.tool import BaseTool
from app.common.config import settings
from app.common.http_client import AsyncMCPClient


class AppendEventTool(BaseTool):
    name = "append_event"
    description = "Log an event for auditing and monitoring."
    parameters = {
        "type": "object",
        "properties": {
            "event_type": {"type": "string", "description": "Type of event (e.g., campaign_created)"},
            "message": {"type": "string", "description": "Event message"},
            "metadata": {"type": "object", "description": "Additional event metadata"},
        },
        "required": ["event_type", "message"],
    }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        async with AsyncMCPClient(settings.LOGS_SERVICE_URL, timeout=settings.SERVICE_TIMEOUT) as client:
            return await client.post("/append_event", kwargs)
