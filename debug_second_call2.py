"""Debug second LLM call - try arguments as object vs string."""
import asyncio
import json

import httpx


async def test():
    # Try with arguments as object (not string)
    payload = {
        "model": "qwen3",
        "messages": [
            {"role": "system", "content": "You can use the filesystem tool."},
            {"role": "user", "content": "Write a file called test.txt with content Hello"},
            {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "filesystem", "arguments": {"operation": "write", "path": "test.txt", "content": "Hello"}}}]},
            {"role": "tool", "content": "File written successfully", "name": "filesystem"},
        ],
        "temperature": 0.1,
    }
    print("Payload (arguments as object):")
    print(json.dumps(payload, indent=2))

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post("http://localhost:11434/api/chat", json=payload)
        print(f"\nStatus: {resp.status_code}")
        if resp.status_code == 200:
            raw = resp.text
            lines = [l.strip() for l in raw.split("\n") if l.strip()]
            for ln in lines:
                try:
                    o = json.loads(ln)
                    m = o.get("message", {})
                    c = m.get("content", "")
                    if c:
                        print(f"  content: {repr(c[:80])}")
                    if "tool_calls" in m:
                        print(f"  tool_calls: {json.dumps(m['tool_calls'], indent=2)}")
                except Exception as e:
                    print(f"  parse error: {e}")
        else:
            print(resp.text[:500])

asyncio.run(test())
