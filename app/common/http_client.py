"""
HTTP client utilities for making requests to MCP services.
"""
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HTTPClient:
    """Simple HTTP client for MCP service communication."""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize HTTP client.
        
        Args:
            base_url: Base URL of the service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make a POST request to the service.
        
        Args:
            endpoint: API endpoint (e.g., "/select_products")
            data: Request body as dictionary
            headers: Optional headers
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)
        
        try:
            response = await self.client.post(url, json=data, headers=default_headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling {url}: {e}")
            raise
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request to the service.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Optional headers
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        default_headers = {}
        if headers:
            default_headers.update(headers)
        
        try:
            response = await self.client.get(url, params=params, headers=default_headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling {url}: {e}")
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()




