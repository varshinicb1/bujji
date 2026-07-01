# LLM Providers

Provider-agnostic LLM layer with pluggable backends.

## Interface

```python
class LLMProvider(ABC):
    async def generate(messages, temperature, max_tokens, stream) -> ProviderResponse
    async def generate_with_tools(messages, tools, temperature, max_tokens) -> ProviderResponse
```

## Supported Providers

| Provider | Class | Config Value |
|----------|-------|-------------|
| Ollama | `OllamaProvider` | `ollama` |
| OpenAI Compatible | `OpenAICompatProvider` | `openai` |
| OpenRouter | `OpenRouterProvider` | `openrouter` |
| Local HTTP | `OpenAICompatProvider` | `local` |

## Switching Providers

```yaml
# bujji.yaml
llm:
  provider: ollama
  model: llama3.2
  base_url: http://localhost:11434
```

To switch:

```yaml
llm:
  provider: openai
  model: gpt-4o
  api_key: ${OPENAI_API_KEY}
```

## Custom Providers

Extend `LLMProvider` and register via `register_provider()`.
