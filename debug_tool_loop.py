"""Debug tool execution loop step by step."""
import asyncio
import logging
import json
from bujji import Agent
from bujji.connections.local import LocalAgentConfig
from bujji.tools.filesystem import FilesystemTool
from bujji.core.models import Message, Role, ToolCall

logging.basicConfig(level=logging.DEBUG)

async def main():
    from bujji.providers.ollama import _serialize_messages, _parse_tool_calls
    from bujji.providers.ollama import OllamaProvider
    from bujji.core.config import Settings

    # Step-by-step: create provider directly
    settings = Settings()
    settings.llm.provider = "ollama"
    settings.llm.model = "qwen3"
    settings.llm.temperature = 0.1
    settings.llm.timeout = 300

    provider = OllamaProvider(dict(
        model="qwen3",
        temperature=0.1,
        timeout=300,
    ))

    schema = {
        "type": "function",
        "function": {
            "name": "filesystem",
            "description": "Read, write, list, and manage files",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["read", "write", "list", "delete", "exists", "glob"]},
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["operation", "path"],
            },
        },
    }

    messages = [
        Message(role=Role.system, content="You can use the filesystem tool to read and write files."),
        Message(role=Role.user, content='Write a file called "test_bujji.txt" with content "Hello from BUJJI tools!"'),
    ]

    print("=== First LLM call ===")
    response = await provider.generate_with_tools(messages, tools=[schema])
    print(f"Content: {repr(response.content[:100])}")
    print(f"Tool calls: {response.tool_calls}")
    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"  -> {tc.name}({tc.arguments})")
            # Try executing
            tool = FilesystemTool()
            result = await tool.execute(**tc.arguments)
            print(f"  -> Result: {result}")

    print("\n=== Check file ===")
    import os
    if os.path.exists("test_bujji.txt"):
        with open("test_bujji.txt") as f:
            print("FILE EXISTS:", f.read())
        os.remove("test_bujji.txt")
    else:
        print("No file created")

asyncio.run(main())
