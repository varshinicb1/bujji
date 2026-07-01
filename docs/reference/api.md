# API Reference

## Base URL

```
http://localhost:8000
```

## Endpoints

### `GET /`

Service status.

```json
{"service": "BUJJI", "version": "1.0.0", "status": "running"}
```

### `POST /chat`

Send a message to BUJJI.

```json
{
  "message": "What's in this project?",
  "conversation_id": null,
  "stream": false
}
```

### `POST /plan`

Create a plan for a task.

```json
{"task": "Add user authentication"}
```

### `GET /tools`

List available tools.

### `POST /memory/search`

Search memory entries.

```json
{"query": "architecture", "limit": 10, "entry_type": null, "semantic": true}
```

### `POST /memory/store`

Store a memory entry.

```json
{"content": "Using FastAPI 0.115", "entry_type": "architecture", "metadata": {}}
```

### `GET /providers`

List available LLM providers.

### `GET /status`

Get system status.
