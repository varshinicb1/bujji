"""Base interfaces for BUJJI connections.

A Connection is the SDK's public interface for interacting with an agent
backend, regardless of where the agent runs.
"""

import abc
import json
from collections.abc import AsyncIterator, Callable
from typing import Any

import pydantic

from bujji import types


class AgentConfig(abc.ABC, pydantic.BaseModel):
    """Abstract base class for agent configuration.

    Each ConnectionStrategy defines a concrete subclass with the
    config fields it needs.
    """

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    system_instructions: str | types.SystemInstructions | None = None
    capabilities: types.CapabilitiesConfig = pydantic.Field(
        default_factory=lambda: types.CapabilitiesConfig(
            enabled_tools=types.BuiltinTools.read_only()
        )
    )
    tools: list[Callable[..., Any]] = pydantic.Field(default_factory=list)
    policies: list[Any] = pydantic.Field(default_factory=list)
    hooks: list[Any] = pydantic.Field(default_factory=list)
    triggers: list[Any] = pydantic.Field(default_factory=list)
    mcp_servers: list[types.McpServerConfig] = pydantic.Field(
        default_factory=list
    )
    workspaces: list[str] = pydantic.Field(default_factory=list)
    conversation_id: str | None = None
    save_dir: str | None = None
    app_data_dir: str | None = None
    response_schema: dict[str, Any] | type[pydantic.BaseModel] | str | None = None
    skills_paths: list[str] = pydantic.Field(default_factory=list)

    @pydantic.field_validator("response_schema")
    @classmethod
    def _validate_schema(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                json.loads(v)
                return v
            except json.JSONDecodeError as exc:
                raise ValueError("response_schema string is not valid JSON.") from exc
        if isinstance(v, dict):
            return json.dumps(v)
        if isinstance(v, type) and issubclass(v, pydantic.BaseModel):
            return json.dumps(v.model_json_schema())
        raise ValueError(
            f"Unsupported response_schema format: {type(v).__name__}. "
            "Expected a JSON string, dict, or pydantic.BaseModel subclass."
        )

    @abc.abstractmethod
    def create_strategy(
        self,
        *,
        tool_runner: Any,
        hook_runner: Any,
    ) -> "ConnectionStrategy":
        ...


class Connection(abc.ABC):
    """A live session with an agent backend."""

    @property
    def is_idle(self) -> bool:
        return True

    @property
    def conversation_id(self) -> str:
        return ""

    @abc.abstractmethod
    async def send(self, prompt: types.Content | None, **kwargs: Any) -> None:
        ...

    @abc.abstractmethod
    def receive_steps(self) -> AsyncIterator[types.Step]:
        ...

    async def disconnect(self) -> None:
        pass

    async def cancel(self) -> None:
        pass

    async def delete(self) -> None:
        pass

    async def signal_idle(self) -> None:
        pass

    async def wait_for_idle(self) -> None:
        pass

    async def wait_for_wakeup(self, timeout: float = 300.0) -> bool:
        return False

    async def send_tool_results(self, results: list[types.ToolResult]) -> None:
        pass

    @abc.abstractmethod
    async def send_trigger_notification(self, content: str) -> None:
        ...


class ConnectionStrategy(abc.ABC):
    """Strategy for establishing a Connection to an agent backend."""

    @abc.abstractmethod
    def connect(self) -> Connection:
        ...

    @abc.abstractmethod
    async def __aenter__(self) -> None:
        ...

    @abc.abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ...
