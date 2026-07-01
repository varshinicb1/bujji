"""MCP (Model Context Protocol) bridge for connecting external tool servers."""

import logging
from typing import Any

from bujji import types


class McpBridge:
    """Bridge to MCP servers providing external tools.

    Each MCP server exposes a set of tools that are merged into the
    agent's ToolRunner.
    """

    def __init__(self) -> None:
        self._servers: list[types.McpServerConfig] = []
        self._tools: list[dict[str, Any]] = []

    async def connect(self, server_config: types.McpServerConfig) -> None:
        logging.info(f"Connecting to MCP server: {server_config.name}")
        self._servers.append(server_config)
        self._tools.append({
            "name": f"mcp_{server_config.name}",
            "description": f"Tool from MCP server '{server_config.name}'",
            "handler": lambda *a, **kw: self._forward_call(server_config.name, *a, **kw),
        })

    async def stop(self) -> None:
        self._servers.clear()
        self._tools.clear()

    @property
    def tools(self) -> list:
        return list(self._tools)

    async def _forward_call(self, server_name: str, *args: Any, **kwargs: Any) -> Any:
        logging.info(f"MCP call forwarded to server {server_name}: {kwargs}")
        return {"mcp_result": "stub", "server": server_name}
