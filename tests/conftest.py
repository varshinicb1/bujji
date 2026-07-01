import pytest

from bujji.core.config import Settings
from bujji.core.models import Message, Role


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        llm={"provider": "ollama", "model": "llama3.2", "base_url": "http://localhost:11434"},
        memory={"sqlite_path": ":memory:", "chroma_path": "/tmp/bujji_test_chroma"},
        router={"local_threshold": 0.7},
    )


@pytest.fixture
def sample_messages() -> list[Message]:
    return [
        Message(role=Role.system, content="You are a helpful assistant."),
        Message(role=Role.user, content="What is Python?"),
    ]
