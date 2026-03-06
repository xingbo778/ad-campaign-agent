"""
LLM Provider abstraction layer.

Unifies Gemini and OpenAI function calling interfaces behind a
single abstract class. Supports automatic fallback.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.common.config import settings
from app.common.middleware import get_logger

logger = get_logger(__name__)


@dataclass
class ToolCall:
    """A single tool call from the LLM."""
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    text: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """Abstract LLM provider with function calling support."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> LLMResponse:
        """Generate a response, optionally using function calling."""
        ...


class GeminiProvider(LLMProvider):
    """Google Gemini provider with function calling."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL
        self._model = None

        if self.api_key:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
            logger.info(f"GeminiProvider initialized with model: {self.model_name}")

    @property
    def available(self) -> bool:
        return self._model is not None

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> LLMResponse:
        if not self._model:
            raise RuntimeError("Gemini not configured (missing GEMINI_API_KEY)")

        import google.generativeai as genai

        # Convert messages to Gemini format
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}\n\n")
            elif role == "tool":
                tool_name = msg.get("name", "tool")
                prompt_parts.append(f"Tool result ({tool_name}): {content}\n\n")
            else:
                prompt_parts.append(content)

        full_prompt = "\n".join(prompt_parts)

        # Build generation config
        gen_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        # Convert tools to Gemini function declarations
        gemini_tools = None
        if tools:
            function_declarations = []
            for tool in tools:
                fd = genai.types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=tool.get("parameters", {}),
                )
                function_declarations.append(fd)
            gemini_tools = [genai.types.Tool(function_declarations=function_declarations)]

        response = self._model.generate_content(
            full_prompt,
            generation_config=gen_config,
            tools=gemini_tools,
        )

        # Parse response
        result = LLMResponse()

        if response.candidates:
            candidate = response.candidates[0]
            for part in candidate.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    result.tool_calls.append(ToolCall(
                        name=fc.name,
                        arguments=dict(fc.args) if fc.args else {},
                    ))
                elif hasattr(part, "text") and part.text:
                    result.text = (result.text or "") + part.text

        # Token usage
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            result.input_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
            result.output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)

        return result


class OpenAIProvider(LLMProvider):
    """OpenAI provider with function calling."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_REAL_KEY
        self.model_name = model or settings.OPENAI_MODEL
        self._client = None

        if self.api_key:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=settings.OPENAI_BASE_URL,
            )
            logger.info(f"OpenAIProvider initialized with model: {self.model_name}")

    @property
    def available(self) -> bool:
        return self._client is not None

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> LLMResponse:
        if not self._client:
            raise RuntimeError("OpenAI not configured (missing OPENAI_REAL_KEY)")

        # Build kwargs
        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Convert tools to OpenAI function format
        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t.get("parameters", {}),
                    },
                }
                for t in tools
            ]

        response = await self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        result = LLMResponse()

        # Extract text
        if choice.message.content:
            result.text = choice.message.content.strip()

        # Extract tool calls
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                result.tool_calls.append(ToolCall(
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments) if tc.function.arguments else {},
                ))

        # Token usage
        if response.usage:
            result.input_tokens = response.usage.prompt_tokens
            result.output_tokens = response.usage.completion_tokens

        return result


class FallbackProvider(LLMProvider):
    """
    Provider that tries multiple LLM providers in order.
    Falls back to the next provider if the current one fails.
    """

    def __init__(self, providers: Optional[List[LLMProvider]] = None):
        if providers:
            self.providers = providers
        else:
            # Auto-detect available providers
            self.providers = []
            openai = OpenAIProvider()
            if openai.available:
                self.providers.append(openai)
            gemini = GeminiProvider()
            if gemini.available:
                self.providers.append(gemini)

        if not self.providers:
            logger.warning("No LLM providers available")

    @property
    def available(self) -> bool:
        return len(self.providers) > 0

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> LLMResponse:
        last_error = None
        for provider in self.providers:
            try:
                return await provider.generate(messages, tools, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"{provider.__class__.__name__} failed: {e}, trying next")
                last_error = e

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")
