import pytest

from bujji.core.exceptions import ConfigurationError
from bujji.providers.base import LLMProvider
from bujji.providers.factory import get_provider, register_provider
from bujji.providers.ollama import OllamaProvider
from bujji.providers.openai_compat import OpenAICompatProvider
from bujji.providers.openrouter import OpenRouterProvider


class TestProviderFactory:
    def test_get_ollama(self, test_settings):
        test_settings.llm.provider = "ollama"
        provider = get_provider(test_settings)
        assert isinstance(provider, OllamaProvider)
        assert provider.provider_name == "ollama"

    def test_get_openai(self, test_settings):
        test_settings.llm.provider = "openai"
        test_settings.llm.api_key = "test-key"
        provider = get_provider(test_settings)
        assert isinstance(provider, OpenAICompatProvider)

    def test_get_openrouter(self, test_settings):
        test_settings.llm.provider = "openrouter"
        test_settings.llm.api_key = "test-key"
        provider = get_provider(test_settings)
        assert isinstance(provider, OpenRouterProvider)

    def test_invalid_provider(self, test_settings):
        test_settings.llm.provider = "nonexistent"
        with pytest.raises(ConfigurationError):
            get_provider(test_settings)

    def test_register_custom_provider(self, test_settings):
        class FakeProvider(LLMProvider):
            def _validate_config(self):
                pass

            async def generate(self, messages, temperature=None, max_tokens=None, stream=False):
                pass  # type: ignore

            async def generate_with_tools(self, messages, tools, temperature=None, max_tokens=None):
                pass  # type: ignore

            @property
            def provider_name(self):
                return "fake"

            @property
            def model_name(self):
                return "fake-model"

        register_provider("fake", FakeProvider)
        test_settings.llm.provider = "fake"
        provider = get_provider(test_settings)
        assert isinstance(provider, FakeProvider)


class TestOllamaProvider:
    def test_initialization(self):
        provider = OllamaProvider({"model": "llama3.2"})
        assert provider.provider_name == "ollama"
        assert provider.model_name == "llama3.2"
        assert provider.base_url == "http://localhost:11434"

    def test_custom_base_url(self):
        provider = OllamaProvider(
            {"model": "codellama", "base_url": "http://192.168.1.100:11434"}
        )
        assert provider.base_url == "http://192.168.1.100:11434"
        assert provider.model_name == "codellama"


class TestOpenAICompatProvider:
    def test_initialization(self):
        provider = OpenAICompatProvider(
            {"model": "gpt-4o", "api_key": "sk-test"}
        )
        assert provider.provider_name == "openai_compat"
        assert provider.model_name == "gpt-4o"

    def test_custom_base_url(self):
        provider = OpenAICompatProvider(
            {"model": "custom-model", "base_url": "http://localhost:8080/v1", "api_key": "test"}
        )
        assert "localhost:8080" in provider.base_url
