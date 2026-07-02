from typing import Any

import httpx

from bujji.core.exceptions import ProviderError
from bujji.core.models import Message, ProviderResponse
from bujji.providers.base import LLMProvider


class OpenAICompatProvider(LLMProvider):
    """Provider for any OpenAI-compatible API."""

    def _validate_config(self) -> None:
        self.base_url = self.config.get(
            "base_url", "https://api.openai.com/v1"
        ).rstrip("/")
        self.model = self.config.get("model", "gpt-4o")
        self.api_key = self.config.get("api_key", "")

    @property
    def provider_name(self) -> str:
        return "openai_compat"

    @property
    def model_name(self) -> str:
        return self.model

    async def generate(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> ProviderResponse:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "temperature": temperature or self.config.get("temperature", 0.1),
            "stream": stream,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

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
            raise ProviderError(f"OpenAI-compatible request failed: {e}") from e

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
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ProviderResponse:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "tools": tools,
            "temperature": temperature or self.config.get("temperature", 0.1),
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

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
            raise ProviderError(f"OpenAI-compatible tool call failed: {e}") from e

        choice = data["choices"][0]
        return ProviderResponse(
            content=choice["message"].get("content", ""),
            model=self.model,
            provider=self.provider_name,
            usage=data.get("usage"),
            finish_reason=choice.get("finish_reason"),
        )
