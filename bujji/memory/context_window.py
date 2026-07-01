"""Automatic context window management with sliding window + summarization.

When total messages approach the model's context limit, older turns are
summarized into compact representations to preserve information without
overflowing the window.
"""

import logging
from typing import Any, Optional

from bujji.core.models import Message, Role
from bujji.core.exceptions import ProviderError

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_LIMITS: dict[str, int] = {
    "qwen3": 131072,
    "qwen2.5": 131072,
    "llama3.2": 131072,
    "llama3.1": 131072,
    "mistral": 32768,
    "deepseek": 65536,
    "default": 32768,
}

_TOKEN_ESTIMATE_RATIO = 4.0  # chars per token (conservative for code/JSON)
_SUMMARY_RESERVE = 8192  # tokens reserved for response generation
_TRIGGER_RATIO = 0.70  # compress when usage exceeds 70% of limit


def estimate_tokens(text: str) -> int:
    return int(len(text) / _TOKEN_ESTIMATE_RATIO) or 1


def estimate_message_tokens(msg: Message) -> int:
    count = estimate_tokens(msg.content)
    if msg.tool_calls:
        for tc in msg.tool_calls:
            count += estimate_tokens(tc.name)
            count += estimate_tokens(str(tc.arguments))
    if msg.name:
        count += estimate_tokens(msg.name)
    count += 4  # overhead per message
    return count


class ContextWindowManager:
    """Manages conversation context within model token limits.

    Strategy:
    1. Track cumulative token usage
    2. When usage > trigger_ratio of model limit, compress older history
    3. Compression: summarize old turns, discard oldest, keep recent turns intact
    """

    def __init__(
        self,
        model_name: str = "default",
        max_tokens: Optional[int] = None,
        trigger_ratio: float = _TRIGGER_RATIO,
        reserve_tokens: int = _SUMMARY_RESERVE,
        min_turns_to_keep: int = 5,
        summarize_llm: Optional[Any] = None,
    ) -> None:
        model_limit = _DEFAULT_MODEL_LIMITS.get(model_name, _DEFAULT_MODEL_LIMITS["default"])
        self._model_limit = max_tokens or model_limit
        self._trigger_threshold = int(self._model_limit * trigger_ratio)
        self._reserve = reserve_tokens
        self._min_turns_to_keep = min_turns_to_keep
        self._summarize_llm = summarize_llm
        self._current_usage = 0
        self._system_content: Optional[str] = None
        logger.info(
            "ContextWindowManager initialized: limit=%d, trigger=%d, reserve=%d",
            self._model_limit, self._trigger_threshold, self._reserve,
        )

    @property
    def usage(self) -> int:
        return self._current_usage

    @property
    def available(self) -> int:
        return self._model_limit - self._current_usage - self._reserve

    @property
    def needs_compression(self) -> bool:
        return self._current_usage >= self._trigger_threshold

    def track_messages(self, messages: list[Message]) -> None:
        self._current_usage = sum(estimate_message_tokens(m) for m in messages)
        for m in messages:
            if m.role == Role.system:
                self._system_content = m.content

    def compress(self, messages: list[Message]) -> list[Message]:
        """Compress history when approaching context limit.

        Strategy:
        - Always keep system prompt
        - Keep the last N recent turns intact
        - Summarize older user+assistant+tool exchanges into compact messages
        - Discard redundant tool results
        """
        if not self.needs_compression:
            return messages

        system_msgs = [m for m in messages if m.role == Role.system]
        non_system = [m for m in messages if m.role != Role.system]

        n_turns = self._min_turns_to_keep * 3
        recent = non_system[-n_turns:] if len(non_system) > n_turns else non_system
        to_compress = non_system[:-len(recent)] if len(non_system) > n_turns else []

        if not to_compress:
            return messages

        compressed = self._build_summary_messages(to_compress)
        result = system_msgs + compressed + recent
        self._current_usage = sum(estimate_message_tokens(m) for m in result)

        kept = len(system_msgs) + len(compressed) + len(recent)
        removed = len(messages) - kept
        logger.info(
            "Context compression: %d messages -> %d messages (removed %d, usage %d/%d)",
            len(messages), kept, removed, self._current_usage, self._model_limit,
        )
        return result

    def _build_summary_messages(self, messages: list[Message]) -> list[Message]:
        """Build compact summary of old messages."""
        summary_parts: list[str] = []
        tool_results: list[str] = []
        turn_count = 0

        for m in messages:
            if m.role == Role.user:
                turn_count += 1
                summary_parts.append(f"User: {m.content[:200]}")
            elif m.role == Role.assistant:
                if m.content:
                    summary_parts.append(f"Assistant: {m.content[:200]}")
                if m.tool_calls:
                    for tc in m.tool_calls:
                        summary_parts.append(f"Tool [{tc.name}]: {str(tc.arguments)[:100]}")
                        tool_results.append(tc.name)
            elif m.role == Role.tool:
                tool_results.append(f"Result: {m.content[:100]}")

        summary_text = "\n".join(summary_parts)
        if not summary_text:
            return []

        return [
            Message(
                role=Role.system,
                content=(
                    f"[Compressed History: {turn_count} previous turns]\n"
                    f"{summary_text}"
                ),
                name="compressed_history",
            ),
        ]

    async def summarize_with_llm(
        self,
        messages: list[Message],
    ) -> list[Message]:
        """Use LLM to generate a smart summary of old messages.

        Falls back to basic compression if LLM is unavailable.
        """
        if not self._summarize_llm:
            return self.compress(messages)
        return await self._llm_summarize(messages)

    async def _llm_summarize(self, messages: list[Message]) -> list[Message]:
        """Use configured LLM to generate a semantic summary."""
        system_msgs = [m for m in messages if m.role == Role.system]
        non_system = [m for m in messages if m.role != Role.system]
        recent = non_system[-(self._min_turns_to_keep * 3):]
        to_compress = non_system[:-(self._min_turns_to_keep * 3)] if len(non_system) > (self._min_turns_to_keep * 3) else []

        if not to_compress:
            return messages

        try:
            raw = "\n".join(
                f"[{m.role.value}] {m.content[:300]}"
                + (f" -> tool: {m.tool_calls[0].name}" if m.tool_calls else "")
                for m in to_compress if m.content or m.tool_calls
            )

            summary_msg = [
                Message(role=Role.system, content="Summarize the key information from this conversation history concisely for an AI assistant. Preserve user goals, decisions, errors, and data."),
                Message(role=Role.user, content=raw[:4000]),
            ]
            summary_resp = await self._summarize_llm.generate(summary_msg, max_tokens=512)
            summary = summary_resp.content.strip()
        except Exception as e:
            logger.warning("LLM summarization failed, using basic: %s", e)
            return self.compress(messages)

        return system_msgs + [
            Message(role=Role.system, content=f"[Compressed History Summary]\n{summary}"),
        ] + recent


def create_context_manager(
    model_name: str = "default",
    max_tokens: Optional[int] = None,
    trigger_ratio: float = _TRIGGER_RATIO,
    summarize_llm: Optional[Any] = None,
) -> ContextWindowManager:
    return ContextWindowManager(
        model_name=model_name,
        max_tokens=max_tokens,
        trigger_ratio=trigger_ratio,
        summarize_llm=summarize_llm,
    )
