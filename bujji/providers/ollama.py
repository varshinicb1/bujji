import json as json_mod
from typing import Any, Optional

import httpx

from bujji.core.exceptions import ProviderError
from bujji.core.models import Message, ProviderResponse, ToolCall
from bujji.providers.base import LLMProvider


def _serialize_messages(messages: list[Message]) -> list[dict[str, Any]]:
    """Serialize Message objects to Ollama API format, including tool calls/results."""
    result = []
    for m in messages:
        entry: dict[str, Any] = {"role": m.role.value, "content": m.content}
        if m.role.value == "assistant" and m.tool_calls:
            entry["tool_calls"] = [
                {
                    "function": {
                        "name": tc.name,
                        "arguments": json_mod.dumps(tc.arguments) if isinstance(tc.arguments, str) else tc.arguments,
                    }
                }
                for tc in m.tool_calls
            ]
        if m.role.value == "tool" and m.name:
            entry["name"] = m.name
        result.append(entry)
    return result


def _parse_tool_calls(raw_tool_calls: list[dict[str, Any]]) -> list[ToolCall]:
    """Parse Ollama tool_calls response into ToolCall objects."""
    calls: list[ToolCall] = []
    for tc in raw_tool_calls:
        fn = tc.get("function", {})
        args_raw = fn.get("arguments", "{}")
        if isinstance(args_raw, str):
            try:
                args = json_mod.loads(args_raw)
            except json_mod.JSONDecodeError:
                args = {}
        else:
            args = args_raw
        calls.append(ToolCall(
            id=tc.get("id", fn.get("name", "unknown")),
            name=fn.get("name", "unknown"),
            arguments=args if isinstance(args, dict) else {},
        ))
    return calls


class OllamaProvider(LLMProvider):
    """LLM provider for Ollama local models."""

    def _validate_config(self) -> None:
        self.base_url = self.config.get("base_url", "http://localhost:11434")
        self.model = self.config.get("model", "llama3.2")

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self.model

    async def generate(
        self,
        messages: list[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> ProviderResponse:
        payload = {
            "model": self.model,
            "messages": _serialize_messages(messages),
            "temperature": temperature or self.config.get("temperature", 0.1),
            "stream": stream,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.config.get("timeout", 300)) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = self._parse_ollama_response(resp.text)
        except httpx.HTTPError as e:
            raise ProviderError(f"Ollama request failed: {e}") from e
        except json_mod.JSONDecodeError as e:
            raise ProviderError(f"Ollama JSON parse failed: {e}") from e

        msg = data.get("message", {})
        tc_raw = msg.get("tool_calls")
        return ProviderResponse(
            content=msg.get("content", ""),
            model=self.model,
            provider=self.provider_name,
            usage={"total_tokens": data.get("eval_count", 0)},
            tool_calls=_parse_tool_calls(tc_raw) if tc_raw else None,
        )

    async def generate_with_tools(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ProviderResponse:
        payload = {
            "model": self.model,
            "messages": _serialize_messages(messages),
            "tools": tools,
            "temperature": temperature or self.config.get("temperature", 0.1),
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.config.get("timeout", 300)) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = self._parse_ollama_response(resp.text)
        except httpx.HTTPError as e:
            raise ProviderError(f"Ollama tool call failed: {e}") from e
        except json_mod.JSONDecodeError as e:
            raise ProviderError(f"Ollama tool call JSON parse failed: {e}") from e

        msg = data.get("message", {})
        tc_raw = msg.get("tool_calls")
        return ProviderResponse(
            content=msg.get("content", ""),
            model=self.model,
            provider=self.provider_name,
            usage={"total_tokens": data.get("eval_count", 0)},
            tool_calls=_parse_tool_calls(tc_raw) if tc_raw else None,
        )

    def _parse_ollama_response(self, text: str) -> dict[str, Any]:
        """Parse Ollama response, handling both single JSON and NDJSON."""
        text = text.strip()
        if not text:
            return {"message": {"content": ""}}
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        # Single JSON — fast path
        if len(lines) == 1:
            try:
                return json_mod.loads(lines[0])
            except json_mod.JSONDecodeError:
                pass
        # NDJSON: prefer last line with tool_calls, else last done=true
        tool_call_obj = None
        last_done = None
        for line in lines:
            try:
                obj = json_mod.loads(line)
                msg = obj.get("message", {})
                if "tool_calls" in msg:
                    tool_call_obj = obj
                if obj.get("done"):
                    last_done = obj
            except json_mod.JSONDecodeError:
                continue
        if tool_call_obj:
            return tool_call_obj
        if last_done:
            return last_done
        return {"message": {"content": ""}}
