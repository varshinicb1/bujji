from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from yaml import safe_load


class LLMProviderConfig(BaseSettings):
    provider: Literal["ollama", "openai", "openrouter", "anthropic", "local", "airllm"] = "ollama"
    model: str = "qwen3"
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 60


class MemoryConfig(BaseSettings):
    type: Literal["sqlite", "postgresql"] = "sqlite"
    sqlite_path: str = "~/.bujji/memory.db"
    vector_collection: str = "bujji_memory"
    chroma_path: str = "~/.bujji/chromadb"
    embedding_model: str = "all-MiniLM-L6-v2"


class ToolsConfig(BaseSettings):
    browser_headless: bool = True
    terminal_sandbox: bool = True
    git_require_approval: bool = True
    max_command_timeout: int = 300


class RouterConfig(BaseSettings):
    local_threshold: float = 0.7
    max_local_tokens: int = 4096
    escalation_endpoint: str | None = None


class LoggingConfig(BaseSettings):
    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level:<7} | {name}:{function}:{line} | {message}"
    rotation: str = "10 MB"
    retention: str = "30 days"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BUJJI_",
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    debug: bool = False
    project_root: str = "."

    llm: LLMProviderConfig = LLMProviderConfig()
    memory: MemoryConfig = MemoryConfig()
    tools: ToolsConfig = ToolsConfig()
    router: RouterConfig = RouterConfig()
    logging: LoggingConfig = LoggingConfig()

    def resolve_paths(self) -> None:
        self.memory.sqlite_path = str(
            Path(self.memory.sqlite_path).expanduser().resolve()
        )
        self.memory.chroma_path = str(
            Path(self.memory.chroma_path).expanduser().resolve()
        )
        self.project_root = str(Path(self.project_root).expanduser().resolve())


def load_config(path: str | None = None) -> Settings:
    settings = Settings()

    if path:
        path_obj = Path(path).expanduser().resolve()
        if path_obj.exists():
            with open(path_obj) as f:
                data = safe_load(f)
            if data:
                for section, values in data.items():
                    if hasattr(settings, section) and isinstance(values, dict):
                        for key, val in values.items():
                            if hasattr(getattr(settings, section), key):
                                setattr(getattr(settings, section), key, val)

    settings.resolve_paths()
    return settings
