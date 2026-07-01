"""Local connection backed by BUJJI providers.

Processes prompts by calling the LLM, executing tool calls via the
ToolRunner in a loop, and streaming results back as Step objects.
"""

import asyncio
import logging
import uuid
from typing import Any, AsyncIterator

from bujji import types
from bujji.connections.connection import Connection, ConnectionStrategy
from bujji.core.models import Message, Role, ToolCall as CoreToolCall
from bujji.providers.factory import get_provider
from bujji.providers.base import LLMProvider
from bujji.llm.service import LLMService

_MAX_TOOL_TURNS = 25


class LocalConnection(Connection):
    """A connection to a locally-running LLM via BUJJI providers.

    Runs a tool execution loop: LLM -> tool calls -> execute -> results -> LLM.
    """

    def __init__(
        self,
        strategy: "LocalConnectionStrategy",
        llm_service: LLMService,
    ) -> None:
        self._strategy = strategy
        self._llm = llm_service
        self._conversation_id = str(uuid.uuid4())
        self._history: list[dict[str, Any]] = []
        self._idle = asyncio.Event()
        self._idle.set()
        self._tool_runner = strategy._tool_runner
        self._hook_runner = strategy._hook_runner
        self._queue: asyncio.Queue[types.Step] = asyncio.Queue()
        self._trigger_messages: asyncio.Queue[str] = asyncio.Queue()

    @property
    def is_idle(self) -> bool:
        return self._idle.is_set()

    @property
    def conversation_id(self) -> str:
        return self._conversation_id

    async def send(self, prompt: types.Content | None, **kwargs: Any) -> None:
        self._idle.clear()

        prompt_text = self._resolve_prompt(prompt)
        self._history.append({"role": "user", "content": prompt_text})

        system_instructions = self._strategy._config.system_instructions
        messages: list[Message] = []
        if system_instructions:
            messages.append(Message(
                role=Role.system,
                content=str(system_instructions),
            ))

        max_tokens = self._strategy._config.max_tokens or 4096

        for h in self._history:
            role = h.get("role", "user")
            content = h.get("content", "")
            msg = Message(role=Role(role), content=content)
            if "tool_calls" in h:
                msg.tool_calls = [
                    CoreToolCall(id=tc.get("id", ""), name=tc.get("name", ""), arguments=tc.get("arguments", {}))
                    for tc in h["tool_calls"]
                ]
            if "name" in h:
                msg.name = h["name"]
            messages.append(msg)

        tool_schemas = self._tool_runner.get_schemas() if self._tool_runner else []
        has_tools = bool(tool_schemas)
        step_index = len(self._history)
        all_content_parts: list[str] = []
        usage = types.UsageMetadata()
        tool_turns = 0

        try:
            while True:
                if has_tools:
                    response = await self._llm.generate_with_tools(
                        messages=messages, tools=tool_schemas, max_tokens=max_tokens,
                    )
                else:
                    response = await self._llm.generate(
                        messages=messages, max_tokens=max_tokens,
                    )

                text = response.content or ""
                all_content_parts.append(text)

                if response.usage:
                    usage.total_token_count += response.usage.get("total_tokens", 0)
                    usage.prompt_token_count += response.usage.get("prompt_tokens", 0)
                    usage.candidates_token_count += response.usage.get("completion_tokens", 0)

                tool_calls = (response.tool_calls or []) if has_tools else []

                if not tool_calls:
                    self._history.append({"role": "assistant", "content": text})
                    messages.append(Message(role=Role.assistant, content=text))
                    combined_text = "".join(all_content_parts)
                    self._queue.put_nowait(types.Step(
                        step_index=step_index,
                        type=types.StepType.TEXT_RESPONSE,
                        source=types.StepSource.MODEL,
                        target=types.StepTarget.USER,
                        status=types.StepStatus.DONE,
                        content=combined_text,
                        content_delta=combined_text,
                        is_complete_response=True,
                        usage_metadata=usage,
                    ))
                    break

                # Tool call turn
                tool_turns += 1
                if tool_turns >= _MAX_TOOL_TURNS:
                    logging.warning("Tool execution loop reached max turns (%d)", _MAX_TOOL_TURNS)
                    self._queue.put_nowait(types.Step(
                        step_index=step_index,
                        type=types.StepType.SYSTEM_MESSAGE,
                        source=types.StepSource.SYSTEM,
                        target=types.StepTarget.USER,
                        status=types.StepStatus.DONE,
                        content="Max tool execution turns reached. Task may be incomplete.",
                        is_complete_response=True,
                    ))
                    break

                tc_list = [{"id": tc.id, "name": tc.name, "arguments": tc.arguments} for tc in tool_calls]
                self._history.append({"role": "assistant", "content": text, "tool_calls": tc_list})
                assistant_msg = Message(role=Role.assistant, content=text, tool_calls=tool_calls)
                messages.append(assistant_msg)

                types_tool_calls = [
                    types.ToolCall(name=tc.name, args=tc.arguments, id=tc.id)
                    for tc in tool_calls
                ]
                self._queue.put_nowait(types.Step(
                    step_index=step_index,
                    type=types.StepType.TOOL_CALL,
                    source=types.StepSource.MODEL,
                    target=types.StepTarget.ENVIRONMENT,
                    status=types.StepStatus.ACTIVE,
                    content=text,
                    tool_calls=types_tool_calls,
                ))

                for tc in tool_calls:
                    result = await self._tool_runner.execute(tc.name, **tc.arguments)
                    result_text = ""
                    if isinstance(result, dict):
                        result_text = result.get("output", result.get("error", str(result)))
                        if isinstance(result_text, dict):
                            result_text = str(result_text)
                    else:
                        result_text = str(result)
                    self._history.append({
                        "role": "tool",
                        "content": result_text,
                        "name": tc.name,
                    })
                    messages.append(Message(
                        role=Role.tool,
                        content=result_text,
                        name=tc.name,
                    ))

                    self._queue.put_nowait(types.Step(
                        step_index=step_index,
                        type=types.StepType.TOOL_CALL,
                        source=types.StepSource.SYSTEM,
                        target=types.StepTarget.ENVIRONMENT,
                        status=types.StepStatus.DONE,
                        content=result_text,
                        tool_results=[types.ToolResult(
                            name=tc.name,
                            id=tc.id,
                            result=result_text,
                        )],
                    ))

        except Exception as e:
            logging.exception("LLM call or tool execution failed")
            self._queue.put_nowait(types.Step(
                step_index=step_index,
                type=types.StepType.SYSTEM_MESSAGE,
                source=types.StepSource.SYSTEM,
                target=types.StepTarget.USER,
                status=types.StepStatus.ERROR,
                content=f"Error: {e}",
                is_complete_response=True,
            ))

        self._idle.set()

    def receive_steps(self) -> AsyncIterator[types.Step]:
        return self._step_iterator()

    async def _step_iterator(self) -> AsyncIterator[types.Step]:
        while True:
            try:
                step = await asyncio.wait_for(self._queue.get(), timeout=0.5)
                yield step
                if step.is_complete_response:
                    break
            except asyncio.TimeoutError:
                if self._idle.is_set() and self._queue.empty():
                    break

    async def send_trigger_notification(self, content: str) -> None:
        self._queue.put_nowait(types.Step(
            step_index=0,
            type=types.StepType.SYSTEM_MESSAGE,
            source=types.StepSource.SYSTEM,
            target=types.StepTarget.USER,
            content=f"[Trigger] {content}",
        ))

    async def disconnect(self) -> None:
        self._idle.set()

    async def cancel(self) -> None:
        self._idle.set()

    def _resolve_prompt(self, prompt: types.Content | None) -> str:
        if prompt is None:
            return ""
        if isinstance(prompt, str):
            return prompt
        if isinstance(prompt, list):
            parts = []
            for item in prompt:
                if isinstance(item, str):
                    parts.append(item)
                elif hasattr(item, "description") and item.description:
                    parts.append(f"[{item.__class__.__name__}: {item.description}]")
                else:
                    parts.append(f"[{item.__class__.__name__}]")
            return "\n".join(parts)
        return str(prompt)


class LocalConnectionStrategy(ConnectionStrategy):
    """Strategy for establishing a local connection via BUJJI providers."""

    def __init__(
        self,
        config: Any,
        tool_runner: Any,
        hook_runner: Any,
    ) -> None:
        self._config = config
        self._tool_runner = tool_runner
        self._hook_runner = hook_runner
        self._connection: LocalConnection | None = None
        self._provider: LLMProvider | None = None

    async def __aenter__(self) -> None:
        settings = self._build_settings()
        self._provider = get_provider(settings)
        llm_service = LLMService(self._provider)
        self._connection = LocalConnection(self, llm_service)

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._connection:
            await self._connection.disconnect()
            self._connection = None

    def connect(self) -> LocalConnection:
        if not self._connection:
            raise RuntimeError("Connection not established. Use 'async with' block.")
        return self._connection

    def _build_settings(self) -> Any:
        from bujji.core.config import Settings
        settings = Settings()
        settings.llm.provider = self._config.provider or "ollama"
        settings.llm.model = self._config.model or "llama3.2"
        settings.llm.base_url = self._config.base_url
        settings.llm.api_key = self._config.api_key
        settings.llm.temperature = self._config.temperature
        settings.llm.max_tokens = self._config.max_tokens
        settings.llm.timeout = self._config.timeout
        return settings
