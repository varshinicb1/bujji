from typing import Any

from bujji.core.config import Settings
from bujji.core.exceptions import ConfigurationError
from bujji.providers.base import LLMProvider
from bujji.providers.ollama import OllamaProvider
from bujji.providers.openai_compat import OpenAICompatProvider
from bujji.providers.openrouter import OpenRouterProvider
from bujji.providers.airllm_provider import AirLLMProvider


_PROVIDER_MAP: dict[str, type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "openai": OpenAICompatProvider,
    "openrouter": OpenRouterProvider,
    "local": OpenAICompatProvider,
    "airllm": AirLLMProvider,
}


def get_provider(settings: Settings) -> LLMProvider:
    provider_name = settings.llm.provider
    provider_cls = _PROVIDER_MAP.get(provider_name)

    if not provider_cls:
        raise ConfigurationError(
            f"Unknown provider: {provider_name}. "
            f"Available: {', '.join(_PROVIDER_MAP)}"
        )

    config: dict[str, Any] = {
        "model": settings.llm.model,
        "base_url": settings.llm.base_url,
        "api_key": settings.llm.api_key,
        "temperature": settings.llm.temperature,
        "max_tokens": settings.llm.max_tokens,
        "timeout": settings.llm.timeout,
    }

    config = {k: v for k, v in config.items() if v is not None}

    return provider_cls(config)


def register_provider(name: str, provider_cls: type[LLMProvider]) -> None:
    _PROVIDER_MAP[name] = provider_cls
