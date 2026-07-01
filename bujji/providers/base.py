from abc import ABC, abstractmethod
from typing import Any, Optional

from bujji.core.models import Message, ProviderResponse


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider-specific configuration."""

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> ProviderResponse:
        """Generate a response from the LLM."""

    @abstractmethod
    async def generate_with_tools(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ProviderResponse:
        """Generate a response with tool calling support."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the current model name."""
