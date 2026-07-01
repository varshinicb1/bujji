from typing import Any, Optional

import httpx

from bujji.core.exceptions import ProviderError
from bujji.core.models import Message, ProviderResponse
from bujji.providers.base import LLMProvider


class OpenRouterProvider(LLMProvider):
    """Provider for OpenRouter API (multi-model gateway)."""

    def _validate_config(self) -> None:
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = self.config.get("model", "anthropic/claude-sonnet")
        self.api_key = self.config.get("api_key", "")

    @property
    def provider_name(self) -> str:
        return "openrouter"

    @property
    def model_name(self) -> str:
        return self.model

    async def generate(
        self,
        messages: list[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> ProviderResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "temperature": temperature or self.config.get("temperature", 0.1),
            "stream": stream,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.config.get("timeout", 60)) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            raise ProviderError(f"OpenRouter request failed: {e}") from e

        choice = data["choices"][0]
        return ProviderResponse(
            content=choice["message"].get("content", ""),
            model=self.model,
            provider=self.provider_name,
            usage=data.get("usage"),
            finish_reason=choice.get("finish_reason"),
        )

    async def generate_with_tools(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ProviderResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "tools": tools,
            "temperature": temperature or self.config.get("temperature", 0.1),
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.config.get("timeout", 60)) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            raise ProviderError(f"OpenRouter tool call failed: {e}") from e

        choice = data["choices"][0]
        return ProviderResponse(
            content=choice["message"].get("content", ""),
            model=self.model,
            provider=self.provider_name,
            usage=data.get("usage"),
            finish_reason=choice.get("finish_reason"),
        )
