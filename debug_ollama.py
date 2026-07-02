"""Debug what Ollama returns for tool calls."""
import asyncio
import json

import httpx


async def main():
    schema = {
        "type": "function",
        "function": {
            "name": "filesystem",
            "description": "Read/write files",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["read", "write", "list"]},
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["operation", "path"],
            },
        },
    }
    payload = {
        "model": "qwen3",
        "messages": [
            {"role": "system", "content": "You can use the filesystem tool."},
            {"role": "user", "content": "Write a file called test_bujji.txt with content Hello from BUJJI tools"},
        ],
        "tools": [schema],
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post("http://localhost:11434/api/chat", json=payload)
        raw = resp.text
        print("Status:", resp.status_code)
        print("Content-Type:", resp.headers.get("content-type"))
        print("Length:", len(raw))
        print("Lines:", raw.count("\n"))
        # Print raw repr to see hidden chars
        print("Raw repr[:600]:", repr(raw[:600]))
        # Try to parse
        try:
            d = json.loads(raw)
            msg = d.get("message", {})
            print("\nContent:", repr(msg.get("content", "")[:100]))
            print("Has tool_calls:", "tool_calls" in msg)
            if "tool_calls" in msg:
                print("Tool calls:", json.dumps(msg["tool_calls"], indent=2))
            print("Has thinking:", "thinking" in msg)
        except json.JSONDecodeError as e:
            print("\nJSON error:", e)
            # Print bytes around error position
            pos = e.pos
            print(f"Error at position {pos}: {repr(raw[max(0,pos-50):pos+50])}")

asyncio.run(main())
