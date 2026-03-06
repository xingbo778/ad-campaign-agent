"""
Common HTTP client utilities for making requests to MCP services.

Supports both synchronous and asynchronous clients with circuit breaker
integration for resilience.
"""

import httpx
from typing import Any, Dict, Optional
from app.common.middleware import get_logger
from app.common.circuit_breaker import circuit_breakers, CircuitOpenError

logger = get_logger(__name__)


class MCPClient:
    """
    Synchronous HTTP client for communicating with MCP microservices.
    
    For orchestrator services, use AsyncMCPClient instead for better performance.
    """
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the MCP client.
        
        Args:
            base_url: Base URL of the MCP service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request to the MCP service.
        
        Args:
            endpoint: API endpoint path
            data: Request payload
            
        Returns:
            Response data as dictionary
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        logger.info(f"POST {url}")
        
        try:
            response = self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling {url}: {e}")
            raise
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request to the MCP service.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        logger.info(f"GET {url}")
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling {url}: {e}")
            raise
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncMCPClient:
    """
    Asynchronous HTTP client for communicating with MCP microservices.

    Includes circuit breaker integration: if a service fails repeatedly,
    subsequent calls fail fast without making HTTP requests.
    """

    def __init__(self, base_url: str, timeout: float = 30.0, service_name: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.service_name = service_name or self.base_url
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _check_circuit(self) -> None:
        """Check circuit breaker before making a request."""
        cb = circuit_breakers.get(self.service_name)
        if not cb.allow_request():
            raise CircuitOpenError(self.service_name)

    def _record_success(self) -> None:
        circuit_breakers.get(self.service_name).record_success()

    def _record_failure(self) -> None:
        circuit_breakers.get(self.service_name).record_failure()

    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make an async POST request with circuit breaker protection."""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout)

        self._check_circuit()
        url = f"{self.base_url}{endpoint}"
        logger.info(f"POST {url}")

        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            self._record_success()
            return response.json()
        except httpx.HTTPError as e:
            self._record_failure()
            logger.error(f"HTTP error calling {url}: {e}")
            raise

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an async GET request with circuit breaker protection."""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout)

        self._check_circuit()
        url = f"{self.base_url}{endpoint}"
        logger.info(f"GET {url}")

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            self._record_success()
            return response.json()
        except httpx.HTTPError as e:
            self._record_failure()
            logger.error(f"HTTP error calling {url}: {e}")
            raise

    async def close(self):
        """Close the async HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
