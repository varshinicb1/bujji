"""Local agent configuration backed by BUJJI providers."""

from typing import Any, Callable

import pydantic

from bujji.connections.connection import AgentConfig, ConnectionStrategy
from bujji.providers.factory import get_provider
from bujji.core.config import Settings


class LocalAgentConfig(AgentConfig):
    """Configuration for a locally-running agent backed by a BUJJI provider.

    Uses BUJJI's provider-agnostic layer instead of a compiled Go binary.
    Supports Ollama, OpenAI-compatible, OpenRouter, and local HTTP endpoints.
    """

    provider: str = "ollama"
    model: str = "llama3.2"
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 60
    memory_enabled: bool = True
    memory_type: str = "sqlite"
    planner_enabled: bool = True
    router_enabled: bool = True

    @pydantic.field_validator("capabilities", mode="before")
    @classmethod
    def _default_capabilities(cls, v):
        if v is None:
            return None
        if isinstance(v, dict) and not v.get("enabled_tools") and not v.get("disabled_tools"):
            from bujji.types import BuiltinTools, CapabilitiesConfig
            return CapabilitiesConfig(enabled_tools=BuiltinTools.all_tools())
        return v

    def create_strategy(
        self,
        *,
        tool_runner: Any,
        hook_runner: Any,
    ) -> ConnectionStrategy:
        from bujji.connections.local.local_connection import LocalConnectionStrategy
        return LocalConnectionStrategy(
            config=self,
            tool_runner=tool_runner,
            hook_runner=hook_runner,
        )
