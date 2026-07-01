# Installation

## Prerequisites

- Python 3.12+
- UV package manager

## Install from Source

```bash
git clone <repo-url>
cd bujji
uv pip install -e .
```

## Install with Browser Support

```bash
uv pip install -e ".[browser]"
playwright install chromium
```

## Install with Development Tools

```bash
uv pip install -e ".[dev]"
```

## Docker

```bash
docker compose up -d
```

## Configuration

Copy `.env.example` to `.env` and adjust:

```bash
cp .env.example .env
# Edit .env with your settings
```
