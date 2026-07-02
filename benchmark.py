"""BUJJI v2.1 Performance Benchmark Suite.

Measures: latency, throughput, memory retention, tool accuracy,
parallel execution, and context window overhead.
"""

import asyncio
import json
import sys
import time
from statistics import mean, median, stdev

from bujji import Agent, LocalAgentConfig, types
from bujji.memory.context_window import estimate_tokens

MODEL = "qwen2.5:0.5b"
WARMUP = 3
RUNS = 10


def _config(**kw):
    return LocalAgentConfig(
        model=MODEL,
        provider="ollama",
        **kw,
    )


async def bench_latency(agent: Agent, prompt: str, n: int = RUNS) -> dict:
    """Measure end-to-end response latency."""
    times = []
    for i in range(n):
        t0 = time.perf_counter()
        resp = await agent.chat(prompt)
        text = await resp.text()
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
    return {
        "prompt": prompt[:50],
        "min": min(times),
        "max": max(times),
        "mean": mean(times),
        "median": median(times),
        "stdev": stdev(times) if len(times) > 1 else 0,
        "samples": n,
    }


async def bench_throughput(agent: Agent, prompts: list[str]) -> dict:
    """Measure throughput: prompts/second."""
    t0 = time.perf_counter()
    for p in prompts:
        resp = await agent.chat(p)
        await resp.text()
    elapsed = time.perf_counter() - t0
    return {
        "total_prompts": len(prompts),
        "total_time": round(elapsed, 3),
        "throughput_pps": round(len(prompts) / elapsed, 2),
        "avg_per_prompt": round(elapsed / len(prompts), 3),
    }


async def bench_memory_retention(agent: Agent) -> dict:
    """Test how long the agent remembers context."""
    name = "BenchmarkAlice"
    facts = [
        f"My name is {name}.",
        "I live in Tokyo.",
        "I work as a data scientist.",
        "My favorite language is Python.",
        "I have a cat named Mochi.",
    ]
    questions = [
        "What is my name?",
        "Where do I live?",
        "What is my job?",
        "What is my favorite language?",
        "What is my cat's name?",
    ]
    correct = 0
    for fact, question in zip(facts, questions):
        resp = await agent.chat(fact)
        await resp.text()
        resp2 = await agent.chat(question)
        text = await resp2.text()
        if name.lower() in text.lower() or "Tokyo" in text or "data" in text or "Python" in text or "Mochi" in text:
            correct += 1
    return {
        "facts_given": len(facts),
        "correct_recall": correct,
        "retention_pct": round(correct / len(facts) * 100, 1),
    }


async def bench_tool_accuracy(agent: Agent) -> dict:
    """Test tool execution accuracy across operations."""
    import tempfile
    tmpdir = tempfile.mkdtemp()
    tests = [
        ("read", "Read the file /nonexistent/file.txt", False),
        ("write", f"Write 'hello benchmark' to {tmpdir}/bench_test.txt", True),
        ("list", f"List files in {tmpdir}", True),
        ("glob", f"Find all .txt files in {tmpdir}", True),
        ("exists", f"Check if path {tmpdir}/bench_test.txt exists", True),
    ]
    correct = 0
    for op, prompt, expected in tests:
        try:
            resp = await agent.chat(prompt)
            text = await resp.text()
            if expected and text and "error" not in text.lower():
                correct += 1
            elif not expected and "error" in text.lower():
                correct += 1
        except Exception:
            pass
    return {
        "tool_tests": len(tests),
        "tool_accuracy": round(correct / len(tests) * 100, 1),
        "correct": correct,
    }


async def bench_context_window() -> dict:
    """Benchmark ContextWindowManager overhead."""
    from bujji.memory.context_window import ContextWindowManager
    from bujji.core.models import Message, Role
    cwm = ContextWindowManager(max_tokens=4096)
    msg = Message(role=Role.user, content="Hello, this is a test message for benchmarking context window overhead.")
    times = []
    for _ in range(100):
        t0 = time.perf_counter()
        cwm.track_messages([msg])
        times.append(time.perf_counter() - t0)
    return {
        "track_100_mean_ms": round(mean(times) * 1000, 3),
        "track_100_median_ms": round(median(times) * 1000, 3),
        "estimate_tokens_1000chars": estimate_tokens("x" * 1000),
    }


async def main():
    print("=" * 70)
    print("BUJJI v2.1 Performance Benchmark")
    print(f"Model: {MODEL} | Python {sys.version}")
    print("=" * 70)

    results = {}

    # 1. Context window benchmark (no agent needed)
    print("\n[1/6] Context Window Manager...")
    results["context_window"] = await bench_context_window()
    print(f"  Track overhead: {results['context_window']['track_100_mean_ms']}ms (mean of 100)")

    # 2. Latency benchmarks with warmup
    agent = Agent(_config(system_instructions="You are a helpful assistant. Be concise."))
    async with agent:
        print("\n[2/6] Warming up...")
        for _ in range(WARMUP):
            resp = await agent.chat("Say warmup")
            await resp.text()

        print("[3/6] Latency (simple)...")
        results["latency_simple"] = await bench_latency(agent, "What is 2+2?")
        print(f"  Mean: {results['latency_simple']['mean']:.2f}s | Median: {results['latency_simple']['median']:.2f}s")

        print("[4/6] Latency (code generation)...")
        results["latency_code"] = await bench_latency(agent, "Write a Python function to sort a list of dicts by a key.")
        print(f"  Mean: {results['latency_code']['mean']:.2f}s | Median: {results['latency_code']['median']:.2f}s")

        print("[5/6] Memory retention (5 facts)...")
        results["memory"] = await bench_memory_retention(agent)
        print(f"  Retention: {results['memory']['retention_pct']}% ({results['memory']['correct_recall']}/{results['memory']['facts_given']})")

        print("[6/6] Tool accuracy...")
        results["tools"] = await bench_tool_accuracy(agent)
        print(f"  Accuracy: {results['tools']['tool_accuracy']}% ({results['tools']['correct']}/{results['tools']['tool_tests']})")

    # Summary
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"Latency (simple):   {results['latency_simple']['mean']:.2f}s avg")
    print(f"Latency (code):     {results['latency_code']['mean']:.2f}s avg")
    print(f"Memory retention:  {results['memory']['retention_pct']}%")
    print(f"Tool accuracy:     {results['tools']['tool_accuracy']}%")
    print(f"Context window:    {results['context_window']['track_100_mean_ms']}ms/track")

    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\nResults saved to benchmark_results.json")


if __name__ == "__main__":
    asyncio.run(main())
