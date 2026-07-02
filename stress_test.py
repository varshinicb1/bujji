"""BUJJI Programming Assistant Stress Test.

Tests tiered by model capability:
  Tier 1 (0.5B can do): Code gen, basic Q&A, pattern matching
  Tier 2 (0.5B may do): Debugging, optimization, simple tools
  Tier 3 (8B required): Tool execution, multi-step workflows
  Tier 4 (8B+ required): Architecture, complex planning, multi-tool
"""

import asyncio
import os
import sys
import time

from bujji import Agent, LocalAgentConfig, types

MODEL = os.environ.get("BUJJI_MODEL", "qwen2.5:0.5b")
TIER = {"qwen2.5:0.5b": 1, "qwen3:8b": 3, "qwen3:0.5b": 1}.get(MODEL, 1)


def _make_config(**kwargs):
    return LocalAgentConfig(
        model=MODEL,
        provider="ollama",
        system_instructions=kwargs.pop("system_instructions", None),
        capabilities=types.CapabilitiesConfig(
            enabled_tools=types.BuiltinTools.all_tools()
        ),
        timeout=300,
        max_tokens=8192,
        **kwargs,
    )


Level = tuple[str, str | None, str, object | None, int]  # name, sys_inst, prompt, check, min_tier


async def run_tests():
    print("=" * 70)
    print("BUJJI Programming Assistant Stress Test")
    print(f"Python {sys.version}")
    print(f"Model: {MODEL} (Ollama) — Tier {TIER} capable")
    print("=" * 70)

    tests: list[Level] = [
        # ── TIER 1: Code Generation (0.5B does this well) ──
        ("P1-prime", "You are a senior Python developer. Write clean, correct code only.",
         "Write a Python function is_prime(n) that returns True if n is prime. Return only the function, no explanation.",
         "def is_prime", 1),
        ("P1-fib", "You are a senior Python developer. Write clean, correct code only.",
         "Write a Python function fibonacci(n) that returns the nth Fibonacci number using iteration. Return only the function.",
         "def fibonacci", 1),
        ("P1-sort", "You are a senior Python developer.",
         "Write a Python function quicksort(arr) that sorts a list using quicksort. Return only the code.",
         "def quicksort", 1),
        ("P1-class", "You are a senior Python developer.",
         "Write a Python class Stack with push, pop, and is_empty methods. Return only the class definition.",
         "class Stack", 1),
        ("P1-regex", "You are a senior Python developer.",
         "Write a Python function extract_emails(text) that returns all email addresses found in a string using regex. Return only the function.",
         "def extract_emails", 1),
        ("P1-decorator", "You are a senior Python developer.",
         "Write a Python decorator @timer that prints the execution time of a function. Return only the decorator code.",
         "def timer", 1),
        ("P1-csv-parse", "You are a senior Python developer.",
         "Write a Python function parse_csv_line(line) that splits a comma-separated string into a list, handling quoted fields. Return only the function.",
         "def parse_csv_line", 1),
        ("P1-file-size", "You are a senior Python developer.",
         "Write a Python function get_file_size(path) that returns the size of a file in bytes. Use os.path. Return only the function.",
         "def get_file_size", 1),

        # ── TIER 2: Debugging & Optimization (0.5B may do, 8B owns) ──
        ("P2-find-bug", "You are a code reviewer. Find and explain the bug.",
         "Review this code and find the bug: def sum_list(lst): total = 0; for i in range(len(lst)): total += lst[i]; return None",
         "return", 1),
        ("P2-debug-syntax", "You are a senior Python developer.",
         "Fix: def calc(x, y): result = x + y; return result; print(calc(1 2)). Write the fixed code.",
         "SyntaxError", 2),
        ("P2-optimize", "You are a performance engineer.",
         "Optimize: squares = []; for i in range(len(nums)): squares.append(nums[i] ** 2). Write the one-liner version.",
         "comprehension", 2),
        ("P2-exception", "You are a senior Python developer.",
         "Write a try/except block that catches ZeroDivisionError when dividing a by b. Return only the code.",
         "ZeroDivisionError", 2),

        # ── TIER 3: Tool Execution (requires tool-calling, 8B) ──
        ("P3-fs-write", "You are a Python developer with filesystem access.",
         "Write a file called bujji_test.txt with content 'works'. Use a tool or open().",
         "written", 3),
        ("P3-fs-read", "You are a Python developer.",
         "Read bujji_test.txt and show its contents.",
         "works", 3),
        ("P3-py-run", "You are a developer.",
         "Run python -c \"print(42)\" using the terminal and tell me the output.",
         "42", 3),

        # ── TIER 4: Multi-step + Architecture (8B+) ──
        ("P4-write-test", "You are a senior Python developer.",
         "Write a function is_palindrome(s) and a test with assert. Run the test.",
         "assert True", 4),
        ("P4-sql", "You are a backend developer.",
         "Write a SQL query to find users who joined in the last 30 days from table users(id, name, created_at).",
         "SELECT", 4),
        ("P4-api-design", "You are a senior backend developer.",
         "Design a REST API for a blog (posts, comments, users). List endpoints with HTTP methods.",
         "GET", 4),
        ("P4-project-structure", "You are a software architect.",
         "Design a Python project structure for a CLI todo app (add, list, complete tasks). List files and directories.",
         "todo", 4),
    ]

    passed = 0
    failed = 0
    skipped = 0
    level_stats: dict[str, list[int]] = {}
    start = time.time()

    agent = Agent(_make_config(system_instructions="You are a senior Python developer. Write clean, correct code. Be concise."))
    async with agent:
        for name, sys_inst, prompt, check, min_tier in tests:
            if TIER < min_tier:
                print(f"  [SKIP] [{min_tier}] {name} (needs tier {min_tier}, have tier {TIER})")
                skipped += 1
                continue
            level = f"T{min_tier}"
            if level not in level_stats:
                level_stats[level] = [0, 0]
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
    print("RESULTS BY CAPABILITY TIER")
    print("-" * 70)
    total_pass = total_fail = 0
    for lvl in sorted(level_stats.keys()):
        p, f = level_stats[lvl]
        total = p + f
        pct = round(p / total * 100, 1) if total else 0
        tier_desc = {1: "Code gen (any model)", 2: "Debugging (8B+)", 3: "Tools (8B+)", 4: "Architecture (8B+)"}
        desc = tier_desc.get(int(lvl[1:]), "")
        print(f"  Tier {lvl}: {p}/{total} passed ({pct}%) — {desc}")
        total_pass += p
        total_fail += f
    print("-" * 70)
    print(f"TOTAL: {total_pass} passed, {total_fail} failed, {skipped} skipped, {elapsed:.1f}s")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
