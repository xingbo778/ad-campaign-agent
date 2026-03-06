"""
Tests for the Agent ReAct loop, tool registry, and execution flow.

Uses a MockLLMProvider to simulate LLM responses with tool calls,
so tests run without any API keys.
"""

import pytest
import pytest_asyncio
from typing import Any, Dict, List, Optional
from app.agent.agent import Agent, AgentResult, AgentStep, AgentMaxStepsError
from app.agent.tool import BaseTool, ToolRegistry
from app.agent.llm import LLMProvider, LLMResponse, ToolCall


# ─── Mock LLM Provider ─────────────────────────────────────────────

class MockLLMProvider(LLMProvider):
    """
    Mock LLM that returns pre-configured responses in sequence.

    Each call to generate() pops the next response from the queue.
    If the queue is empty, returns a text-only "Done" response.
    """

    def __init__(self, responses: Optional[List[LLMResponse]] = None):
        self.responses = list(responses or [])
        self.call_count = 0
        self.last_messages: List[Dict[str, Any]] = []

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> LLMResponse:
        self.call_count += 1
        self.last_messages = messages
        if self.responses:
            return self.responses.pop(0)
        return LLMResponse(text="Done.", input_tokens=10, output_tokens=5)


# ─── Mock Tools ─────────────────────────────────────────────────────

class EchoTool(BaseTool):
    name = "echo"
    description = "Echoes back the input"
    parameters = {
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        return {"echoed": kwargs.get("message", "")}


class FailingTool(BaseTool):
    name = "fail"
    description = "Always fails"
    parameters = {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> Dict[str, Any]:
        raise RuntimeError("Tool failed intentionally")


class CounterTool(BaseTool):
    name = "counter"
    description = "Increments a counter"
    parameters = {"type": "object", "properties": {}}

    def __init__(self):
        self.count = 0

    async def execute(self, **kwargs) -> Dict[str, Any]:
        self.count += 1
        return {"count": self.count}


# ─── Tool Registry Tests ───────────────────────────────────────────

class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()
        tool = EchoTool()
        registry.register(tool)
        assert registry.get("echo") is tool
        assert "echo" in registry
        assert len(registry) == 1

    def test_get_unknown_returns_none(self):
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_register_without_name_raises(self):
        class NoNameTool(BaseTool):
            name = ""
            description = "no name"
            parameters = {}
            async def execute(self, **kwargs):
                return {}

        registry = ToolRegistry()
        with pytest.raises(ValueError):
            registry.register(NoNameTool())

    def test_get_schemas(self):
        registry = ToolRegistry()
        registry.register(EchoTool())
        schemas = registry.get_schemas()
        assert len(schemas) == 1
        assert schemas[0]["name"] == "echo"
        assert "description" in schemas[0]
        assert "parameters" in schemas[0]

    def test_list_tools(self):
        registry = ToolRegistry()
        registry.register(EchoTool())
        registry.register(CounterTool())
        tools = registry.list_tools()
        assert len(tools) == 2


# ─── Agent ReAct Loop Tests ────────────────────────────────────────

class TestAgentReActLoop:
    @pytest.mark.asyncio
    async def test_immediate_text_response(self):
        """Agent returns immediately when LLM gives text (no tool calls)."""
        llm = MockLLMProvider([
            LLMResponse(text="Here is your answer.", input_tokens=50, output_tokens=20),
        ])
        agent = Agent(llm=llm, tools=[], system_prompt="You are a helper.")

        result = await agent.run("Hello")
        assert result.answer == "Here is your answer."
        assert len(result.steps) == 0
        assert result.total_input_tokens == 50
        assert result.total_output_tokens == 20
        assert llm.call_count == 1

    @pytest.mark.asyncio
    async def test_single_tool_call(self):
        """Agent calls one tool then returns."""
        llm = MockLLMProvider([
            # Step 1: LLM wants to call echo tool
            LLMResponse(tool_calls=[ToolCall(name="echo", arguments={"message": "hello"})]),
            # Step 2: LLM returns final answer
            LLMResponse(text="I echoed: hello"),
        ])
        agent = Agent(llm=llm, tools=[EchoTool()], system_prompt="Test")

        result = await agent.run("Echo hello")
        assert result.answer == "I echoed: hello"
        assert len(result.steps) == 1
        assert result.steps[0].tool_name == "echo"
        assert result.steps[0].result == {"echoed": "hello"}
        assert llm.call_count == 2

    @pytest.mark.asyncio
    async def test_multi_tool_calls(self):
        """Agent calls multiple tools in sequence."""
        counter = CounterTool()
        llm = MockLLMProvider([
            LLMResponse(tool_calls=[ToolCall(name="counter", arguments={})]),
            LLMResponse(tool_calls=[ToolCall(name="counter", arguments={})]),
            LLMResponse(text="Counter is at 2"),
        ])
        agent = Agent(llm=llm, tools=[counter], system_prompt="Test")

        result = await agent.run("Count twice")
        assert result.answer == "Counter is at 2"
        assert len(result.steps) == 2
        assert counter.count == 2

    @pytest.mark.asyncio
    async def test_unknown_tool_handled(self):
        """Agent handles unknown tool names gracefully."""
        llm = MockLLMProvider([
            LLMResponse(tool_calls=[ToolCall(name="nonexistent", arguments={})]),
            LLMResponse(text="Tool not found"),
        ])
        agent = Agent(llm=llm, tools=[EchoTool()], system_prompt="Test")

        result = await agent.run("Call unknown")
        assert result.answer == "Tool not found"
        # Unknown tool doesn't create a step
        assert len(result.steps) == 0

    @pytest.mark.asyncio
    async def test_tool_failure_captured(self):
        """Agent captures tool errors and continues."""
        llm = MockLLMProvider([
            LLMResponse(tool_calls=[ToolCall(name="fail", arguments={})]),
            LLMResponse(text="Tool failed, sorry"),
        ])
        agent = Agent(llm=llm, tools=[FailingTool()], system_prompt="Test")

        result = await agent.run("Try failing tool")
        assert "error" in result.steps[0].result
        assert result.answer == "Tool failed, sorry"

    @pytest.mark.asyncio
    async def test_max_steps_exceeded(self):
        """Agent raises AgentMaxStepsError when exceeding max_steps."""
        # LLM always calls a tool, never returns text
        infinite_responses = [
            LLMResponse(tool_calls=[ToolCall(name="counter", arguments={})])
            for _ in range(5)
        ]
        llm = MockLLMProvider(infinite_responses)
        agent = Agent(llm=llm, tools=[CounterTool()], system_prompt="Test", max_steps=3)

        with pytest.raises(AgentMaxStepsError) as exc_info:
            await agent.run("Loop forever")
        assert exc_info.value.max_steps == 3
        assert len(exc_info.value.steps_taken) == 3

    @pytest.mark.asyncio
    async def test_dry_run_mode(self):
        """In dry_run mode, tools are not actually executed."""
        counter = CounterTool()
        llm = MockLLMProvider([
            LLMResponse(tool_calls=[ToolCall(name="counter", arguments={})]),
            LLMResponse(text="Dry run complete"),
        ])
        agent = Agent(llm=llm, tools=[counter], system_prompt="Test")

        result = await agent.run("Count", dry_run=True)
        assert counter.count == 0  # Not actually called
        assert result.steps[0].result["status"] == "dry_run"

    @pytest.mark.asyncio
    async def test_context_passed_to_llm(self):
        """Context is included in LLM messages."""
        llm = MockLLMProvider([LLMResponse(text="Got context")])
        agent = Agent(llm=llm, tools=[], system_prompt="Test")

        await agent.run("Hello", context={"key": "value"})
        # Check that context was in the messages
        messages = llm.last_messages
        context_msgs = [m for m in messages if "Context" in m.get("content", "")]
        assert len(context_msgs) == 1

    @pytest.mark.asyncio
    async def test_result_to_dict(self):
        """AgentResult.to_dict() produces valid structure."""
        result = AgentResult(
            answer="Done",
            steps=[AgentStep(step_number=1, tool_name="echo", arguments={"msg": "hi"}, result={"ok": True}, duration_ms=42.0)],
            total_input_tokens=100,
            total_output_tokens=50,
            total_duration_ms=500.0,
        )
        d = result.to_dict()
        assert d["answer"] == "Done"
        assert len(d["steps"]) == 1
        assert d["token_usage"]["input_tokens"] == 100
        assert d["total_duration_ms"] == 500.0
