from datetime import datetime

from bujji.core.models import (
    ChatRequest,
    ChatResponse,
    MemoryEntry,
    Message,
    Plan,
    ProviderResponse,
    Role,
    RouterDecision,
    Subtask,
    ToolCall,
    ToolResult,
)


class TestMessage:
    def test_message_creation(self):
        msg = Message(role=Role.user, content="Hello")
        assert msg.role == Role.user
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, datetime)

    def test_message_with_tool_calls(self):
        tc = ToolCall(id="call_1", name="filesystem", arguments={"path": "/tmp"})
        msg = Message(role=Role.assistant, content="", tool_calls=[tc])
        assert msg.tool_calls is not None
        assert len(msg.tool_calls) == 1


class TestToolResult:
    def test_successful_result(self):
        result = ToolResult(
            call_id="call_1",
            tool_name="filesystem",
            success=True,
            output="file content",
            execution_time=0.5,
        )
        assert result.success
        assert result.output == "file content"
        assert result.error is None

    def test_failed_result(self):
        result = ToolResult(
            call_id="call_1",
            tool_name="filesystem",
            success=False,
            output="",
            error="File not found",
        )
        assert not result.success
        assert result.error == "File not found"


class TestPlan:
    def test_plan_creation(self):
        subtask = Subtask(
            id="1",
            description="Install dependencies",
            estimated_complexity=0.3,
        )
        plan = Plan(
            task="Setup project",
            goal="Initialize the project with dependencies",
            subtasks=[subtask],
            estimated_complexity=0.3,
            confidence_score=0.9,
        )
        assert len(plan.subtasks) == 1
        assert plan.subtasks[0].description == "Install dependencies"

    def test_plan_confidence_range(self):
        plan = Plan(
            task="test",
            goal="test",
            subtasks=[],
            estimated_complexity=0.5,
            confidence_score=0.9,
        )
        assert 0.0 <= plan.confidence_score <= 1.0


class TestMemoryEntry:
    def test_entry_defaults(self):
        entry = MemoryEntry(content="test memory")
        assert entry.entry_type == "general"
        assert isinstance(entry.timestamp, datetime)
        assert entry.metadata == {}

    def test_entry_with_metadata(self):
        entry = MemoryEntry(
            content="project summary",
            entry_type="project",
            metadata={"project": "bujji", "version": "1.0.0"},
        )
        assert entry.metadata["project"] == "bujji"


class TestProviderResponse:
    def test_response_creation(self):
        resp = ProviderResponse(
            content="Hello!",
            model="llama3.2",
            provider="ollama",
            usage={"total_tokens": 42},
            finish_reason="stop",
            latency_ms=150.5,
        )
        assert resp.content == "Hello!"
        assert resp.latency_ms == 150.5
        assert resp.usage["total_tokens"] == 42


class TestRouterDecision:
    def test_local_decision(self):
        decision = RouterDecision(
            task="list files",
            confidence=0.9,
            can_handle_locally=True,
            reason="Simple file listing operation",
        )
        assert decision.can_handle_locally
        assert decision.escalation_request is None

    def test_escalation_decision(self):
        decision = RouterDecision(
            task="design architecture",
            confidence=0.3,
            can_handle_locally=False,
            reason="Complex architecture design",
            escalation_request="Requires senior architect review",
        )
        assert not decision.can_handle_locally
        assert decision.escalation_request is not None


class TestChatRequest:
    def test_request_creation(self):
        req = ChatRequest(message="Hello")
        assert req.message == "Hello"
        assert req.conversation_id is None
        assert not req.stream


class TestChatResponse:
    def test_response_creation(self):
        resp = ChatResponse(
            response="Hi there!",
            conversation_id="conv_1",
        )
        assert resp.response == "Hi there!"
        assert resp.conversation_id == "conv_1"
