"""Tests for Agent guardrails: budget guard, tool guard, composite guardrails."""

import pytest
from app.agent.guardrails import BudgetGuard, ToolGuard, Guardrails


class TestBudgetGuard:
    def test_within_budget(self):
        guard = BudgetGuard(max_budget=1000.0)
        assert guard.check(500.0) is True
        assert guard.remaining == 1000.0

    def test_exact_budget(self):
        guard = BudgetGuard(max_budget=1000.0)
        assert guard.check(1000.0) is True

    def test_over_budget(self):
        guard = BudgetGuard(max_budget=1000.0)
        guard.allocate(800.0)
        assert guard.check(300.0) is False
        assert guard.remaining == 200.0

    def test_allocate_tracks_total(self):
        guard = BudgetGuard(max_budget=1000.0)
        guard.allocate(400.0)
        guard.allocate(300.0)
        assert guard.remaining == 300.0
        assert guard.check(301.0) is False
        assert guard.check(300.0) is True


class TestToolGuard:
    def test_no_restrictions(self):
        guard = ToolGuard()
        assert guard.needs_confirmation("any_tool") is False
        assert guard.is_blocked("any_tool") is False

    def test_requires_confirmation(self):
        guard = ToolGuard(require_confirmation={"create_campaign"})
        assert guard.needs_confirmation("create_campaign") is True
        assert guard.needs_confirmation("select_products") is False

    def test_confirm_clears_requirement(self):
        guard = ToolGuard(require_confirmation={"create_campaign"})
        guard.confirm("create_campaign")
        assert guard.needs_confirmation("create_campaign") is False

    def test_blocked_tool(self):
        guard = ToolGuard(blocked_tools={"dangerous_tool"})
        assert guard.is_blocked("dangerous_tool") is True
        assert guard.is_blocked("safe_tool") is False
        # Blocked tools also need "confirmation" (but can't be confirmed)
        assert guard.needs_confirmation("dangerous_tool") is True


class TestGuardrails:
    def test_validate_normal_tool(self):
        guardrails = Guardrails(max_budget=5000.0)
        allowed, reason = guardrails.validate_tool_call("select_products", {})
        assert allowed is True
        assert reason == "ok"

    def test_validate_blocked_tool(self):
        guardrails = Guardrails(blocked_tools=["delete_all"])
        allowed, reason = guardrails.validate_tool_call("delete_all", {})
        assert allowed is False
        assert "blocked" in reason

    def test_validate_confirmation_tool(self):
        guardrails = Guardrails(require_confirmation=["create_campaign"])
        allowed, reason = guardrails.validate_tool_call("create_campaign", {})
        assert allowed is False
        assert "confirmation" in reason

    def test_validate_budget_exceeded(self):
        guardrails = Guardrails(max_budget=1000.0)
        guardrails.budget.allocate(900.0)
        allowed, reason = guardrails.validate_tool_call("create_campaign", {"budget": 200.0})
        assert allowed is False
        assert "Budget exceeded" in reason

    def test_validate_budget_ok(self):
        guardrails = Guardrails(max_budget=1000.0)
        allowed, reason = guardrails.validate_tool_call("create_campaign", {"budget": 500.0})
        assert allowed is True
