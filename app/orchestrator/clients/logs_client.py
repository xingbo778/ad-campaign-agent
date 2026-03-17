"""
Client for logs_service MCP.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from app.common.http_client import HTTPClient
from app.common.config import settings


class LogsClient:
    """Client for interacting with the logs service."""
    
    def __init__(self):
        self.client = HTTPClient(settings.LOGS_SERVICE_URL)
    
    async def append_event(
        self,
        event_type: str,
        service: str,
        data: Dict[str, Any] = None,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, str]:
        """
        Log events and operations for audit trails.
        
        Args:
            event_type: Type of event (e.g., 'campaign_created', 'creative_generated')
            service: Service name that generated the event
            data: Optional event data
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            Dictionary with 'status' field
        """
        payload = {
            "event_type": event_type,
            "service": service,
            "data": data or {}
        }
        if timestamp:
            payload["timestamp"] = timestamp.isoformat()
        else:
            payload["timestamp"] = datetime.utcnow().isoformat()
        
        response = await self.client.post("/append_event", payload)
        return response
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.close()




