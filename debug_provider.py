"""Debug the OllamaProvider generate_with_tools."""
import asyncio
from bujji.providers.ollama import OllamaProvider
from bujji.core.models import Message, Role

async def main():
    provider = OllamaProvider(dict(
        model="qwen3",
        temperature=0.1,
        timeout=300,
    ))

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
        Message(role=Role.user, content="Write a file called test_bujji.txt with content Hello"),
    ]

    response = await provider.generate_with_tools(messages, tools=[schema])
    print(f"Content: {repr(response.content[:100])}")
    print(f"Tool calls: {response.tool_calls}")
    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"  -> {tc.name}({tc.arguments})")

asyncio.run(main())
