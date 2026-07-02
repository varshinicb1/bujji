"""Canonical type definitions for BUJJI SDK.

All public SDK interfaces use these types. Pure Python Pydantic V2 models.
Combines Antigravity SDK patterns with BUJJI's core models.
"""

from __future__ import annotations

import enum
import mimetypes
import pathlib
from collections.abc import AsyncIterator, Callable
from typing import Any, Literal

import pydantic

from bujji.core.models import Message as Message

__all__ = [
    # Config
    "CapabilitiesConfig",
    "BuiltinTools",
    "McpStdioServer",
    "McpSseServer",
    "McpStreamableHttpServer",
    "McpServerConfig",
    # Core types
    "Message",
    # Tool types
    "ToolCall",
    "ToolResult",
    "SystemInstructions",
    "PythonTool",
    # Step types
    "StepType",
    "StepSource",
    "StepTarget",
    "StepStatus",
    "UsageMetadata",
    "Step",
    # Hook types
    "HookResult",
    # Streaming
    "StreamChunk",
    "Thought",
    "Text",
    "ChatResponse",
    # Content primitives
    "Image",
    "Document",
    "Audio",
    "Video",
    "ContentPrimitive",
    "Content",
    "from_file",
    # Trigger types
    "TriggerDelivery",
    "FileChangeKind",
    "FileChange",
    # Errors
    "BujjiConnectionError",
    "BujjiValidationError",
]

# =============================================================================
# Built-in Tools Enum
# =============================================================================


class BuiltinTools(enum.StrEnum):
    """Built-in tools available to the agent."""

    VIEW_FILE = "View"
    VIEW_CODE = "ViewCode"
    SEARCH = "Grep"
    RUN_COMMAND = "RunCommand"
    EDIT = "Edit"
    WRITE = "Write"
    LIST_DIR = "ListDir"
    SEARCH_DIR = "SearchDir"
    SUB_AGENT = "SubAgent"
    IMAGE_GENERATION = "ImageGeneration"
    FILE_SYSTEM = "BujjiFileSystem"

    @classmethod
    def read_only(cls) -> list[str]:
        return [cls.VIEW_FILE, cls.VIEW_CODE, cls.SEARCH, cls.LIST_DIR, cls.SEARCH_DIR, cls.FILE_SYSTEM]

    @classmethod
    def nondestructive(cls) -> list[str]:
        return [cls.VIEW_FILE, cls.VIEW_CODE, cls.SEARCH, cls.LIST_DIR, cls.SEARCH_DIR, cls.FILE_SYSTEM]

    @classmethod
    def file_tools(cls) -> list[str]:
        return [cls.VIEW_FILE, cls.VIEW_CODE, cls.EDIT, cls.WRITE, cls.LIST_DIR, cls.SEARCH_DIR]

    @classmethod
    def none(cls) -> list[str]:
        return []

    @classmethod
    def all_tools(cls) -> list[str]:
        return [e.value for e in cls]


# =============================================================================
# Capabilities
# =============================================================================


class CapabilitiesConfig(pydantic.BaseModel):
    """Controls which features are available to the agent."""

    enable_subagents: bool = False
    enabled_tools: list[str] | None = None
    disabled_tools: list[str] | None = None
    finish_tool_schema_json: dict | None = None

    @pydantic.model_validator(mode="after")
    def _check_exclusive(self):
        if self.enabled_tools is not None and self.disabled_tools is not None:
            raise ValueError(
                "enabled_tools and disabled_tools are mutually exclusive"
            )
        return self


# =============================================================================
# MCP Server Config
# =============================================================================


class McpStdioServer(pydantic.BaseModel):
    """MCP server launched as a subprocess over stdio."""

    type: Literal["stdio"] = "stdio"
    command: str
    args: list[str] = pydantic.Field(default_factory=list)


class McpSseServer(pydantic.BaseModel):
    """MCP server connected via Server-Sent Events."""

    type: Literal["sse"] = "sse"
    url: str
    headers: dict[str, str] = pydantic.Field(default_factory=dict)


class McpStreamableHttpServer(pydantic.BaseModel):
    """MCP server connected via Streamable HTTP."""

    type: Literal["streamable-http"] = "streamable-http"
    url: str
    headers: dict[str, str] = pydantic.Field(default_factory=dict)
    timeout: float = 30.0
    sse_read_timeout: float = 300.0
    terminate_on_close: bool = False


McpServerConfig = McpStdioServer | McpSseServer | McpStreamableHttpServer


# =============================================================================
# Tool Types
# =============================================================================


class ToolCall(pydantic.BaseModel):
    """A request from the model to execute a tool."""

    name: str
    args: dict[str, Any] = pydantic.Field(default_factory=dict)
    id: str | None = None
    canonical_path: str | None = None


class ToolResult(pydantic.BaseModel):
    """The result of executing a tool call."""

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    name: str
    id: str | None = None
    result: Any = None
    error: str | None = None
    exception: BaseException | None = None


class SystemInstructions(pydantic.BaseModel):
    """System instructions for the agent."""

    text: str = ""


PythonTool = Callable[..., Any]


# =============================================================================
# Step Types
# =============================================================================


class StepType(enum.StrEnum):
    TEXT_RESPONSE = "text_response"
    TOOL_CALL = "tool_call"
    SYSTEM_MESSAGE = "system_message"
    COMPACTION = "compaction"
    FINISH = "finish"
    UNKNOWN = "unknown"


class StepSource(enum.StrEnum):
    SYSTEM = "system"
    USER = "user"
    MODEL = "model"
    UNKNOWN = "unknown"


class StepTarget(enum.StrEnum):
    USER = "user"
    ENVIRONMENT = "environment"
    UNSPECIFIED = "unspecified"
    UNKNOWN = "unknown"


class StepStatus(enum.StrEnum):
    ACTIVE = "active"
    DONE = "done"
    WAITING_FOR_USER = "waiting_for_user"
    ERROR = "error"
    CANCELED = "canceled"
    UNKNOWN = "unknown"


class UsageMetadata(pydantic.BaseModel):
    """Token usage counters."""

    prompt_token_count: int = 0
    cached_content_token_count: int = 0
    candidates_token_count: int = 0
    thoughts_token_count: int = 0
    total_token_count: int = 0


class Step(pydantic.BaseModel):
    """A single step in the agent conversation."""

    step_index: int = 0
    type: StepType = StepType.UNKNOWN
    source: StepSource = StepSource.UNKNOWN
    target: StepTarget = StepTarget.UNKNOWN
    status: StepStatus = StepStatus.DONE
    content: str = ""
    content_delta: str | None = None
    thinking: str | None = None
    thinking_delta: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_results: list[ToolResult] | None = None
    is_complete_response: bool = False
    structured_output: dict[str, Any] | None = None
    usage_metadata: UsageMetadata | None = None

    model_config = pydantic.ConfigDict(extra="ignore")


# =============================================================================
# Hook Types
# =============================================================================


class HookResult(pydantic.BaseModel):
    """Result from a DecideHook."""

    allow: bool = True
    message: str | None = None


# =============================================================================
# Trigger Types
# =============================================================================


class TriggerDelivery(enum.StrEnum):
    SEND_IMMEDIATELY = "send_immediately"
    WAIT_IDLE = "wait_idle"


class FileChangeKind(enum.StrEnum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


class FileChange(pydantic.BaseModel):
    kind: FileChangeKind
    path: str


# =============================================================================
# Streaming Types
# =============================================================================


class StreamChunk(pydantic.BaseModel):
    """Base class for streaming chunks."""

    step_index: int = 0


class Thought(StreamChunk):
    """A reasoning/thinking delta from the model."""

    text: str = ""
    signature: str | None = None


class Text(StreamChunk):
    """A text content delta from the model."""

    text: str = ""


class ChatResponse:
    """Streaming response from the agent.

    Supports multiple async iterators for consuming different aspects
    of the response: text tokens, thoughts, and tool calls.
    """

    def __init__(
        self,
        chunk_iter: AsyncIterator[StreamChunk | ToolCall],
        *,
        conversation: Any = None,
    ) -> None:
        self._chunk_iter = chunk_iter
        self._conversation = conversation
        self._consumed = False

    async def text(self) -> str:
        """Collects all text chunks and returns the full response."""
        parts: list[str] = []
        async for chunk in self:
            parts.append(chunk)
        return "".join(parts)

    def __aiter__(self) -> AsyncIterator[str]:
        """Iterates over text tokens as they arrive."""
        return self._text_iterator()

    async def _text_iterator(self) -> AsyncIterator[str]:
        parts: list[str] = []
        async for chunk in self._chunk_iter:
            if isinstance(chunk, Text):
                parts.append(chunk.text)
                yield chunk.text
            elif isinstance(chunk, ToolCall):
                pass
        self._consumed = True

    @property
    def chunks(self) -> AsyncIterator[StreamChunk | ToolCall]:
        """Raw chunk stream."""
        return self._chunk_iter

    @property
    def thoughts(self) -> AsyncIterator[Thought]:
        """Stream reasoning/thinking deltas."""
        return self._filter_chunks(Thought)

    @property
    def tool_calls(self) -> AsyncIterator[ToolCall]:
        """Stream tool call events."""
        return self._filter_chunks(ToolCall)

    async def _filter_chunks(self, cls: type) -> AsyncIterator[Any]:
        async for chunk in self._chunk_iter:
            if isinstance(chunk, cls):
                yield chunk

    @property
    def conversation(self) -> Any:
        return self._conversation

    async def resolve(self) -> str:
        return await self.text()

    def structured_output(self) -> Any | None:
        if self._conversation:
            return self._conversation.get_last_structured_output()
        return None

    @property
    def usage_metadata(self) -> UsageMetadata | None:
        if self._conversation:
            return self._conversation.last_turn_usage
        return None


# =============================================================================
# Content Primitives (Multimodal)
# =============================================================================


class _BaseMedia(pydantic.BaseModel):
    data: bytes
    mime_type: str = "application/octet-stream"
    description: str | None = None

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)


class Image(_BaseMedia):
    mime_type: str = "image/png"


class Document(_BaseMedia):
    mime_type: str = "application/pdf"


class Audio(_BaseMedia):
    mime_type: str = "audio/mpeg"


class Video(_BaseMedia):
    mime_type: str = "video/mp4"


ContentPrimitive = str | Image | Document | Audio | Video

Content = ContentPrimitive | list[ContentPrimitive]


def from_file(path: str | pathlib.Path, description: str | None = None) -> _BaseMedia:
    """Resolves a file path to the correct media type."""
    path = pathlib.Path(path)
    mime_type, _ = mimetypes.guess_type(str(path))
    mime_type = mime_type or "application/octet-stream"
    data = path.read_bytes()

    if mime_type.startswith("image/"):
        return Image(data=data, mime_type=mime_type, description=description)
    elif mime_type.startswith("audio/"):
        return Audio(data=data, mime_type=mime_type, description=description)
    elif mime_type.startswith("video/"):
        return Video(data=data, mime_type=mime_type, description=description)
    else:
        return Document(data=data, mime_type=mime_type, description=description)


# =============================================================================
# Errors
# =============================================================================


class BujjiConnectionError(Exception):
    """Raised when a connection to an agent backend fails."""


class BujjiValidationError(Exception):
    """Raised when input validation fails."""
