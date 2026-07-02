"""Quick test: basic chat + tool execution loop."""
import asyncio
import os

from bujji import Agent
from bujji.connections.local import LocalAgentConfig
from bujji.tools.filesystem import FilesystemTool


async def main():
    # Test basic chat
    print("=== Test 1: Basic Chat ===")
    config = LocalAgentConfig(provider="ollama", model="qwen3", temperature=0.1, timeout=300)
    async with Agent(config) as agent:
        r = await agent.chat("What is 2+2? Reply briefly.")
        print("Response:", await r.resolve())

    # Test tool execution: write a file
    print("\n=== Test 2: Write File via Tool ===")
    config2 = LocalAgentConfig(
        provider="ollama", model="qwen3", temperature=0.1, timeout=300,
        tools=[FilesystemTool()],
        system_instructions="You can use the filesystem tool to read/write files. When asked to write, use the tool.",
    )
    async with Agent(config2) as agent:
        r = await agent.chat(
            'Use the filesystem tool to write a file called "test_bujji.txt" '
            'with content "Hello from BUJJI tools!"'
        )
        print("Response:", await r.resolve())

    if os.path.exists("test_bujji.txt"):
        with open("test_bujji.txt") as f:
            content = f.read()
        os.remove("test_bujji.txt")
        print(f"\n>>> TOOL EXECUTION: PASS (file content: {content})")
    else:
        print("\n>>> TOOL EXECUTION: No file created")


asyncio.run(main())
