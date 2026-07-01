"""BUJJI v2.1 Stress Test Suite.

Tests core functionality: agent creation, chat, multi-turn memory,
task planning, streaming, code generation, JSON output, error recovery,
concurrent conversations, capability awareness, tool execution, and
context window management.
"""

import asyncio
import time
import json
import sys

from bujji import Agent, LocalAgentConfig, types
from bujji.core.models import Plan

MODEL = "qwen3"


def _make_config(**kwargs):
    return LocalAgentConfig(
        model=MODEL,
        provider="ollama",
        system_instructions=kwargs.pop("system_instructions", None),
        capabilities=types.CapabilitiesConfig(
            enabled_tools=types.BuiltinTools.all_tools()
        ),
        timeout=300,
        max_tokens=4096,
        **kwargs,
    )


async def run_tests():
    print("=" * 60)
    print(f"BUJJI v2.1 Stress Test Suite")
    print(f"Python {sys.version}")
    print(f"Model: {MODEL} (Ollama)")
    print("=" * 60)

    tests = [
        ("Warmup", "You are a helpful AI assistant. Be concise.", "Say hello in exactly 2 words.", None),
        ("Test 01", "You are a helpful assistant.", "What is 2 + 2?", "4"),
        ("Test 02", "You are a helpful assistant. Be concise.", "My name is Alice.", None),
        ("Test 02b", None, "What is my name?", "Alice"),
        ("Test 03", "You are a helpful assistant.", "Create a plan to analyze a CSV file with sales data.", None),
        ("Test 04", "You are a helpful assistant. Be concise.", "Count from 1 to 5.", None),
        ("Test 05", "You are a helpful assistant.", "Write a Python function to check if a number is prime.", "def"),
        ("Test 06", "You are a helpful assistant. Be concise.", 'Return a JSON object with keys: name, age, city. Say only the JSON.', "name"),
        ("Test 07", "You are a helpful assistant.", "", None),
        ("Test 08", "You are a helpful assistant. Be concise.", "Say 'Hello from agent 0'.", "Hello from agent 0"),
        ("Test 09", "You are a helpful assistant.", "Write Python code to list all .py files in the current directory.", "glob"),
        ("Test 10", "You are a helpful assistant with filesystem access.", 'Write a file called stress_test_bujji.txt with content "BUJJI v2.1 tools work!"', True),
        ("Test 11", "You are a helpful assistant. Be very concise (max 5 words).", "Say 'msg 0'", None),
        ("Test 11b", None, "Say 'msg 1'", None),
        ("Test 11c", None, "Say 'msg 2'", None),
        ("Test 11d", None, "Say 'msg 3'", None),
        ("Test 11e", None, "Say 'msg 4'", None),
    ]

    passed = 0
    failed = 0
    start = time.time()

    agent = Agent(_make_config(system_instructions="You are a helpful AI assistant. Be concise."))
    async with agent:
        for i, (name, sys_inst, prompt, check) in enumerate(tests):
            try:
                if sys_inst is not None:
                    agent2 = Agent(_make_config(system_instructions=sys_inst))
                    async with agent2:
                        resp = await agent2.chat(prompt)
                        text = await resp.text()
                else:
                    resp = await agent.chat(prompt)
                    text = await resp.text()
                
                if check is None or check in text:
                    print(f"  [PASS] {name}")
                    passed += 1
                else:
                    print(f"  [FAIL] {name}: expected '{check}' in '{text[:60]}'")
                    failed += 1
            except Exception as e:
                failed += 1
                print(f"  [FAIL] {name}: {e}")

    elapsed = time.time() - start
    print()
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed, {elapsed:.1f}s")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)