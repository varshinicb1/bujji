"""Tool runner executes tool calls and manages tool lifecycle."""

import inspect
import logging
from typing import Any, Callable

from bujji.tools.base import BaseTool
from bujji.tools.tool_context import ToolContext


class ToolRunner:
    """Coordinates tool execution with context and lifecycle."""

    def __init__(self, tools: list[Callable[..., Any] | dict[str, Any] | BaseTool]) -> None:
        self._tools: dict[str, Callable[..., Any] | BaseTool] = {}
        self._context: ToolContext | None = None

        for tool in tools:
            if isinstance(tool, BaseTool):
                self._tools[tool.metadata.name] = tool
            elif isinstance(tool, dict):
                name = tool.get("name", "unnamed")
                handler = tool.get("handler", tool.get("fn"))
                if handler:
                    self._tools[name] = handler
            elif callable(tool):
                name = getattr(tool, "__name__", tool.__class__.__name__)
                self._tools[name] = tool

    def set_context(self, ctx: ToolContext) -> None:
        self._context = ctx

    async def execute(self, tool_name: str, **kwargs: Any) -> Any:
        handler = self._tools.get(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")
        logging.info(f"Executing tool {tool_name}")
        try:
            if isinstance(handler, BaseTool):
                result = await handler.execute(**kwargs)
                return result
            args_to_pass = kwargs
            if self._context:
                if inspect.signature(handler).parameters.get("context"):
                    args_to_pass["context"] = self._context
            result = handler(**args_to_pass)
            if inspect.iscoroutine(result):
                result = await result
            return result
        except Exception as e:
            logging.exception(f"Tool {tool_name} failed")
            return {"error": str(e)}

    def get_schemas(self) -> list[dict[str, Any]]:
        schemas: list[dict[str, Any]] = []
        for name, handler in self._tools.items():
            if isinstance(handler, BaseTool):
                schemas.append(handler.get_schema())
        return schemas

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())
