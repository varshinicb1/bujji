"""BUJJI v2.0 — AirLLM god-tier mode with Qwen3-32B on a 6GB GPU.

Requires: Python 3.12 with CUDA torch and airllm installed.
  py -3.12 -m pip install airllm

Uses the Router: simple tasks go to Ollama (Qwen2.5-Coder:7b),
complex reasoning escalates to AirLLM (Qwen3-32B).
"""

import asyncio

from bujji.agent import Agent
from bujji.connections.local.config import LocalAgentConfig

config = LocalAgentConfig(
    model="qwen2.5-coder:7b",
    system_instructions=(
        "You are BUJJI, a coding assistant with dual-model architecture. "
        "For simple questions, respond directly. For complex coding tasks, "
        "plan carefully before answering."
    ),
)

async def main():
    async with Agent(config) as agent:
        response = await agent.chat("Write a complete REST API server in FastAPI")
        print(await response.text())

if __name__ == "__main__":
    asyncio.run(main())
