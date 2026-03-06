"""
Metrics collector for Agent tool calls, latency, and token usage.

Provides per-tool and aggregate statistics for observability.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List
from app.common.middleware import get_logger

logger = get_logger(__name__)


@dataclass
class ToolMetric:
    """Metrics for a single tool call."""
    tool_name: str
    duration_ms: float
    success: bool
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """
    Collects and reports agent metrics.

    Tracks:
    - Per-tool call count, success rate, latency (p50/p95/p99)
    - Total token usage (input/output)
    - Agent run count and duration
    """

    def __init__(self):
        self._tool_calls: List[ToolMetric] = []
        self._total_input_tokens: int = 0
        self._total_output_tokens: int = 0
        self._agent_runs: int = 0
        self._agent_total_duration_ms: float = 0.0

    def record_tool_call(self, tool_name: str, duration_ms: float, success: bool = True) -> None:
        """Record a tool call metric."""
        self._tool_calls.append(ToolMetric(
            tool_name=tool_name,
            duration_ms=duration_ms,
            success=success,
        ))

    def record_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """Record token usage from an agent run."""
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._agent_runs += 1

    def record_agent_duration(self, duration_ms: float) -> None:
        """Record agent run duration."""
        self._agent_total_duration_ms += duration_ms

    def summary(self) -> Dict[str, Any]:
        """Get summary metrics."""
        total_calls = len(self._tool_calls)
        success_calls = sum(1 for m in self._tool_calls if m.success)

        return {
            "total_tool_calls": total_calls,
            "success_rate": round(success_calls / total_calls, 3) if total_calls > 0 else 1.0,
            "total_agent_runs": self._agent_runs,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
        }

    def per_tool_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get per-tool statistics."""
        stats: Dict[str, Dict[str, Any]] = {}

        # Group by tool name
        by_tool: Dict[str, List[ToolMetric]] = {}
        for m in self._tool_calls:
            by_tool.setdefault(m.tool_name, []).append(m)

        for tool_name, calls in by_tool.items():
            durations = sorted([c.duration_ms for c in calls])
            success_count = sum(1 for c in calls if c.success)
            n = len(durations)

            stats[tool_name] = {
                "call_count": n,
                "success_count": success_count,
                "failure_count": n - success_count,
                "success_rate": round(success_count / n, 3) if n > 0 else 1.0,
                "latency_ms": {
                    "min": round(durations[0], 1) if durations else 0,
                    "max": round(durations[-1], 1) if durations else 0,
                    "avg": round(sum(durations) / n, 1) if n > 0 else 0,
                    "p50": round(durations[n // 2], 1) if n > 0 else 0,
                    "p95": round(durations[int(n * 0.95)], 1) if n > 0 else 0,
                    "p99": round(durations[int(n * 0.99)], 1) if n > 0 else 0,
                },
            }

        return stats

    def full_report(self) -> Dict[str, Any]:
        """Get full metrics report."""
        return {
            "summary": self.summary(),
            "token_usage": {
                "input_tokens": self._total_input_tokens,
                "output_tokens": self._total_output_tokens,
                "total_tokens": self._total_input_tokens + self._total_output_tokens,
            },
            "per_tool": self.per_tool_stats(),
            "agent_runs": {
                "count": self._agent_runs,
                "total_duration_ms": round(self._agent_total_duration_ms, 1),
                "avg_duration_ms": round(self._agent_total_duration_ms / self._agent_runs, 1) if self._agent_runs > 0 else 0,
            },
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._tool_calls.clear()
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._agent_runs = 0
        self._agent_total_duration_ms = 0.0


# Global metrics instance
metrics = MetricsCollector()
