import time
from typing import Any

from bujji.core.models import Message, ProviderResponse
from bujji.providers.base import LLMProvider


class LLMService:
    """High-level LLM service wrapping providers."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    @property
    def provider(self) -> LLMProvider:
        return self._provider

    async def generate(
        self,
        messages: list[dict[str, Any]] | list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> ProviderResponse:
        if messages and isinstance(messages[0], dict):
            parsed = []
            for m in messages:
                if isinstance(m, dict):
                    parsed.append(Message(role=m["role"], content=m["content"]))
                else:
                    parsed.append(m)
            messages = parsed

        start = time.monotonic()
        response = await self._provider.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )
        response.latency_ms = (time.monotonic() - start) * 1000
        return response

    async def generate_with_tools(
        self,
        messages: list[dict[str, Any]] | list[Message],
        tools: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ProviderResponse:
        if messages and isinstance(messages[0], dict):
            parsed = []
            for m in messages:
                if isinstance(m, dict):
                    parsed.append(Message(role=m["role"], content=m["content"]))
                else:
                    parsed.append(m)
            messages = parsed

        start = time.monotonic()
        response = await self._provider.generate_with_tools(
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        response.latency_ms = (time.monotonic() - start) * 1000
        return response
