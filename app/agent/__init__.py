"""
Lightweight Agent framework for ad campaign orchestration.

No external agent framework dependency - uses Gemini/OpenAI native
function calling + custom ReAct loop (~500 lines total).
"""

from .agent import Agent, AgentResult, AgentStep, AgentMaxStepsError
from .tool import BaseTool, ToolRegistry
from .llm import LLMProvider, GeminiProvider, OpenAIProvider

__all__ = [
    "Agent",
    "AgentResult",
    "AgentStep",
    "AgentMaxStepsError",
    "BaseTool",
    "ToolRegistry",
    "LLMProvider",
    "GeminiProvider",
    "OpenAIProvider",
]
