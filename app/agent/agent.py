"""
Lightweight Agent with ReAct loop.

The agent uses LLM function calling to autonomously decide which tools
to call and in what order. No hardcoded pipeline.

~100 lines of core logic, zero external agent framework dependency.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .tool import BaseTool, ToolRegistry
from .llm import LLMProvider, LLMResponse
from app.common.middleware import get_logger

logger = get_logger(__name__)


@dataclass
class AgentStep:
    """A single step in the agent's execution."""
    step_number: int
    tool_name: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    duration_ms: float = 0.0


@dataclass
class AgentResult:
    """Final result of an agent run."""
    answer: str
    steps: List[AgentStep] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "steps": [
                {
                    "step": s.step_number,
                    "tool": s.tool_name,
                    "args": s.arguments,
                    "result_preview": str(s.result)[:200],
                    "duration_ms": s.duration_ms,
                }
                for s in self.steps
            ],
            "token_usage": {
                "input_tokens": self.total_input_tokens,
                "output_tokens": self.total_output_tokens,
            },
            "total_duration_ms": self.total_duration_ms,
        }


class AgentMaxStepsError(Exception):
    """Raised when the agent exceeds the maximum number of steps."""

    def __init__(self, max_steps: int, steps_taken: List[AgentStep]):
        self.max_steps = max_steps
        self.steps_taken = steps_taken
        tools_called = [s.tool_name for s in steps_taken]
        super().__init__(f"Agent exceeded {max_steps} steps. Tools called: {tools_called}")


class Agent:
    """
    Lightweight agent that uses LLM function calling to orchestrate tools.

    The LLM autonomously decides:
    - Which tool to call next
    - What arguments to pass
    - When to stop and return a final answer
    """

    def __init__(
        self,
        llm: LLMProvider,
        tools: List[BaseTool],
        system_prompt: str,
        max_steps: int = 10,
        require_confirmation: Optional[List[str]] = None,
    ):
        """
        Args:
            llm: LLM provider for function calling
            tools: List of available tools
            system_prompt: System prompt defining agent behavior
            max_steps: Maximum tool calls before aborting
            require_confirmation: Tool names that need human confirmation before execution
        """
        self.llm = llm
        self.registry = ToolRegistry()
        for tool in tools:
            self.registry.register(tool)
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self.require_confirmation = set(require_confirmation or [])

    async def run(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
    ) -> AgentResult:
        """
        Run the agent on a user request.

        Args:
            user_request: Natural language request from user
            context: Optional context (e.g., previous campaign results)
            dry_run: If True, plan tool calls but don't execute them

        Returns:
            AgentResult with the final answer and execution trace
        """
        start_time = time.time()

        # Build initial messages
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
        ]
        if context:
            messages.append({"role": "system", "content": f"Context: {json.dumps(context)}"})
        messages.append({"role": "user", "content": user_request})

        steps: List[AgentStep] = []
        total_input_tokens = 0
        total_output_tokens = 0

        tool_schemas = self.registry.get_schemas()

        for step_num in range(1, self.max_steps + 1):
            # Ask LLM what to do next
            response = await self.llm.generate(
                messages=messages,
                tools=tool_schemas if tool_schemas else None,
            )

            total_input_tokens += response.input_tokens
            total_output_tokens += response.output_tokens

            # If no tool calls, LLM is done - return final answer
            if not response.has_tool_calls:
                answer = response.text or "Agent completed without a final response."
                total_ms = (time.time() - start_time) * 1000
                return AgentResult(
                    answer=answer,
                    steps=steps,
                    total_input_tokens=total_input_tokens,
                    total_output_tokens=total_output_tokens,
                    total_duration_ms=total_ms,
                )

            # Execute each tool call
            for tool_call in response.tool_calls:
                tool = self.registry.get(tool_call.name)
                if not tool:
                    # Unknown tool - tell LLM
                    error_msg = f"Unknown tool: {tool_call.name}. Available: {[t.name for t in self.registry.list_tools()]}"
                    messages.append({"role": "tool", "name": tool_call.name, "content": json.dumps({"error": error_msg})})
                    logger.warning(error_msg)
                    continue

                # Check if confirmation required
                if tool_call.name in self.require_confirmation:
                    logger.info(f"Tool '{tool_call.name}' requires confirmation (skipping in auto mode)")
                    if dry_run:
                        result = {"status": "dry_run", "message": f"Would call {tool_call.name}", "args": tool_call.arguments}
                        steps.append(AgentStep(step_number=step_num, tool_name=tool_call.name, arguments=tool_call.arguments, result=result))
                        messages.append({"role": "tool", "name": tool_call.name, "content": json.dumps(result)})
                        continue

                # Execute tool
                step_start = time.time()
                try:
                    if dry_run:
                        result = {"status": "dry_run", "message": f"Would call {tool_call.name}", "args": tool_call.arguments}
                    else:
                        result = await tool.execute(**tool_call.arguments)
                except Exception as e:
                    result = {"error": str(e), "tool": tool_call.name}
                    logger.error(f"Tool '{tool_call.name}' failed: {e}")

                step_duration = (time.time() - step_start) * 1000

                step = AgentStep(
                    step_number=step_num,
                    tool_name=tool_call.name,
                    arguments=tool_call.arguments,
                    result=result,
                    duration_ms=step_duration,
                )
                steps.append(step)
                logger.info(f"Step {step_num}: {tool_call.name} completed in {step_duration:.0f}ms")

                # Add tool result to conversation
                messages.append({
                    "role": "tool",
                    "name": tool_call.name,
                    "content": json.dumps(result, default=str),
                })

        # Exceeded max steps
        raise AgentMaxStepsError(self.max_steps, steps)
