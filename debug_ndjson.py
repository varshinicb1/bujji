"""Debug NDJSON parsing."""
import asyncio
import json

import httpx


async def main():
    schema = {
        "type": "function",
        "function": {
            "name": "filesystem",
            "description": "Read/write files",
            "parameters": {"type": "object", "properties": {"operation": {"type": "string"}, "path": {"type": "string"}, "content": {"type": "string"}}, "required": ["operation", "path"]},
        },
    }
    payload = {
        "model": "qwen3",
        "messages": [
            {"role": "system", "content": "You can use the filesystem tool."},
            {"role": "user", "content": "Write a file called test_bujji.txt with content Hello"},
        ],
        "tools": [schema],
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post("http://localhost:11434/api/chat", json=payload)
        raw = resp.text
        print("Content-Type:", resp.headers.get("content-type"))
        print("Length:", len(raw))
        print("Lines:", raw.count("\n"))

        lines = [l.strip() for l in raw.split("\n") if l.strip()]
        print(f"Got {len(lines)} non-empty lines")

        for i, line in enumerate(lines):
            try:
                obj = json.loads(line)
                msg = obj.get("message", {})
                has_tc = "tool_calls" in msg
                done = obj.get("done", False)
                if i < 3 or has_tc or done:
                    print(f"  Line {i}: done={done}, has_tc={has_tc}, content={repr(msg.get('content','')[:40])}, thinking={repr(msg.get('thinking','')[:40])}")
                    if has_tc:
                        print(f"    Tool calls: {json.dumps(msg['tool_calls'], indent=2)}")
            except json.JSONDecodeError as e:
                print(f"  Line {i}: PARSE ERROR: {e}")

asyncio.run(main())
