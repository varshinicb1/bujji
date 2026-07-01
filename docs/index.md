# BUJJI

**AI Engineering Assistant for OpenCode**

BUJJI is a production-grade AI engineering assistant designed to augment OpenCode.
It researches, plans, remembers, executes tools, validates work, and escalates
difficult reasoning to stronger models when necessary.

## Core Principles

- **Modular architecture** - Clean separation of concerns
- **Extensible plugin system** - Add capabilities without rewrites
- **Provider-agnostic LLM** - Switch providers with config changes
- **Local-first** - Run entirely on your machine
- **Privacy-first** - No data leaves your control
- **Production-ready** - Comprehensive testing and error handling

## Quick Start

```bash
# Install
uv pip install bujji

# Start the API
uvicorn bujji.api.server:app

# Use the CLI
bujji chat "What's in this project?"
```

## Documentation

- [Architecture Overview](architecture/overview.md)
- [Installation Guide](guides/installation.md)
- [Configuration](guides/configuration.md)
- [API Reference](reference/api.md)
- [CLI Reference](reference/cli.md)
