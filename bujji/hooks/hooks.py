"""Hook abstraction for BUJJI SDK.

A Hook is an observer/interceptor that runs at specific points during
agent execution: before turn, after turn, after tool call, etc.
"""

import abc
from typing import Any


class HookResult:
    def __init__(self, blocked: bool = False, message: str | None = None) -> None:
        self.blocked = blocked
        self.message = message


class HookEvent:
    def __init__(
        self,
        *,
        prompt: str | None = None,
        response: str | None = None,
        tool_name: str | None = None,
        tool_args: dict[str, Any] | None = None,
        tool_result: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.prompt = prompt
        self.response = response
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        self.tool_result = tool_result
        self.metadata = metadata or {}


class Hook(abc.ABC):
    name: str = "unnamed_hook"

    async def on_turn(self, event: HookEvent) -> HookResult | None:
        return None

    async def on_after_turn(self, event: HookEvent) -> HookResult | None:
        return None

    async def on_before_tool_call(self, event: HookEvent) -> HookResult | None:
        return None

    async def on_after_tool_call(self, event: HookEvent) -> HookResult | None:
        return None
