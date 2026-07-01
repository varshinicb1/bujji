"""BUJJI v2.0 — Agent with custom tools and MCP."""

import asyncio
from bujji.agent import Agent
from bujji.connections.local.config import LocalAgentConfig
from bujji.tools.base import tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"Sunny, 25°C in {city}"

async def main():
    config = LocalAgentConfig(
        model="qwen2.5-coder:7b",
        tools=[get_weather],
    )
    async with Agent(config) as agent:
        response = await agent.chat("What's the weather in Bangalore?")
        print(await response.text())

if __name__ == "__main__":
    asyncio.run(main())
