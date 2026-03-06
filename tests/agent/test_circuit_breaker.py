"""Tests for circuit breaker and rate limiter."""

import time
import pytest
from app.common.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerRegistry, CircuitOpenError


class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED

    def test_allows_request_when_closed(self):
        cb = CircuitBreaker("test")
        assert cb.allow_request() is True

    def test_opens_after_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False

    def test_stays_closed_below_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=5)
        for _ in range(4):
            cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        cb.record_failure()
        cb.record_failure()
        # Should still be closed because success reset the count
        assert cb.state == CircuitState.CLOSED

    def test_half_open_after_recovery_timeout(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.01)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.allow_request() is True

    def test_half_open_success_closes(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.01)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_failure_reopens(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.01)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_failure()
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerRegistry:
    def test_get_creates_new(self):
        registry = CircuitBreakerRegistry()
        cb = registry.get("service_a")
        assert isinstance(cb, CircuitBreaker)
        assert cb.name == "service_a"

    def test_get_returns_same_instance(self):
        registry = CircuitBreakerRegistry()
        cb1 = registry.get("service_a")
        cb2 = registry.get("service_a")
        assert cb1 is cb2

    def test_status(self):
        registry = CircuitBreakerRegistry(failure_threshold=2)
        cb = registry.get("failing_service")
        cb.record_failure()
        cb.record_failure()
        status = registry.status()
        assert status["failing_service"] == "open"


class TestCircuitOpenError:
    def test_error_message(self):
        error = CircuitOpenError("my_service")
        assert "my_service" in str(error)
        assert error.service_name == "my_service"
