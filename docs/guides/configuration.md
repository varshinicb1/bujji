# Configuration

BUJJI supports configuration via YAML file or environment variables.

## YAML Config (`bujji.yaml`)

```yaml
llm:
  provider: ollama
  model: llama3.2
  base_url: http://localhost:11434
  temperature: 0.1
  max_tokens: 4096

memory:
  type: sqlite
  sqlite_path: ~/.bujji/memory.db
  vector_collection: bujji_memory

tools:
  browser_headless: true
  git_require_approval: true

router:
  local_threshold: 0.7

logging:
  level: INFO
```

## Environment Variables

All settings can be overridden via `BUJJI_*` environment variables:

```bash
BUJJI_LLM__PROVIDER=openai
BUJJI_LLM__MODEL=gpt-4o
BUJJI_LLM__API_KEY=sk-...
BUJJI_ROUTER__LOCAL_THRESHOLD=0.8
```

## Configuration Priority

1. Environment variables (highest)
2. YAML config file
3. Default values (lowest)
