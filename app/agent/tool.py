"""
BaseTool abstraction and Tool Registry.

Each tool wraps a service client and exposes a standard interface
for the Agent's function calling.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.common.middleware import get_logger

logger = get_logger(__name__)


class BaseTool(ABC):
    """
    Abstract base for all Agent tools.

    Subclasses must define:
    - name: Tool identifier (used in function calling)
    - description: What the tool does (sent to LLM)
    - parameters: JSON Schema for tool parameters
    - execute(**kwargs): Actual execution logic
    """

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        ...

    def to_function_schema(self) -> Dict[str, Any]:
        """Generate function calling schema for LLM."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    def __repr__(self) -> str:
        return f"Tool({self.name})"


class ToolRegistry:
    """Registry for dynamically registering and discovering tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        if not tool.name:
            raise ValueError("Tool must have a name")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get function calling schemas for all tools."""
        return [tool.to_function_schema() for tool in self._tools.values()]

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
