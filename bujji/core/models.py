from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Role(StrEnum):
    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"


class Message(BaseModel):
    role: Role
    content: str
    name: str | None = None
    tool_calls: list["ToolCall"] | None = None
    timestamp: datetime = Field(default_factory=_utcnow)


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class ToolResult(BaseModel):
    call_id: str
    tool_name: str
    success: bool
    output: str
    error: str | None = None
    execution_time: float = 0.0
    timestamp: datetime = Field(default_factory=_utcnow)


class Subtask(BaseModel):
    id: str
    description: str
    dependencies: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    estimated_complexity: float = Field(ge=0.0, le=1.0)
    status: str = "pending"


class Plan(BaseModel):
    task: str
    goal: str
    subtasks: list[Subtask]
    dependencies: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    estimated_complexity: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""


class MemoryEntry(BaseModel):
    id: str = ""
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None
    timestamp: datetime = Field(default_factory=_utcnow)
    entry_type: str = "general"


class ProviderResponse(BaseModel):
    content: str
    model: str
    provider: str
    usage: dict[str, int] | None = None
    finish_reason: str | None = None
    latency_ms: float = 0.0
    tool_calls: list["ToolCall"] | None = None


class RouterDecision(BaseModel):
    task: str
    confidence: float
    can_handle_locally: bool
    reason: str
    escalation_request: str | None = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    plan: Plan | None = None
    tool_results: list[ToolResult] = Field(default_factory=list)
    router_decision: RouterDecision | None = None
