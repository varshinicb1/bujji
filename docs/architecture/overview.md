# Architecture Overview

BUJJI follows a clean architecture pattern with clear separation of concerns.

## System Diagram

```
┌─────────────────────────────────────────────────────┐
│                      CLI / API                       │
├─────────────────────────────────────────────────────┤
│                      Agent                           │
├──────────┬──────────┬──────────┬────────────────────┤
│  Planner │  Router  │  Memory  │    Tool Registry    │
├──────────┴──────────┴──────────┴────────────────────┤
│                   LLM Service                        │
├─────────────────────────────────────────────────────┤
│               Provider Abstraction                   │
├──────────┬──────────┬──────────┬────────────────────┤
│  Ollama  │  OpenAI  │ OpenRouter │    Local HTTP     │
└──────────┴──────────┴──────────┴────────────────────┘
```

## Core Components

1. **Agent** - Orchestrates all subsystems
2. **Planner** - Breaks tasks into structured plans
3. **Router** - Decides local vs. escalated execution
4. **Memory** - Persistent storage with semantic retrieval
5. **LLM Service** - High-level wrapper for providers
6. **Tool Registry** - Plugin system for tool execution

## Design Decisions

- **LangGraph** for agent workflow orchestration
- **Pydantic** for all data validation
- **SQLite + ChromaDB** for dual memory storage
- **Provider abstraction** for LLM flexibility
- **Plugin architecture** for extensible tools
