"""
Client for interacting with the Logs Service.
"""

from typing import Dict, Any, Optional
from app.common.http_client import MCPClient
from app.common.config import settings


class LogsClient:
    """Client for the Logs Service MCP."""
    
    def __init__(self):
        """Initialize the logs service client."""
        self.client = MCPClient(settings.LOGS_SERVICE_URL)
    
    def append_event(
        self,
        event_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Append an event to the logs.
        
        Args:
            event_type: Type of event
            message: Event message
            metadata: Additional event metadata
            campaign_id: Associated campaign ID
            
        Returns:
            Status and event ID
        """
        request_data = {
            "event_type": event_type,
            "message": message
        }
        
        if metadata:
            request_data["metadata"] = metadata
        if campaign_id:
            request_data["campaign_id"] = campaign_id
        
        return self.client.post("/append_event", request_data)
    
    def close(self) -> None:
        """Close the client connection."""
        self.client.close()


if __name__ == "__main__":
    # Example usage
    from app.common.middleware import get_logger
    logger = get_logger(__name__)
    
    client = LogsClient()
    try:
        result = client.append_event(
            event_type="campaign_created",
            message="Campaign created successfully",
            campaign_id="CAMP-123"
        )
        logger.info(f"Event logged: {result}")
    finally:
        client.close()
