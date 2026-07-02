"""BUJJI v2.0 — Stream response tokens in real-time."""

import asyncio

from bujji.agent import Agent
from bujji.connections.local.config import LocalAgentConfig


async def main():
    config = LocalAgentConfig(
        model="qwen2.5-coder:7b",
    )
    async with Agent(config) as agent:
        response = await agent.chat("Explain how async/await works in Python.")
        print("Response: ")
        async for chunk in response:
            print(chunk, end="", flush=True)
        print()

if __name__ == "__main__":
    asyncio.run(main())
