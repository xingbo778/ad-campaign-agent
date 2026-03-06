"""
Simple token bucket rate limiter for API and LLM calls.
"""

import time
import asyncio
from typing import Dict
from app.common.middleware import get_logger

logger = get_logger(__name__)


class TokenBucket:
    """
    Token bucket rate limiter.

    Allows `capacity` requests, refilling at `refill_rate` tokens/second.
    """

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now

    def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens. Returns True if allowed, False if rate limited."""
        self._refill()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, waiting if necessary."""
        while not self.try_acquire(tokens):
            # Calculate wait time
            deficit = tokens - self._tokens
            wait_time = deficit / self.refill_rate
            await asyncio.sleep(min(wait_time, 1.0))


class RateLimiterRegistry:
    """Registry of rate limiters for different resources."""

    def __init__(self):
        self._limiters: Dict[str, TokenBucket] = {}

    def get_or_create(self, name: str, capacity: int = 60, refill_rate: float = 1.0) -> TokenBucket:
        """Get or create a rate limiter."""
        if name not in self._limiters:
            self._limiters[name] = TokenBucket(capacity=capacity, refill_rate=refill_rate)
        return self._limiters[name]


# Global registry with default limiters
rate_limiters = RateLimiterRegistry()

# Pre-configure common limiters
api_limiter = rate_limiters.get_or_create("api", capacity=100, refill_rate=10.0)
llm_limiter = rate_limiters.get_or_create("llm", capacity=20, refill_rate=2.0)
