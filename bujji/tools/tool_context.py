"""Tool execution context providing access to the connection and runtime state."""

from typing import Any


class ToolContext:
    """Context passed to tool handlers during execution."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection
        self._state: dict[str, Any] = {}

    @property
    def connection(self) -> Any:
        return self._connection

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)
