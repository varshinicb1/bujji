from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from bujji.core.models import ToolResult


class ToolMetadata(BaseModel):
    name: str
    description: str
    permissions: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    tool_schema: dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """Abstract base for all BUJJI tools."""

    metadata: ToolMetadata

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    async def __call__(self, **kwargs: Any) -> Any:
        result = await self.execute(**kwargs)
        if isinstance(result, ToolResult):
            return result.model_dump()
        return result

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given arguments."""

    async def validate_args(self, **kwargs: Any) -> None:
        """Validate arguments before execution. Override in subclasses."""

    def get_schema(self) -> dict[str, Any]:
        return self.metadata.tool_schema


class ToolRegistry:
    """Registry for discovering and managing tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        name = tool.metadata.name
        self._tools[name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolMetadata]:
        return [tool.metadata for tool in self._tools.values()]

    def get_schemas(self) -> list[dict[str, Any]]:
        return [tool.get_schema() for tool in self._tools.values()]

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def __len__(self) -> int:
        return len(self._tools)
