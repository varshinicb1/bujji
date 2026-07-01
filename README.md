# BUJJI v2.0

**Local-first AI Agent SDK — Ollama + AirLLM on your laptop**

BUJJI is a production-grade AI agent SDK that runs fully locally on your machine. It combines a modular 3-layer architecture (Agent → Conversation → Connection) with provider-agnostic LLM support, tool execution, hooks, triggers, MCP server integration, and a dual-model router for intelligent model selection.

## One-Command Install

```bash
pip install bujji
ollama pull qwen3
bujji chat "Write a prime number checker in Python"
```

## Features

- **100% Local**: All inference runs on-device via Ollama or AirLLM. No cloud dependency.
- **Dual-Model Router**: Simple tasks use fast Ollama models (Qwen2.5-Coder:7b); complex reasoning escalates to AirLLM (Qwen3-32B, DeepSeek-V3) — all on a 6GB GPU.
- **Provider-Agnostic**: Supports Ollama, OpenAI-compatible APIs, OpenRouter, AirLLM, and custom providers.
- **3-Layer Architecture**: `Agent` (high-level API) → `Conversation` (stateful session) → `Connection` (transport abstraction).
- **Rich Tool System**: Custom Python tools, built-in filesystem/shell tools, and MCP server integration.
- **Hook & Policy System**: Pre/post hooks, safety policies, workspace scoping.
- **Trigger System**: Time-based, event-based, and interval triggers for scheduled agent execution.
- **Memory & Persistence**: SQLite and ChromaDB backends with conversation history management.

## Architecture

```
┌─────────────┐
│    Agent    │  High-level API (async context manager)
├─────────────┤
│ Conversation│  Stateful session with step history, compaction, usage tracking
├─────────────┤
│  Connection │  Transport abstraction (Ollama, AirLLM, OpenAI, OpenRouter)
├─────────────┤
│  Providers  │  LLM backends: ollama, airllm, openai, openrouter, local
├─────────────┤
│  Router     │  Intelligent model selection (fast ↔ god-tier)
├─────────────┤
│ Tools/Hooks │  Custom tools, MCP servers, safety policies, triggers
└─────────────┘
```

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run the agent
python examples/quickstart.py
```

### Basic Usage

```python
import asyncio
from bujji.agent import Agent
from bujji.connections.local.config import LocalAgentConfig

async def main():
    config = LocalAgentConfig(model="qwen2.5-coder:7b")
    async with Agent(config) as agent:
        response = await agent.chat("Write a prime number checker in Python")
        print(await response.text())

asyncio.run(main())
```

### Streaming

```python
async with Agent(config) as agent:
    response = await agent.chat("Explain async/await")
    async for chunk in response:
        print(chunk, end="", flush=True)
```

### Custom Tools

```python
from bujji.tools.base import tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Sunny, 25°C in {city}"

config = LocalAgentConfig(model="qwen2.5-coder:7b", tools=[get_weather])
```

### AirLLM God-Tier Mode

```bash
# Requires Python 3.12 with CUDA torch
py -3.12 -m pip install airllm
py -3.12 examples/airllm_god_mode.py
```

## Provider Configuration

| Provider | Config | Description |
|----------|--------|-------------|
| Ollama | `provider="ollama"` | Local models via Ollama (default) |
| AirLLM | `provider="airllm"` | Massive models on tiny GPUs (Qwen3-32B, DeepSeek-V3) |
| OpenAI | `provider="openai"` | OpenAI API-compatible |
| OpenRouter | `provider="openrouter"` | OpenRouter API |

```python
LocalAgentConfig(model="qwen2.5-coder:7b", provider="ollama")
LocalAgentConfig(model="qwen3-32b", provider="airllm")  # Python 3.12 only
```

## Models

| Model | Size | Provider | Use Case |
|-------|------|----------|----------|
| Qwen2.5-Coder:7b | 4.7 GB | Ollama | Primary — fast, reliable coding |
| Qwen3-32B | ~20 GB | AirLLM | God-tier complex reasoning |
| DeepSeek-V3 | 671B | AirLLM | Maximum intelligence |

All models fit on an RTX 4050 (6GB VRAM) thanks to AirLLM's layer-by-layer loading.

## Python Version Support

- **Python 3.14**: Default runtime, CPU torch (BUJJI core, Ollama provider)
- **Python 3.12**: CUDA runtime with PyTorch 2.5.1+cu121 (AirLLM provider, heavy models)

Use `py -3.12` for AirLLM and `python` (3.14) for everything else.

## Examples

See the `examples/` directory:

- `quickstart.py` — Minimal agent
- `streaming_chat.py` — Real-time token streaming
- `agent_with_tools.py` — Custom Python tools
- `airllm_god_mode.py` — AirLLM Qwen3-32B on 6GB GPU

## Tests

```bash
pytest tests/ -v
```

48 tests covering config, models, providers, router, planner, tools, and more.

## License

MIT
