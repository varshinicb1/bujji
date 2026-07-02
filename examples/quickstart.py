"""BUJJI v2.0 Quickstart — local-first AI agent with Ollama."""

import asyncio

from bujji.agent import Agent
from bujji.connections.local.config import LocalAgentConfig


async def main():
    config = LocalAgentConfig(
        model="qwen2.5-coder:7b",
        system_instructions="You are a helpful coding assistant.",
    )
    async with Agent(config) as agent:
        response = await agent.chat("Write a Python function to check if a number is prime.")
        print(await response.text())

if __name__ == "__main__":
    asyncio.run(main())
