"""
Agent-mode orchestrator service.

Exposes the lightweight Agent via FastAPI endpoints:
- /agent/run: Single-turn agent execution
- /agent/chat: Multi-turn conversational agent
- /agent/stream: SSE streaming of agent thinking process
"""

import json
import time
import asyncio
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.common.config import settings
from app.common.middleware import setup_logging, RequestIDMiddleware, get_cors_middleware_class, get_logger
from app.common.exceptions import register_exception_handlers
from app.agent.agent import Agent, AgentResult, AgentMaxStepsError
from app.agent.llm import FallbackProvider, LLMResponse, ToolCall
from app.agent.memory import ShortTermMemory, LongTermMemory
from app.agent.guardrails import Guardrails
from app.agent.tools import (
    SelectProductsTool,
    GenerateCreativesTool,
    GenerateStrategyTool,
    CreateCampaignTool,
    AppendEventTool,
    SummarizeRunsTool,
)
from app.agent.metrics import MetricsCollector, metrics

# Setup
setup_logging(level=settings.LOG_LEVEL, service_name="agent_service")
logger = get_logger(__name__)

app = FastAPI(
    title="Ad Campaign Agent Service",
    description="Autonomous agent that uses LLM function calling to orchestrate ad campaign creation",
    version="3.0.0",
)
app.add_middleware(RequestIDMiddleware)
cors_middleware = get_cors_middleware_class(settings.ENVIRONMENT)
cors_middleware(app)
register_exception_handlers(app)

# Shared state
long_term_memory = LongTermMemory()

# System prompt for the agent
AGENT_SYSTEM_PROMPT = """You are an expert ad campaign orchestrator agent. You autonomously create and manage advertising campaigns by calling specialized tools.

## How to Work
- Analyze the user's request to understand their campaign needs
- Call tools in the order that makes sense (typically: select_products → generate_strategy → generate_creatives → create_campaign → append_event)
- You can skip tools that aren't needed, or call them in a different order based on the request
- If the user's request is unclear or missing required information (budget, objective, category), ask for clarification instead of guessing
- After completing all tool calls, provide a clear summary of what was accomplished

## Campaign Spec Format
When calling tools, use this campaign_spec structure:
{
  "user_query": "<original user request>",
  "platform": "meta",
  "budget": <number>,
  "objective": "sales|traffic|conversions|leads",
  "category": "<product category>",
  "time_range": null,
  "metadata": {}
}

## Important Rules
- Never allocate budget higher than what the user specified
- Always log campaign creation events via append_event
- If a tool fails, explain the error and suggest alternatives
- Be concise in your final summary
"""


# ─── Request/Response Models ────────────────────────────────────────

class AgentRunRequest(BaseModel):
    user_request: str = Field(..., min_length=1, max_length=5000, description="Natural language request")
    max_budget: float = Field(default=float("inf"), gt=0, description="Maximum budget guard")
    dry_run: bool = Field(default=False, description="Plan tool calls without executing")
    max_steps: int = Field(default=10, ge=1, le=20, description="Maximum agent steps")


class AgentRunResponse(BaseModel):
    status: str
    answer: str
    steps: List[Dict[str, Any]] = []
    token_usage: Dict[str, int] = {}
    duration_ms: float = 0.0
    metrics: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")


class AgentChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1, description="Conversation history")
    max_budget: float = Field(default=float("inf"), gt=0)
    dry_run: bool = Field(default=False)
    max_steps: int = Field(default=10, ge=1, le=20)


class AgentStreamRequest(BaseModel):
    user_request: str = Field(..., min_length=1, max_length=5000)
    max_budget: float = Field(default=float("inf"), gt=0)
    max_steps: int = Field(default=10, ge=1, le=20)


# ─── Helper: build agent instance ──────────────────────────────────

def _build_agent(max_steps: int = 10, require_confirmation: Optional[List[str]] = None) -> Agent:
    """Create an Agent with all tools and auto-detected LLM provider."""
    llm = FallbackProvider()
    if not llm.available:
        raise HTTPException(status_code=503, detail="No LLM provider configured. Set OPENAI_REAL_KEY or GEMINI_API_KEY.")

    tools = [
        SelectProductsTool(),
        GenerateCreativesTool(),
        GenerateStrategyTool(),
        CreateCampaignTool(),
        AppendEventTool(),
        SummarizeRunsTool(),
    ]

    return Agent(
        llm=llm,
        tools=tools,
        system_prompt=AGENT_SYSTEM_PROMPT,
        max_steps=max_steps,
        require_confirmation=require_confirmation or ["create_campaign"],
    )


# ─── Endpoints ──────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "agent_service",
        "mode": "agent",
        "llm_available": FallbackProvider().available,
        "metrics_summary": metrics.summary(),
    }


@app.post("/agent/run", response_model=AgentRunResponse)
async def agent_run(request: AgentRunRequest):
    """
    Single-turn agent execution.

    The agent autonomously decides which tools to call based on the user request.
    """
    try:
        agent = _build_agent(max_steps=request.max_steps)

        # Build context from long-term memory
        context = None
        memory_context = long_term_memory.get_context_string()
        if memory_context:
            context = {"campaign_history": memory_context}

        result = await agent.run(
            user_request=request.user_request,
            context=context,
            dry_run=request.dry_run,
        )

        # Record metrics
        for step in result.steps:
            metrics.record_tool_call(step.tool_name, step.duration_ms, success="error" not in step.result)
        metrics.record_tokens(result.total_input_tokens, result.total_output_tokens)

        return AgentRunResponse(
            status="success",
            answer=result.answer,
            steps=[
                {
                    "step": s.step_number,
                    "tool": s.tool_name,
                    "args": s.arguments,
                    "result_preview": str(s.result)[:500],
                    "duration_ms": round(s.duration_ms, 1),
                }
                for s in result.steps
            ],
            token_usage={
                "input_tokens": result.total_input_tokens,
                "output_tokens": result.total_output_tokens,
            },
            duration_ms=round(result.total_duration_ms, 1),
            metrics=metrics.summary(),
        )

    except AgentMaxStepsError as e:
        return AgentRunResponse(
            status="max_steps_exceeded",
            answer=f"Agent exceeded maximum steps ({e.max_steps}). Partial results may be available.",
            steps=[
                {"step": s.step_number, "tool": s.tool_name, "duration_ms": round(s.duration_ms, 1)}
                for s in e.steps_taken
            ],
        )
    except Exception as e:
        logger.error(f"Agent run failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@app.post("/agent/chat", response_model=AgentRunResponse)
async def agent_chat(request: AgentChatRequest):
    """
    Multi-turn conversational agent.

    Accepts a conversation history (messages) so the agent can:
    - Ask follow-up questions if info is missing
    - Reference previous turns
    - Refine campaigns based on feedback
    """
    try:
        agent = _build_agent(max_steps=request.max_steps)

        # Build the full conversation as a single context-rich prompt
        conversation_parts = []
        for msg in request.messages[:-1]:  # All except last (which is current request)
            conversation_parts.append(f"{msg.role.capitalize()}: {msg.content}")

        current_request = request.messages[-1].content

        # If there's conversation history, include it as context
        context = None
        if conversation_parts:
            context = {"conversation_history": "\n".join(conversation_parts)}

        # Add long-term memory
        memory_context = long_term_memory.get_context_string()
        if memory_context:
            if context is None:
                context = {}
            context["campaign_history"] = memory_context

        result = await agent.run(
            user_request=current_request,
            context=context,
            dry_run=request.dry_run,
        )

        # Record metrics
        for step in result.steps:
            metrics.record_tool_call(step.tool_name, step.duration_ms, success="error" not in step.result)
        metrics.record_tokens(result.total_input_tokens, result.total_output_tokens)

        return AgentRunResponse(
            status="success",
            answer=result.answer,
            steps=[
                {
                    "step": s.step_number,
                    "tool": s.tool_name,
                    "args": s.arguments,
                    "result_preview": str(s.result)[:500],
                    "duration_ms": round(s.duration_ms, 1),
                }
                for s in result.steps
            ],
            token_usage={
                "input_tokens": result.total_input_tokens,
                "output_tokens": result.total_output_tokens,
            },
            duration_ms=round(result.total_duration_ms, 1),
        )

    except AgentMaxStepsError as e:
        return AgentRunResponse(
            status="max_steps_exceeded",
            answer=f"Agent exceeded maximum steps ({e.max_steps}).",
            steps=[],
        )
    except Exception as e:
        logger.error(f"Agent chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent chat failed: {str(e)}")


@app.post("/agent/stream")
async def agent_stream(request: AgentStreamRequest):
    """
    SSE streaming endpoint for agent thinking process.

    Streams events as the agent reasons and calls tools, so the
    frontend can show real-time progress.

    Event types:
    - thinking: Agent is reasoning about what to do
    - tool_call: Agent is calling a tool
    - tool_result: Tool returned a result
    - answer: Final agent answer
    - error: An error occurred
    """

    async def event_generator():
        try:
            llm = FallbackProvider()
            if not llm.available:
                yield _sse_event("error", {"message": "No LLM provider configured"})
                return

            tools = [
                SelectProductsTool(),
                GenerateCreativesTool(),
                GenerateStrategyTool(),
                CreateCampaignTool(),
                AppendEventTool(),
                SummarizeRunsTool(),
            ]

            from app.agent.tool import ToolRegistry
            registry = ToolRegistry()
            for tool in tools:
                registry.register(tool)

            tool_schemas = registry.get_schemas()

            # Build messages
            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": request.user_request},
            ]

            yield _sse_event("thinking", {"message": "Analyzing your request..."})

            for step_num in range(1, request.max_steps + 1):
                response = await llm.generate(
                    messages=messages,
                    tools=tool_schemas,
                )

                if not response.has_tool_calls:
                    answer = response.text or "Done."
                    yield _sse_event("answer", {"answer": answer, "step": step_num})
                    return

                for tool_call in response.tool_calls:
                    yield _sse_event("tool_call", {
                        "step": step_num,
                        "tool": tool_call.name,
                        "args": tool_call.arguments,
                    })

                    tool = registry.get(tool_call.name)
                    if not tool:
                        error = f"Unknown tool: {tool_call.name}"
                        yield _sse_event("error", {"message": error, "step": step_num})
                        messages.append({"role": "tool", "name": tool_call.name, "content": json.dumps({"error": error})})
                        continue

                    step_start = time.time()
                    try:
                        result = await tool.execute(**tool_call.arguments)
                    except Exception as e:
                        result = {"error": str(e)}

                    duration_ms = (time.time() - step_start) * 1000

                    yield _sse_event("tool_result", {
                        "step": step_num,
                        "tool": tool_call.name,
                        "duration_ms": round(duration_ms, 1),
                        "result_preview": str(result)[:300],
                        "success": "error" not in result,
                    })

                    metrics.record_tool_call(tool_call.name, duration_ms, success="error" not in result)
                    messages.append({"role": "tool", "name": tool_call.name, "content": json.dumps(result, default=str)})

                yield _sse_event("thinking", {"message": f"Step {step_num} complete, deciding next action..."})

            yield _sse_event("error", {"message": f"Max steps ({request.max_steps}) exceeded"})

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield _sse_event("error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/agent/metrics")
async def get_metrics():
    """Get agent metrics: tool latency, success rates, token usage."""
    return metrics.full_report()


def _sse_event(event_type: str, data: dict) -> str:
    """Format an SSE event."""
    return f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
