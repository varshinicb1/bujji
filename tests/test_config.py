import tempfile
from pathlib import Path

import pytest
import yaml

from bujji.core.config import Settings, load_config


class TestSettings:
    def test_default_settings(self):
        settings = Settings()
        assert settings.llm.provider == "ollama"
        assert settings.llm.model == "qwen2.5:0.5b"
        assert settings.memory.type == "sqlite"
        assert settings.router.local_threshold == 0.7
        assert settings.logging.level == "INFO"

    def test_env_prefix(self, monkeypatch):
        monkeypatch.setenv("BUJJI_LLM__PROVIDER", "openai")
        monkeypatch.setenv("BUJJI_LLM__MODEL", "gpt-4o")
        settings = Settings()
        assert settings.llm.provider == "openai"
        assert settings.llm.model == "gpt-4o"

    def test_path_resolution(self):
        settings = Settings()
        settings.resolve_paths()
        resolved = Path(settings.memory.sqlite_path)
        assert resolved.is_absolute()
        assert not str(resolved).startswith("~")


class TestLoadConfig:
    def test_load_from_yaml(self):
        config_data = {
            "llm": {"provider": "openrouter", "model": "claude-sonnet"},
            "router": {"local_threshold": 0.8},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            settings = load_config(config_path)
            assert settings.llm.provider == "openrouter"
            assert settings.llm.model == "claude-sonnet"
            assert settings.router.local_threshold == 0.8
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_load_nonexistent_file(self):
        settings = load_config("/nonexistent/bujji.yaml")
        assert isinstance(settings, Settings)

    def test_settings_immutable_types(self):
        settings = Settings()
        assert isinstance(settings.llm.temperature, float)
        assert isinstance(settings.llm.max_tokens, int)
        assert isinstance(settings.llm.timeout, int)
