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
from bujji.memory.context_window import ContextWindowManager, create_context_manager
from bujji.providers.factory import get_provider
from bujji.providers.base import LLMProvider
from bujji.llm.service import LLMService

_MAX_TOOL_TURNS = 25
_PARALLEL_TOOL_LIMIT = 5

logger = logging.getLogger(__name__)


class LocalConnection(Connection):
    """A connection to a locally-running LLM via BUJJI providers.

    Features:
    - Tool execution loop with parallel tool calls
    - Automatic context window management
    - Per-tool error isolation
    - Streaming Step events
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
        model_name = strategy._config.model if strategy._config else "default"
        self._ctx_mgr = create_context_manager(
            model_name=model_name,
            max_tokens=strategy._config.max_tokens if strategy._config else None,
        )

    @property
    def is_idle(self) -> bool:
        return self._idle.is_set()

    @property
    def conversation_id(self) -> str:
        return self._conversation_id

    def _build_messages(self) -> list[Message]:
        system_instructions = self._strategy._config.system_instructions if self._strategy._config else None
        messages: list[Message] = []
        if system_instructions:
            messages.append(Message(
                role=Role.system,
                content=str(system_instructions),
            ))
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
        self._ctx_mgr.track_messages(messages)
        if self._ctx_mgr.needs_compression:
            logger.info("Context compression triggered (%d/%d tokens)", self._ctx_mgr.usage, self._ctx_mgr._model_limit)
            messages = self._ctx_mgr.compress(messages)
        return messages

    async def send(self, prompt: types.Content | None, **kwargs: Any) -> None:
        self._idle.clear()

        prompt_text = self._resolve_prompt(prompt)
        self._history.append({"role": "user", "content": prompt_text})

        max_tokens = self._strategy._config.max_tokens or 4096
        messages = self._build_messages()
        tool_schemas = self._tool_runner.get_schemas() if self._tool_runner else []
        has_tools = bool(tool_schemas)
        step_index = len(self._history)
        all_content_parts: list[str] = []
        usage = types.UsageMetadata()
        tool_turns = 0
        last_error: str | None = None

        try:
            while True:
                if has_tools:
                    try:
                        response = await self._llm.generate_with_tools(
                            messages=messages, tools=tool_schemas, max_tokens=max_tokens,
                        )
                    except Exception as e:
                        logger.warning("generate_with_tools failed, retrying without tools: %s", e)
                        response = await self._llm.generate(
                            messages=messages, max_tokens=max_tokens,
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
                    step_kw: dict[str, Any] = dict(
                        step_index=step_index,
                        type=types.StepType.TEXT_RESPONSE,
                        source=types.StepSource.MODEL,
                        target=types.StepTarget.USER,
                        status=types.StepStatus.DONE,
                        content=combined_text,
                        content_delta=combined_text,
                        is_complete_response=True,
                        usage_metadata=usage,
                    )
                    self._queue.put_nowait(types.Step(**step_kw))
                    break

                tool_turns += 1
                if tool_turns >= _MAX_TOOL_TURNS:
                    logger.warning("Tool execution loop reached max turns (%d)", _MAX_TOOL_TURNS)
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

                results = await self._execute_tool_calls(tool_calls)
                for tc, result in zip(tool_calls, results):
                    result_text = self._format_tool_result(result)
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
                    status = types.StepStatus.ERROR if isinstance(result, Exception) else types.StepStatus.DONE
                    self._queue.put_nowait(types.Step(
                        step_index=step_index,
                        type=types.StepType.TOOL_CALL,
                        source=types.StepSource.SYSTEM,
                        target=types.StepTarget.ENVIRONMENT,
                        status=status,
                        content=result_text,
                        tool_results=[types.ToolResult(
                            name=tc.name,
                            id=tc.id,
                            result=str(result) if not isinstance(result, Exception) else None,
                            error=str(result) if isinstance(result, Exception) else None,
                        )],
                    ))

        except Exception as e:
            logger.exception("LLM call or tool execution failed")
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

    async def _execute_tool_calls(self, tool_calls: list[CoreToolCall]) -> list[Any]:
        """Execute tool calls, potentially in parallel for independent calls."""
        if len(tool_calls) == 1:
            return [await self._execute_single(tool_calls[0])]

        tasks = []
        for tc in tool_calls:
            tasks.append(self._execute_single(tc))
            if len(tasks) >= _PARALLEL_TOOL_LIMIT:
                break
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_single(self, tc: CoreToolCall) -> Any:
        """Execute a single tool with isolated error handling."""
        try:
            result = await self._tool_runner.execute(tc.name, **tc.arguments)
            return result
        except Exception as e:
            logger.error("Tool %s failed: %s", tc.name, e)
            return Exception(f"Tool '{tc.name}' failed: {e}")

    def _format_tool_result(self, result: Any) -> str:
        if isinstance(result, Exception):
            return f"Error: {result}"
        if isinstance(result, dict):
            return result.get("output", result.get("error", str(result)))
        return str(result)

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
