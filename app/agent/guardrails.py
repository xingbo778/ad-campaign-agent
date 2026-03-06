"""
Safety guardrails for the Agent.

Ensures the agent doesn't exceed budgets, call dangerous tools
without confirmation, or run indefinitely.
"""

from typing import Any, Dict, List, Optional, Set
from app.common.middleware import get_logger

logger = get_logger(__name__)


class BudgetGuard:
    """Ensures the agent doesn't allocate more than the user-specified budget."""

    def __init__(self, max_budget: float):
        self.max_budget = max_budget
        self.allocated: float = 0.0

    def check(self, amount: float) -> bool:
        """Check if an allocation is within budget."""
        if self.allocated + amount > self.max_budget:
            logger.warning(
                f"Budget guard: rejected allocation ${amount:.2f} "
                f"(allocated: ${self.allocated:.2f}, max: ${self.max_budget:.2f})"
            )
            return False
        return True

    def allocate(self, amount: float) -> None:
        """Record an allocation."""
        self.allocated += amount

    @property
    def remaining(self) -> float:
        return max(0, self.max_budget - self.allocated)


class ToolGuard:
    """Controls which tools require human confirmation before execution."""

    def __init__(self, require_confirmation: Optional[Set[str]] = None, blocked_tools: Optional[Set[str]] = None):
        self.require_confirmation = require_confirmation or set()
        self.blocked_tools = blocked_tools or set()
        self._confirmed: Set[str] = set()

    def needs_confirmation(self, tool_name: str) -> bool:
        """Check if a tool needs human confirmation."""
        if tool_name in self.blocked_tools:
            return True
        if tool_name in self.require_confirmation and tool_name not in self._confirmed:
            return True
        return False

    def confirm(self, tool_name: str) -> None:
        """Mark a tool as confirmed for this session."""
        self._confirmed.add(tool_name)

    def is_blocked(self, tool_name: str) -> bool:
        """Check if a tool is blocked entirely."""
        return tool_name in self.blocked_tools


class Guardrails:
    """Composite guardrails for the Agent."""

    def __init__(
        self,
        max_budget: float = float("inf"),
        require_confirmation: Optional[List[str]] = None,
        blocked_tools: Optional[List[str]] = None,
        max_steps: int = 10,
    ):
        self.budget = BudgetGuard(max_budget)
        self.tools = ToolGuard(
            require_confirmation=set(require_confirmation or []),
            blocked_tools=set(blocked_tools or []),
        )
        self.max_steps = max_steps

    def validate_tool_call(self, tool_name: str, args: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate a tool call before execution.

        Returns:
            (allowed, reason) tuple
        """
        if self.tools.is_blocked(tool_name):
            return False, f"Tool '{tool_name}' is blocked"

        if self.tools.needs_confirmation(tool_name):
            return False, f"Tool '{tool_name}' requires human confirmation"

        # Check budget for tools that allocate money
        if "budget" in args:
            budget_amount = float(args["budget"])
            if not self.budget.check(budget_amount):
                return False, f"Budget exceeded: requested ${budget_amount:.2f}, remaining ${self.budget.remaining:.2f}"

        return True, "ok"
