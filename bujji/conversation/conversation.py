"""Stateful conversation session for BUJJI SDK.

Conversation is the Layer 2 session API wrapping a Connection with:
- Step history accumulation
- chat() convenience method (send + collect)
- State introspection (idle, turn count, usage)
"""

import contextlib
from collections.abc import AsyncIterator
from typing import Any

from bujji import types
from bujji.connections import connection

_DEFAULT_MAX_HISTORY_SIZE = 10_000


def _zero_usage() -> types.UsageMetadata:
    return types.UsageMetadata(
        prompt_token_count=0,
        cached_content_token_count=0,
        candidates_token_count=0,
        thoughts_token_count=0,
        total_token_count=0,
    )


def _add_usage(target: types.UsageMetadata, source: types.UsageMetadata) -> None:
    target.prompt_token_count += source.prompt_token_count or 0
    target.cached_content_token_count += source.cached_content_token_count or 0
    target.candidates_token_count += source.candidates_token_count or 0
    target.thoughts_token_count += source.thoughts_token_count or 0
    target.total_token_count += source.total_token_count or 0


class Conversation:
    """Stateful session wrapping a single conversation with the agent."""

    def __init__(
        self,
        conn: connection.Connection,
        *,
        max_history_size: int = _DEFAULT_MAX_HISTORY_SIZE,
    ):
        self._connection = conn
        self._steps: list[types.Step] = []
        self._turn_start_indices: list[int] = []
        self._compaction_indices: list[int] = []
        self._max_history_size = max_history_size
        self._cumulative_usage = _zero_usage()
        self._turn_usage: types.UsageMetadata | None = None

    @classmethod
    @contextlib.asynccontextmanager
    async def create(
        cls,
        strategy: connection.ConnectionStrategy,
    ) -> AsyncIterator["Conversation"]:
        async with strategy:
            yield cls(strategy.connect())

    async def send(self, prompt: types.Content | None, **kwargs: Any) -> None:
        if not self._connection.is_idle:
            try:
                async for _ in self.receive_steps():
                    pass
            except RuntimeError:
                await self._connection.wait_for_idle()
        self._turn_start_indices.append(len(self._steps))
        self._turn_usage = None
        await self._connection.send(prompt, **kwargs)

    async def receive_steps(self) -> AsyncIterator[types.Step]:
        async for step in self._connection.receive_steps():
            self._steps.append(step)
            if step.type == types.StepType.COMPACTION:
                self._compaction_indices.append(len(self._steps) - 1)
            if step.usage_metadata:
                self._accumulate_usage(step.usage_metadata)
            self._enforce_max_history()
            yield step

    async def receive_chunks(self) -> AsyncIterator[types.StreamChunk | types.ToolCall]:
        seen_tool_ids: set[str] = set()
        async for step in self.receive_steps():
            is_model = step.source == types.StepSource.MODEL
            is_target_user = step.target == types.StepTarget.USER
            if is_model and is_target_user:
                if step.thinking_delta:
                    yield types.Thought(step_index=step.step_index, text=step.thinking_delta)
                if step.content_delta:
                    yield types.Text(step_index=step.step_index, text=step.content_delta)
            if step.tool_calls:
                for call in step.tool_calls:
                    if call.id is None or call.id not in seen_tool_ids:
                        if call.id is not None:
                            seen_tool_ids.add(call.id)
                        yield call

    def get_last_structured_output(self) -> Any | None:
        for step in reversed(self._steps):
            if step.type == types.StepType.FINISH:
                return step.structured_output
        return None

    async def chat(self, prompt: types.Content | None = None, **kwargs: Any) -> types.ChatResponse:
        await self.send(prompt, **kwargs)
        return types.ChatResponse(self.receive_chunks(), conversation=self)

    @property
    def history(self) -> list[types.Step]:
        return list(self._steps)

    @property
    def last_response(self) -> str:
        for step in reversed(self._steps):
            if step.is_complete_response:
                return step.content
        return ""

    @property
    def turn_count(self) -> int:
        return len(self._turn_start_indices)

    @property
    def compaction_indices(self) -> list[int]:
        return list(self._compaction_indices)

    def clear_history(self) -> None:
        self._steps.clear()
        self._turn_start_indices.clear()
        self._compaction_indices.clear()
        self._cumulative_usage = _zero_usage()
        self._turn_usage = None

    def _enforce_max_history(self) -> None:
        if self._max_history_size and len(self._steps) > self._max_history_size:
            overflow = len(self._steps) - self._max_history_size
            self._steps = self._steps[overflow:]
            self._turn_start_indices = [i - overflow for i in self._turn_start_indices if i >= overflow]
            self._compaction_indices = [i - overflow for i in self._compaction_indices if i >= overflow]

    @property
    def connection(self) -> connection.Connection:
        return self._connection

    @property
    def is_idle(self) -> bool:
        return self._connection.is_idle

    @property
    def conversation_id(self) -> str:
        return self._connection.conversation_id

    @property
    def total_usage(self) -> types.UsageMetadata:
        return self._cumulative_usage.model_copy()

    @property
    def last_turn_usage(self) -> types.UsageMetadata | None:
        return self._turn_usage.model_copy() if self._turn_usage else None

    def _accumulate_usage(self, usage: types.UsageMetadata) -> None:
        _add_usage(self._cumulative_usage, usage)
        if self._turn_usage is None:
            self._turn_usage = _zero_usage()
        _add_usage(self._turn_usage, usage)

    async def cancel(self) -> None:
        await self._connection.cancel()

    async def delete(self) -> None:
        await self._connection.delete()

    async def signal_idle(self) -> None:
        await self._connection.signal_idle()

    async def wait_for_idle(self) -> None:
        await self._connection.wait_for_idle()

    async def wait_for_wakeup(self, timeout: float = 300.0) -> bool:
        return await self._connection.wait_for_wakeup(timeout)

    async def disconnect(self) -> None:
        await self._connection.disconnect()
