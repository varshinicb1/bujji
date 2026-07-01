# Tool System

Plugin-based tool architecture with standardized metadata and execution.

## Tool Interface

```python
class BaseTool(ABC):
    metadata: ToolMetadata       # name, description, permissions, schema
    async def execute(**kwargs) -> ToolResult  # standardized result
    async def validate_args(**kwargs)           # pre-execution validation
```

## Tool Metadata

```python
class ToolMetadata(BaseModel):
    name: str                  # Unique tool identifier
    description: str           # Human-readable description
    permissions: list[str]     # Required permissions (read, write, execute)
    requires_approval: bool    # Requires user confirmation
    schema: dict               # JSON Schema for tool calling
```

## Available Tools

| Tool | Name | Description |
|------|------|-------------|
| Filesystem | `filesystem` | Read, write, list, manage files |
| Terminal | `terminal` | Execute shell commands |
| Git | `git` | Git operations |
| GitHub | `github` | GitHub API |
| Web Search | `web_search` | Multi-provider search |
| Browser | `browser` | Playwright automation |
| Docker | `docker` | Docker commands |
| Python Exec | `python_exec` | Sandboxed Python execution |
| Documentation | `documentation` | Doc site search |

## Adding Tools

1. Extend `BaseTool`
2. Define `metadata` and implement `execute()`
3. Register via `registry.register(tool)`
