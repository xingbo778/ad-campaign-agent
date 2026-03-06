"""
Lightweight circuit breaker for service-to-service calls.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is down, fail fast without calling
- HALF_OPEN: Allow one probe request to test recovery
"""

import time
from enum import Enum
from typing import Optional
from app.common.middleware import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit breaker that tracks failures per service and fails fast
    when a service is consistently down.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._last_success_time: Optional[float] = None

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self._last_failure_time and (time.time() - self._last_failure_time) >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker '{self.name}': OPEN → HALF_OPEN (recovery timeout elapsed)")
        return self._state

    def allow_request(self) -> bool:
        """Check if a request should be allowed."""
        current_state = self.state
        if current_state == CircuitState.CLOSED:
            return True
        if current_state == CircuitState.HALF_OPEN:
            return True  # Allow one probe request
        return False  # OPEN state - fail fast

    def record_success(self) -> None:
        """Record a successful call."""
        self._failure_count = 0
        self._last_success_time = time.time()
        if self._state != CircuitState.CLOSED:
            logger.info(f"Circuit breaker '{self.name}': {self._state.value} → CLOSED (success)")
            self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit breaker '{self.name}': HALF_OPEN → OPEN (probe failed)")
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit breaker '{self.name}': CLOSED → OPEN (threshold {self.failure_threshold} reached)")

    def __repr__(self) -> str:
        return f"CircuitBreaker(name={self.name}, state={self.state.value}, failures={self._failure_count})"


class CircuitBreakerRegistry:
    """Registry of circuit breakers for all services."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout

    def get(self, service_name: str) -> CircuitBreaker:
        """Get or create a circuit breaker for a service."""
        if service_name not in self._breakers:
            self._breakers[service_name] = CircuitBreaker(
                name=service_name,
                failure_threshold=self._failure_threshold,
                recovery_timeout=self._recovery_timeout,
            )
        return self._breakers[service_name]

    def status(self) -> dict[str, str]:
        """Get status of all circuit breakers."""
        return {name: cb.state.value for name, cb in self._breakers.items()}


class CircuitOpenError(Exception):
    """Raised when a circuit breaker is open and request is rejected."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Circuit breaker open for service: {service_name}")


# Global registry
circuit_breakers = CircuitBreakerRegistry()
