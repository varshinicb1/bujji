"""BUJJI SDK - AI Engineering Assistant SDK.

A Python SDK for building AI agents powered by any LLM provider.
Provides a three-layer architecture: Agent (high-level), Conversation (session),
and Connection (transport), with built-in tools, memory, planning, routing,
hooks, policies, MCP integration, and triggers.
"""

from bujji import types
from bujji.agent import Agent
from bujji.connections.connection import AgentConfig, Connection, ConnectionStrategy
from bujji.connections.local import LocalAgentConfig
from bujji.hooks import hooks, policy
from bujji.memory.context_window import ContextWindowManager, create_context_manager
from bujji.tools.tool_context import ToolContext
from bujji.utils import run_interactive_loop

__version__ = "2.1.0"
__all__ = [
    "Agent",
    "AgentConfig",
    "LocalAgentConfig",
    "Connection",
    "ConnectionStrategy",
    "ContextWindowManager",
    "create_context_manager",
    "ToolContext",
    "policy",
    "hooks",
    "run_interactive_loop",
    "types",
]
