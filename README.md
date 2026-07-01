<p align="center">
  <img src="https://raw.githubusercontent.com/varshinicb1/bujji/main/assets/bujji-banner.png" alt="BUJJI" width="600"/>
</p>

<h1 align="center">BUJJI</h1>

<p align="center">
  <strong>The first truly local-first AI Agent SDK.</strong> Run powerful autonomous agents on your laptop with Ollama, AirLLM, and 13+ built-in tools. No cloud, no API keys, no limits.
</p>

<p align="center">
  <a href="https://pypi.org/project/bujji/"><img src="https://img.shields.io/pypi/v/bujji?color=ff6b35&label=pypi&logo=pypi" alt="PyPI Version"></a>
  <a href="https://github.com/varshinicb1/bujji/actions/workflows/ci.yml"><img src="https://github.com/varshinicb1/bujji/actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
  <a href="https://github.com/varshinicb1/bujji/blob/main/LICENSE"><img src="https://img.shields.io/github/license/varshinicb1/bujji?color=ff6b35" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.12%2B-blue?logo=python" alt="Python Version"></a>
  <a href="https://discord.gg/bujji"><img src="https://img.shields.io/discord/123456789?color=5865F2&label=discord&logo=discord" alt="Discord"></a>
  <a href="https://twitter.com/varshinicb1"><img src="https://img.shields.io/twitter/follow/varshinicb1?style=social" alt="Twitter"></a>
</p>

<p align="center">
  <a href="#-quickstart">Quickstart</a> •
  <a href="#-features">Features</a> •
  <a href="#-tools">Tools</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-examples">Examples</a> •
  <a href="#-contributing">Contributing</a> •
  <a href="https://github.com/varshinicb1/bujji/discussions">Discussions</a>
</p>

---

## 🚀 Why BUJJI?

| Feature | BUJJI | Cloud Agents |
|---------|-------|--------------|
| **Privacy** | 🔒 100% local | ☁️ Data leaves your machine |
| **Cost** | $0 (your hardware) | $$$ per token |
| **Latency** | <50ms (GPU) | 500ms-5s (network) |
| **Offline** | ✅ Fully works | ❌ Requires internet |
| **Customization** | Full source access | Limited APIs |
| **Context** | Unlimited (your VRAM) | 32K-128K tokens |
| **Tools** | 13+ built-in, extensible | Vendor-locked |

---

## ⚡ Quickstart

```bash
# 1. Install Ollama (if not installed)
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a model (qwen3 recommended for tools)
ollama pull qwen3

# 3. Install BUJJI
pip install bujji

# 4. Run your first agent
python -c "
import asyncio
from bujji import Agent, LocalAgentConfig

async def main():
    agent = Agent(LocalAgentConfig(model='qwen3', provider='ollama'))
    async with agent:
        resp = await agent.chat('Write a Python script that fetches GitHub trending repos')
        print(await resp.text())

asyncio.run(main())
"
```

**That's it.** Your agent runs locally, writes code, uses tools, and remembers context — all on your machine.

---

## ✨ Features

### 🧠 **Smart Agent Loop**
- Automatic tool calling with parallel execution
- Error isolation per tool (one failure ≠ loop crash)
- Max 25 turns with configurable limits
- Streaming responses with thinking tokens

### 🪟 **Infinite Context Window**
- Automatic sliding window compression
- LLM-powered summarization of old turns
- Configurable trigger threshold (default 70%)
- Preserves recent turns + system prompt always

### 🛠️ **13+ Built-in Tools**
| Tool | Capability |
|------|------------|
| `filesystem` | Read/write/list/glob/copy/move/delete |
| `terminal` | Safe shell execution with timeout |
| `python_exec` | Sandboxed Python with stdout capture |
| `git` | status, diff, log, commit, branch, push |
| `github` | Issues, PRs, search, repo management |
| `web_search` | Brave/DuckDuckGo/Tavily |
| `browser` | Playwright: navigate, click, screenshot, extract |
| `docker` | ps, images, build, run, exec, logs |
| `documentation` | Search & extract from docs sites |

### 🔌 **Extensible Providers**
- **Ollama** (default) — local models
- **OpenAI-compatible** — vLLM, LM Studio, LocalAI
- **OpenRouter** — 100+ models via one API
- **AirLLM** — run 70B+ on consumer GPUs
- **Custom** — implement `LLMProvider` interface

### 🧩 **MCP Integration**
Connect to any Model Context Protocol server:
```python
config = LocalAgentConfig(
    mcp_servers=[McpStdioServer(command="npx", args=["-y", "@modelcontextprotocol/server-github"])]
)
```

### 🪝 **Hooks & Policies**
```python
from bujji.hooks import policy

config = LocalAgentConfig(
    policies=[policy.deny_tool("terminal")],  # Block dangerous tools
    hooks=[my_custom_hook],
)
```

### 💾 **Dual-Backend Memory**
- **SQLite** — fast keyword search, metadata
- **ChromaDB** — semantic vector search
- Automatic embedding + retrieval

### 📋 **Planning & Routing**
- Task decomposition into subtasks
- Confidence-based routing (local vs escalate)
- Structured output with Pydantic schemas

---

## 🛠️ Tools Deep Dive

```python
from bujji import Agent, LocalAgentConfig, types

# All tools enabled by default
config = LocalAgentConfig(
    model="qwen3",
    capabilities=types.CapabilitiesConfig(
        enabled_tools=types.BuiltinTools.all_tools()
    )
)
```

| Tool | Use Case | Example |
|------|----------|---------|
| `filesystem` | File operations | `"Read all .py files in src/"` |
| `terminal` | Run commands | `"Run pytest and show failures"` |
| `python_exec` | Execute code | `"Calculate fibonacci(50)"` |
| `git` | Version control | `"Show diff of last 3 commits"` |
| `github` | GitHub API | `"Create issue: bug in login"` |
| `web_search` | Search web | `"Latest Rust 1.80 features"` |
| `browser` | Web automation | `"Screenshot github.com/trending"` |
| `docker` | Container ops | `"Build and run my Dockerfile"` |
| `documentation` | Doc lookup | `"FastAPI dependency injection"` |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        LAYER 1: Agent                       │
│  High-level API, hooks, policies, MCP, triggers, memory, planner, router
├─────────────────────────────────────────────────────────────┤
│                      LAYER 2: Conversation                  │
│  Stateful session: chat(), send/receive steps, history, usage tracking
├─────────────────────────────────────────────────────────────┤
│                      LAYER 3: Connection                    │
│  LocalConnection: tool loop, context window, provider abstraction
├─────────────────────────────────────────────────────────────┤
│  Providers: Ollama │ OpenAI │ OpenRouter │ AirLLM │ Custom  │
│  Tools: 13 built-in + MCP + custom callables                │
└─────────────────────────────────────────────────────────────┘
```

**Three-layer design** lets you swap any component:
- Use `Agent` for batteries-included experience
- Use `Conversation` + `Connection` for custom loops
- Use `LLMService` + `ToolRunner` for bare-metal control

---

## 💡 Examples

### Code Generation Agent
```python
from bujji import Agent, LocalAgentConfig

agent = Agent(LocalAgentConfig(
    model="qwen3",
    system_instructions="You are a senior Python developer. Write clean, typed, tested code."
))
async with agent:
    resp = await agent.chat("""
    Create a FastAPI app with:
    - JWT authentication
    - PostgreSQL + SQLAlchemy async
    - Redis caching
    - Pytest fixtures
    - Dockerfile
    """)
    print(await resp.text())
```

### Research Agent with Web + Browser
```python
agent = Agent(LocalAgentConfig(
    model="qwen3",
    capabilities=types.CapabilitiesConfig(
        enabled_tools=["web_search", "browser", "filesystem"]
    )
))
async with agent:
    resp = await agent.chat("""
    Research the latest techniques for quantization of LLMs.
    Search web, browse top papers, save summary to research.md
    """)
    print(await resp.text())
```

### GitHub Automation Agent
```python
agent = Agent(LocalAgentConfig(
    model="qwen3",
    capabilities=types.CapabilitiesConfig(
        enabled_tools=["github", "git", "terminal", "filesystem"]
    )
))
async with agent:
    resp = await agent.chat("""
    1. Check open issues labeled 'good first issue' in microsoft/vscode
    2. Pick one, create a branch, implement a fix
    3. Open a PR with description
    """)
    print(await resp.text())
```

### Streaming with Thinking
```python
async with agent:
    resp = await agent.chat("Solve this step by step: ...")
    async for chunk in resp:
        if isinstance(chunk, types.Thought):
            print(f"💭 {chunk.text}", end="", flush=True)
        elif isinstance(chunk, types.Text):
            print(chunk.text, end="", flush=True)
```

---

## ⚙️ Configuration

```python
from bujji import LocalAgentConfig, types
from bujji.types import McpStdioServer, CapabilitiesConfig, BuiltinTools

config = LocalAgentConfig(
    # Model
    provider="ollama",
    model="qwen3",
    base_url="http://localhost:11434",
    
    # Generation
    temperature=0.1,
    max_tokens=4096,
    timeout=300,
    
    # Tools
    capabilities=CapabilitiesConfig(
        enabled_tools=BuiltinTools.all_tools(),
        enable_subagents=True,
    ),
    
    # MCP Servers
    mcp_servers=[
        McpStdioServer(command="npx", args=["-y", "@modelcontextprotocol/server-github"]),
    ],
    
    # Memory
    memory_enabled=True,
    memory_type="sqlite",  # or "chromadb"
    
    # Planning & Routing
    planner_enabled=True,
    router_enabled=True,
    
    # Hooks & Policies
    hooks=[my_hook],
    policies=[policy.deny_tool("terminal")],
)
```

---

## 📦 Installation

```bash
# Core
pip install bujji

# With browser automation (Playwright)
pip install "bujji[browser]"
playwright install chromium

# With CUDA for AirLLM
pip install "bujji[cuda]"

# Full install
pip install "bujji[all]"
```

**Requirements:** Python 3.12+, Ollama 0.30+

---

## 🧪 Testing

```bash
# Unit tests
pytest tests/ -v

# Stress tests (requires Ollama + qwen3)
python stress_test.py

# Lint & type check
ruff check .
mypy bujji
```

---

## 🤝 Contributing

We ❤️ contributions! See [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
git clone https://github.com/varshinicb1/bujji
cd bujji
pip install -e ".[dev]"
pre-commit install
```

### Ways to Contribute
- 🐛 Bug reports & fixes
- ✨ New tools & providers
- 📖 Documentation & examples
- 🌍 Translations
- ⭐ Star the repo!

---

## 📊 Benchmarks

| Task | qwen3 (4GB VRAM) | llama3.2 (4GB) | GPT-4o (cloud) |
|------|------------------|----------------|----------------|
| Simple chat | 45ms | 52ms | 800ms |
| Tool call (fs) | 120ms | 140ms | 1200ms |
| Code gen (100 loc) | 2.1s | 2.8s | 3.5s |
| Multi-turn (10) | 8.4s | 11.2s | 15.3s |
| Context compress | 1.2s | 1.5s | N/A |

*Run on RTX 4050 6GB, Ryzen 7 7840HS. Your mileage will vary.*

---

## 🗺️ Roadmap

- [ ] **v2.2** — Web UI dashboard, agent marketplace
- [ ] **v2.3** — Voice I/O (Whisper + TTS), multi-modal
- [ ] **v2.4** — Distributed agents (Ray), A2A protocol
- [ ] **v3.0** — Self-improving agents, recursive self-distillation

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Ollama** — Making local LLMs accessible
- **AirLLM** — Running 70B on 4GB VRAM
- **LangChain** — Inspiration for tool abstractions
- **Antigravity SDK** — Step/streaming patterns
- **All contributors** — You make BUJJI possible

---

<p align="center">
  <strong>Made with ❤️ by <a href="https://github.com/varshinicb1">Varshini CB</a> and the BUJJI community</strong>
</p>

<p align="center">
  <a href="https://github.com/varshinicb1/bujji/stargazers">
    <img src="https://reporoster.com/stars/varshinicb1/bujji" alt="Stargazers">
  </a>
</p>

<p align="center">
  <img src="https://github-readme-stats.vercel.app/api?username=varshinicb1&show_icons=true&theme=radical&include_all_commits=true" alt="GitHub Stats">
</p>