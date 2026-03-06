"""Tests for Agent metrics collector."""

import pytest
from app.agent.metrics import MetricsCollector


class TestMetricsCollector:
    def test_empty_summary(self):
        m = MetricsCollector()
        s = m.summary()
        assert s["total_tool_calls"] == 0
        assert s["success_rate"] == 1.0
        assert s["total_agent_runs"] == 0

    def test_record_tool_calls(self):
        m = MetricsCollector()
        m.record_tool_call("select_products", 150.0, success=True)
        m.record_tool_call("select_products", 200.0, success=True)
        m.record_tool_call("generate_creatives", 300.0, success=False)

        s = m.summary()
        assert s["total_tool_calls"] == 3
        assert s["success_rate"] == pytest.approx(0.667, abs=0.01)

    def test_per_tool_stats(self):
        m = MetricsCollector()
        m.record_tool_call("echo", 10.0, success=True)
        m.record_tool_call("echo", 20.0, success=True)
        m.record_tool_call("echo", 30.0, success=False)

        stats = m.per_tool_stats()
        assert "echo" in stats
        echo = stats["echo"]
        assert echo["call_count"] == 3
        assert echo["success_count"] == 2
        assert echo["failure_count"] == 1
        assert echo["latency_ms"]["min"] == 10.0
        assert echo["latency_ms"]["max"] == 30.0
        assert echo["latency_ms"]["avg"] == 20.0

    def test_record_tokens(self):
        m = MetricsCollector()
        m.record_tokens(100, 50)
        m.record_tokens(200, 100)
        report = m.full_report()
        assert report["token_usage"]["input_tokens"] == 300
        assert report["token_usage"]["output_tokens"] == 150
        assert report["token_usage"]["total_tokens"] == 450
        assert report["agent_runs"]["count"] == 2

    def test_reset(self):
        m = MetricsCollector()
        m.record_tool_call("echo", 10.0)
        m.record_tokens(100, 50)
        m.reset()
        s = m.summary()
        assert s["total_tool_calls"] == 0
        assert s["total_agent_runs"] == 0

    def test_full_report_structure(self):
        m = MetricsCollector()
        m.record_tool_call("tool_a", 100.0)
        m.record_tokens(500, 200)
        m.record_agent_duration(1500.0)

        report = m.full_report()
        assert "summary" in report
        assert "token_usage" in report
        assert "per_tool" in report
        assert "agent_runs" in report
        assert report["agent_runs"]["total_duration_ms"] == 1500.0
