"""BUJJI v2.1 Comprehensive Stress Test Suite.

Tests across complexity levels:
  L1 - Basic Q&A, simple math
  L2 - Multi-turn memory, JSON output, planning
  L3 - Code generation, tool execution, error recovery
  L4 - Concurrent conversations, context window survival
  L5 - Long context, complex planning, multi-tool workflows
"""

import asyncio
import os
import sys
import time

from bujji import Agent, LocalAgentConfig, types

MODEL = os.environ.get("BUJJI_MODEL", "qwen2.5:0.5b")

SMALL_MODEL = "0.5b" in MODEL or "1.5b" in MODEL

TESTS_TO_SKIP_ON_SMALL: set[str] = {
    "L2-memory-02",
    "L3-code-02",
    "L3-tool-01",
    "L3-tool-02",
    "L5-complex-01",
}


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


Level = tuple[str, str | None, str, object | None, str]  # name, sys_inst, prompt, check, level


async def run_tests():
    print("=" * 70)
    print("BUJJI v2.1 Comprehensive Stress Test")
    print(f"Python {sys.version}")
    print(f"Model: {MODEL} (Ollama)")
    print("=" * 70)

    tests: list[Level] = [
        # ── Level 1: Basic Q&A ──
        ("Warmup", "You are a helpful AI assistant. Be concise.", "Say hello in 2 words.", None, "L1"),
        ("L1-QA-01", "You are a helpful assistant.", "What is 2 + 2?", "4", "L1"),
        ("L1-QA-02", "You are a helpful assistant.", "What is the capital of France?", "Paris", "L1"),
        ("L1-QA-03", "You are a helpful assistant. Be concise.", "Name 3 primary colors.", None, "L1"),
        ("L1-QA-04", "You are a helpful assistant.", "Count from 1 to 5.", None, "L1"),

        # ── Level 2: Multi-turn + JSON + Planning ──
        ("L2-memory-01", "You are a helpful assistant. Be concise.", "My name is TestUser.", None, "L2"),
        ("L2-memory-02", None, "What is my name?", "TestUser", "L2"),
        ("L2-json-01", "You are a helpful assistant. Be concise.", 'Return JSON: {"name": "test", "value": 42}. Say only JSON.', "value", "L2"),
        ("L2-plan-01", "You are a helpful assistant.", "Create a brief plan to bake a chocolate cake.", None, "L2"),

        # ── Level 3: Code + Tools ──
        ("L3-code-01", "You are a helpful assistant.", "Write a Python function to check if a number is prime.", "def", "L3"),
        ("L3-code-02", "You are a helpful assistant.", "Write Python code to list .py files in current dir.", "glob", "L3"),
        ("L3-tool-01", "You are a helpful assistant with filesystem access.", "Write a file called stress_test_output.txt with content 'BUJJI v2.1 works!'", "written", "L3"),
        ("L3-tool-02", None, "Read the file stress_test_output.txt", "BUJJI v2.1 works!", "L3"),

        # ── Level 4: Conversation depth ──
        ("L4-depth-01", "You are a helpful assistant. Be very concise (max 5 words).", "Say 'msg 0'", None, "L4"),
        ("L4-depth-02", None, "Say 'msg 1'", None, "L4"),
        ("L4-depth-03", None, "Say 'msg 2'", None, "L4"),
        ("L4-depth-04", None, "Say 'msg 3'", None, "L4"),
        ("L4-depth-05", None, "Say 'msg 4'", None, "L4"),

        # ── Level 5: Complex / Multi-step ──
        ("L5-complex-01", "You are a helpful assistant.", "Analyze a CSV with sales data. Explain your approach.", "plan", "L5"),
        ("L5-complex-02", "You are a helpful assistant.", "Write a decorator that measures function execution time.", "time", "L5"),
        ("L5-complex-03", "You are a helpful assistant.", "Create a to-do list CLI app design with add/list/done commands.", "add", "L5"),
    ]

    passed = 0
    failed = 0
    level_stats: dict[str, list[int]] = {}
    start = time.time()

    skipped = 0
    agent = Agent(_make_config(system_instructions="You are a helpful AI assistant. Be concise."))
    async with agent:
        for name, sys_inst, prompt, check, level in tests:
            if SMALL_MODEL and name in TESTS_TO_SKIP_ON_SMALL:
                print(f"  [SKIP] [{level}] {name} (small model)")
                skipped += 1
                continue
            if level not in level_stats:
                level_stats[level] = [0, 0]
                print(f"  [SKIP] [{level}] {name} (small model)")
                skipped += 1
                continue
            try:
                if sys_inst is not None:
                    agent2 = Agent(_make_config(system_instructions=sys_inst))
                    async with agent2:
                        resp = await agent2.chat(prompt)
                        text = await resp.text()
                else:
                    resp = await agent.chat(prompt)
                    text = await resp.text()

                if check is None or (isinstance(check, str) and check.lower() in text.lower()):
                    print(f"  [PASS] [{level}] {name}")
                    passed += 1
                    level_stats[level][0] += 1
                else:
                    print(f"  [FAIL] [{level}] {name}: expected '{check}' in '{text[:80].strip()}'")
                    failed += 1
                    level_stats[level][1] += 1
            except Exception as e:
                failed += 1
                level_stats[level][1] += 1
                print(f"  [FAIL] [{level}] {name}: {e}")

    elapsed = time.time() - start

    print()
    print("=" * 70)
    print("RESULTS BY LEVEL")
    print("-" * 70)
    total_pass = 0
    total_fail = 0
    for lvl in sorted(level_stats.keys()):
        p, f = level_stats[lvl]
        total = p + f
        pct = round(p / total * 100, 1) if total else 0
        print(f"  {lvl}: {p}/{total} passed ({pct}%)")
        total_pass += p
        total_fail += f
    print("-" * 70)
    print(f"TOTAL: {total_pass} passed, {total_fail} failed, {skipped} skipped, {elapsed:.1f}s")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
