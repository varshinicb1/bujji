# Core Components

## Config (`bujji/core/config.py`)

Settings management using Pydantic Settings.

- Environment variables via `BUJJI_*` prefix
- YAML file support via `bujji.yaml`
- Auto path resolution

## Models (`bujji/core/models.py`)

All shared data models:

- `Message` - Chat messages with role/content
- `ToolCall` / `ToolResult` - Tool execution data
- `Plan` / `Subtask` - Planning structures
- `MemoryEntry` - Memory storage model
- `ProviderResponse` - LLM response wrapper
- `RouterDecision` - Routing decisions
- `ChatRequest` / `ChatResponse` - API models

## Exceptions (`bujji/core/exceptions.py`)

Hierarchical exception system:

- `BUJJIError` - Base exception
- `ConfigurationError` - Invalid config
- `ProviderError` - LLM provider failures
- `ToolError` - Tool execution failures
- `MemoryError` - Memory operation failures
- `PlanningError` - Task planning failures
- `RoutingError` - Routing decision failures
