# Memory System

Dual-backend memory for structured and semantic retrieval.

## Architecture

```
MemoryManager
├── SQLiteMemory    (structured queries, metadata filtering)
└── VectorMemory    (semantic search, embeddings)
```

## SQLite Backend

- Persistent relational storage
- WAL mode for performance
- Indexed by type and timestamp
- Full-text search via LIKE

## Vector Backend (ChromaDB)

- Semantic similarity search
- Cosine distance metric
- Automatic content embedding
- Type-based filtering

## Memory Types

| Type | Purpose |
|------|---------|
| `conversation` | Chat history |
| `project` | Project summaries |
| `architecture` | Architecture decisions |
| `convention` | Coding conventions |
| `todo` | Task tracking |
| `api` | API documentation |
| `database` | Database schemas |
