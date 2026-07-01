# BUJJI

<div align="center">

![BUJJI Logo](https://raw.githubusercontent.com/varshinicb1/bujji/main/assets/logo.png)

**The first truly local-first AI Agent SDK. Run powerful agents on your laptop with zero cloud dependency.**

[![PyPI version](https://img.shields.io/pypi/v/bujji.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/bujji/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/varshinicb1/bujji/ci.yml?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/varshinicb1/bujji/actions/workflows/ci.yml)
[![Ollama](https://img.shields.io/badge/Ollama-ready-orange.svg?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com)
[![Stars](https://img.shields.io/github/stars/varshinicb1/bujji?style=for-the-badge&logo=github&logoColor=white)](https://github.com/varshinicb1/bujji/stargazers)
[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/bujji)

</div>

---

## Why BUJJI?

| Feature | Others | BUJJI |
|---------|--------|-------|
| **Runs locally** | ❌ Cloud required | ✅ **100% local** |
| **Your data stays yours** | ❌ Sent to APIs | ✅ **Never leaves your machine** |
| **Works offline** | ❌ Internet required | ✅ **Air-gapped ready** |
| **GPU acceleration** | ❌ CPU only | ✅ **CUDA / Metal / ROCm** |
| **13+ built-in tools** | 2-3 tools | ✅ **Filesystem, Git, GitHub, Browser, Docker, Python, Terminal, Web Search, Docs, MCP** |
| **Context window mgmt** | Manual truncation | ✅ **Auto sliding window + LLM summarization** |
| **Parallel tool calls** | Sequential only | ✅ **Batched execution** |
| **Setup time** | 30 min + API keys | ✅ **`pip install bujji && ollama pull qwen3` → Done** |

---

## Quick Start

```bash
# 1. Install
pip install bujji

# 2. Pull a model (one-time, ~5GB)
ollama pull qwen3

# 3. Run your first agent
python -c "
import asyncio
from bujji import Agent, LocalAgentConfig

async def main():
    agent = Agent(LocalAgentConfig(model='qwen3'))
    async with agent:
        resp = await agent.chat('Write a Python function to calculate fibonacci numbers')
        print(await resp.text())

asyncio.run(main())
"
```

**That's it. No API keys. No cloud accounts. No Docker. Just works.**

---

## Built-in Tools (13+)

| Tool | Capability |
|------|------------|
| 📁 **Filesystem** | Read, write, list, glob, copy, move, delete files |
| 🔧 **Terminal** | Execute shell commands safely with timeout |
| 🐍 **Python Exec** | Run Python code in sandboxed subprocess |
| 🐳 **Docker** | Manage containers, images, builds, logs |
| 🌿 **Git** | status, diff, log, commit, branch, push, pull |
| 🐙 **GitHub** | Issues, PRs, repos, search via REST API |
| 🌐 **Web Search** | Brave, DuckDuckGo, Tavily providers |
| 📖 **Documentation** | Search & extract from Python, FastAPI, web docs |
| 🎭 **Browser** | Playwright automation: navigate, click, screenshot, extract |
| 🧠 **MCP** | Connect to any Model Context Protocol server |
| 📦 **Sub-agents** | Spawn child agents for complex tasks |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AGENT (Layer 1)                       │
│  High-level API: chat(), structured_output(), run_tools()  │
├─────────────────────────────────────────────────────────────┤
│                    CONVERSATION (Layer 2)                   │
│  Stateful session: history, streaming, usage, compaction   │
├─────────────────────────────────────────────────────────────┤
│                     CONNECTION (Layer 3)                    │
│  Transport: Local (Ollama/AirLLM) | Remote (OpenAI-compat) │
├─────────────────────────────────────────────────────────────┤
│  TOOLS  │  MEMORY  │  PLANNER  │  ROUTER  │  HOOKS  │ MCP  │
└─────────────────────────────────────────────────────────────┘
```

---

## Context Window Management

**Never hit token limits again.** BUJJI automatically manages conversation history:

```python
from bujji import ContextWindowManager, create_context_manager

# Automatic sliding window + LLM summarization
mgr = create_context_manager(model_name="qwen3", max_tokens=131072)

# In your connection, it just works:
# - Tracks token usage in real-time
# - Compresses old turns when >70% full
# - Preserves recent N turns intact
# - Uses LLM to semantically summarize discarded history
# - Tool calls & results included in summaries
```

---

## Advanced Usage

### Structured Outputs

```python
from pydantic import BaseModel
from bujji import Agent, LocalAgentConfig

class CodeReview(BaseModel):
    score: int
    issues: list[str]
    suggestions: list[str]

agent = Agent(LocalAgentConfig(
    model="qwen3",
    response_schema=CodeReview,
))
async with agent:
    result = await agent.chat("Review this code: ...")
    review: CodeReview = result.structured_output()
    print(f"Score: {review.score}/10")
```

### Parallel Tool Execution

```python
# Multiple independent tool calls run in parallel automatically
resp = await agent.chat("""
Read these 3 files in parallel:
- src/main.py
- src/utils.py
- tests/test_main.py
""")
```

### MCP Integration

```python
from bujji.types import McpStdioServer

agent = Agent(LocalAgentConfig(
    model="qwen3",
    mcp_servers=[
        McpStdioServer(command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"])
    ],
))
```

### AirLLM (LLM on CPU/GPU without Ollama)

```python
agent = Agent(LocalAgentConfig(
    provider="airllm",
    model="meta-llama/Llama-3.2-3B-Instruct",
))
```

---

## Providers Supported

| Provider | Models | Hardware |
|----------|--------|----------|
| **Ollama** | llama3, qwen3, mistral, deepseek, phi3, custom GGUF | GPU/CPU |
| **AirLLM** | Any HF model (Llama, Qwen, Mistral, etc.) | GPU/CPU (4-bit) |
| **OpenAI-compat** | vLLM, LM Studio, LocalAI, TGI | GPU |
| **OpenRouter** | 100+ models via API | Cloud |
| **Custom HTTP** | Your own endpoint | Any |

---

## Configuration

```yaml
# bujji.yaml
provider: ollama
model: qwen3
temperature: 0.1
max_tokens: 8192
timeout: 300
memory_enabled: true
memory_type: sqlite
planner_enabled: true
router_enabled: true
capabilities:
  enabled_tools:
    - filesystem
    - terminal
    - python_exec
    - git
    - github
    - web_search
    - browser
```

```python
from bujji.config import load_config
from bujji import Agent

config = load_config("bujji.yaml")
agent = Agent(config)
```

---

## CLI

```bash
# Interactive chat
bujji chat --model qwen3

# One-shot
bujji run "Write a REST API in FastAPI" --model qwen3

# With tools
bujji run "Create a git repo and commit all files" --tools filesystem,git

# Structured output
bujji run "Analyze this code" --schema schemas/code_review.json
```

---

## Python API Reference

```python
from bujji import (
    Agent,
    LocalAgentConfig,
    ContextWindowManager,
    create_context_manager,
    types,
    BuiltinTools,
    CapabilitiesConfig,
    ToolContext,
    policy,
    hooks,
)
```

### Key Types

```python
# All tools available
BuiltinTools.all_tools()  # -> list of 13 tool names

# Capabilities control
CapabilitiesConfig(
    enabled_tools=["filesystem", "terminal"],  # allow only these
    # disabled_tools=["docker"],  # or block specific
    enable_subagents=True,
)

# Multimodal content
from bujji.types import Image, Document, Audio, Video, from_file
content = [from_file("chart.png"), "Analyze this chart"]
```

---

## Contributing

We welcome contributions! 

```bash
git clone https://github.com/varshinicb1/bujji
cd bujji
pip install -e ".[dev]"
pre-commit install
pytest tests/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Roadmap

- [ ] **v2.2** - Voice I/O (Whisper + TTS), WebSocket server
- [ ] **v2.3** - Agent swarm orchestration, A2A protocol
- [ ] **v2.4** - Fine-tuning pipeline (LoRA/QLoRA on consumer GPUs)
- [ ] **v3.0** - WASM sandbox for browser-based agents

---

## Community

- ⭐ **Star us** on GitHub — it helps!
- 🐛 **Report bugs** in [Issues](https://github.com/varshinicb1/bujji/issues)
- 💡 **Request features** in [Discussions](https://github.com/varshinicb1/bujji/discussions)
- 💬 **Join Discord** — [discord.gg/bujji](https://discord.gg/bujji)
- 🐦 **Follow** [@varshinicb1](https://twitter.com/varshinicb1)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ by [Varshini CB](https://github.com/varshinicb1)**

*Run agents locally. Own your data. Build the future.*

</div>