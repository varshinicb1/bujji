"""Debug the second LLM call after tool execution."""
import asyncio
import httpx
import json
from bujji.providers.ollama import _serialize_messages
from bujji.core.models import Message, Role, ToolCall

async def main():
    schema = {
        "type": "function",
        "function": {
            "name": "filesystem",
            "description": "Read/write files",
            "parameters": {"type": "object", "properties": {"operation": {"type": "string"}, "path": {"type": "string"}, "content": {"type": "string"}}, "required": ["operation", "path"]},
        },
    }

    messages = [
        Message(role=Role.system, content="You can use the filesystem tool."),
        Message(role=Role.user, content="Write a file called test.txt with content Hello"),
        Message(role=Role.assistant, content="", tool_calls=[
            ToolCall(id="call_xxx", name="filesystem", arguments={"operation": "write", "path": "test.txt", "content": "Hello"})
        ]),
        Message(role=Role.tool, content="File written successfully", name="filesystem"),
    ]

    serialized = _serialize_messages(messages)
    print("Serialized messages:")
    print(json.dumps(serialized, indent=2))

    payload = {
        "model": "qwen3",
        "messages": serialized,
        "tools": [schema],
        "temperature": 0.1,
    }
    print("\nSending to Ollama...")
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post("http://localhost:11434/api/chat", json=payload)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            # Parse NDJSON
            raw = resp.text
            lines = [l.strip() for l in raw.split("\n") if l.strip()]
            for ln in lines:
                try:
                    obj = json.loads(ln)
                    msg = obj.get("message", {})
                    if msg.get("content") or "tool_calls" in msg:
                        print(f"  content: {repr(msg.get('content','')[:80])}")
                        if "tool_calls" in msg:
                            print(f"  tool_calls: {json.dumps(msg['tool_calls'], indent=2)}")
                except:
                    pass
        else:
            print(f"Error: {resp.text[:500]}")

asyncio.run(main())
