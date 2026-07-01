"""Tests for ContextWindowManager."""

from bujji.memory.context_window import (
    ContextWindowManager,
    estimate_tokens,
    estimate_message_tokens,
    create_context_manager,
)
from bujji.core.models import Message, Role, ToolCall


def _msg(role: str, content: str, tool_calls=None, name=None) -> Message:
    return Message(role=Role(role), content=content, tool_calls=tool_calls, name=name)


def test_estimate_tokens():
    assert estimate_tokens("hello") == 1
    assert estimate_tokens("a" * 400) == 100


def test_estimate_message_tokens():
    m = _msg("user", "hello world")
    assert estimate_message_tokens(m) >= 1

    m2 = _msg("assistant", "some content", tool_calls=[
        ToolCall(id="1", name="test_tool", arguments={"key": "value"}),
    ])
    assert estimate_message_tokens(m2) >= 1


def test_create_manager():
    mgr = create_context_manager("qwen3")
    assert mgr._model_limit == 131072
    assert mgr._trigger_threshold == int(131072 * 0.70)


def test_no_compression_needed():
    mgr = create_context_manager("qwen3", max_tokens=1000000)
    messages = [_msg("user", "hello"), _msg("assistant", "world")]
    mgr.track_messages(messages)
    assert not mgr.needs_compression
    result = mgr.compress(messages)
    assert len(result) == len(messages)


def test_compression_removes_middle():
    mgr = ContextWindowManager("qwen3", max_tokens=50, trigger_ratio=0.5, min_turns_to_keep=2)
    messages = [
        _msg("system", "You are helpful."),
        _msg("user", "old message 1 that is very long and takes up tokens"),
        _msg("assistant", "response 1 that is very long and takes up tokens"),
        _msg("user", "old message 2 that is very long and takes up tokens"),
        _msg("assistant", "response 2 that is very long and takes up tokens"),
        _msg("user", "old message 3 that is very long and takes up tokens"),
        _msg("assistant", "response 3 that is very long and takes up tokens"),
        _msg("user", "recent message"),
        _msg("assistant", "recent response"),
    ]
    mgr.track_messages(messages)
    assert mgr.needs_compression
    result = mgr.compress(messages)
    assert len(result) < len(messages)
    assert any("Compressed" in m.content for m in result if m.role == Role.system)


def test_compression_preserves_recent():
    mgr = create_context_manager("qwen3", max_tokens=150)
    messages = [
        _msg("system", "You are helpful."),
        _msg("user", "old msg 1"), _msg("assistant", "resp 1"),
        _msg("user", "old msg 2"), _msg("assistant", "resp 2"),
        _msg("user", "old msg 3"), _msg("assistant", "resp 3"),
        _msg("user", "old msg 4"), _msg("assistant", "resp 4"),
        _msg("user", "recent msg"), _msg("assistant", "recent resp"),
    ]
    mgr.track_messages(messages)
    compressed = mgr.compress(messages)
    uncompressed_user_msgs = [m.content for m in compressed if m.role == Role.user]
    assert "recent msg" in uncompressed_user_msgs


def test_available_tokens():
    mgr = create_context_manager("qwen3", max_tokens=1000)
    assert mgr.available == 1000 - 8192
    mgr._current_usage = 500
    assert mgr.available == 1000 - 500 - 8192


def test_track_messages():
    mgr = create_context_manager("qwen3")
    messages = [_msg("system", "a" * 400), _msg("user", "b" * 400)]
    mgr.track_messages(messages)
    assert mgr.usage > 0


def test_tool_call_in_summary():
    mgr = ContextWindowManager("qwen3", max_tokens=50, trigger_ratio=0.5, min_turns_to_keep=1)
    messages = [
        _msg("system", "sys"),
        _msg("user", "write file that is very long and takes up many tokens"),
        _msg("assistant", "", tool_calls=[
            ToolCall(id="1", name="filesystem", arguments={"path": "test.txt", "content": "x" * 100}),
        ]),
        _msg("tool", "success" + "x" * 100, name="filesystem"),
        _msg("user", "another old message that is very long"),
        _msg("assistant", "another old response that is very long"),
        _msg("user", "recent"),
    ]
    mgr.track_messages(messages)
    compressed = mgr.compress(messages)
    assert any("filesystem" in m.content for m in compressed if m.role == Role.system)
