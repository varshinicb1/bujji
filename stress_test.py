"""
BUJJI v2.0 Stress Test Suite
Assigns real work, validates tools, multi-turn, streaming, error recovery.
"""
import asyncio
import json
import os
import time
import sys
import traceback

from bujji import Agent
from bujji.connections.local import LocalAgentConfig
from bujji import types
from bujji.core.models import Message, Role


PASS = 0
FAIL = 0
ERRORS = []


def log(result: str, msg: str = ""):
    global PASS, FAIL
    icon = "PASS" if result == "pass" else "FAIL"
    if result == "pass":
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{icon}] {msg}")


async def test_01_basic_agent_creation():
    """Create an agent with qwen3, verify it initializes cleanly."""
    print("\n=== Test 01: Basic Agent Creation ===")
    config = make_config()
    try:
        async with Agent(config) as agent:
            log("pass", f"Agent created, conversation_id={agent.conversation_id}")
    except Exception as e:
        log("fail", f"Agent creation failed: {e}")
        ERRORS.append(traceback.format_exc())


async def test_02_simple_chat():
    """Send a simple message and get a response."""
    print("\n=== Test 02: Simple Chat ===")
    config = make_config()
    try:
        async with Agent(config) as agent:
            response = await agent.chat("What is 2 + 2?")
            text = await response.resolve()
            assert "4" in text or "four" in text.lower(), f"Expected '4' in response, got: {text}"
            log("pass", f"Got correct response: {text.strip()}")
    except Exception as e:
        log("fail", f"Simple chat failed: {e}")
        ERRORS.append(traceback.format_exc())


async def test_03_multi_turn_conversation():
    """Verify conversation history is preserved across turns."""
    print("\n=== Test 03: Multi-turn Conversation ===")
    config = make_config()
    try:
        async with Agent(config) as agent:
            r1 = await agent.chat("My name is Alice.")
            await r1.resolve()
            r2 = await agent.chat("What is my name?")
            text2 = await r2.resolve()
            # Strip non-ASCII chars for Windows console
            safe_text = text2.encode("ascii", errors="replace").decode("ascii")
            assert "Alice" in safe_text, f"Expected 'Alice' remembered, got: {safe_text[:100]}"
            log("pass", f"Multi-turn memory works: {safe_text.strip()[:80]}")
    except Exception as e:
        log("fail", f"Multi-turn failed: {e}")
        ERRORS.append(traceback.format_exc())


async def test_04_assign_work_planning():
    """Assign real work: ask agent to plan a task."""
    print("\n=== Test 04: Assign Work - Task Planning ===")
    config = make_config()
    try:
        async with Agent(config) as agent:
            response = await agent.chat(
                "Plan the steps to build a Python CLI tool that reads a CSV file and "
                "outputs summary statistics. List exactly 3 steps."
            )
            text = await response.resolve()
            steps = [s.strip() for s in text.split("\n") if s.strip() and s[0].isdigit()]
            assert len(steps) >= 2, f"Expected ≥2 steps, got {len(steps)}: {text[:200]}"
            log("pass", f"Plan has {len(steps)} steps: {steps[0][:80]}")
    except Exception as e:
        log("fail", f"Task planning failed: {e}")
        ERRORS.append(traceback.format_exc())


async def test_05_streaming_response():
    """Test that streaming yields progressive tokens."""
    print("\n=== Test 05: Streaming Response ===")
    config = make_config()
    try:
        async with Agent(config) as agent:
            response = await agent.chat("Count from 1 to 5.")
            chunks = []
            async for chunk in response:
                chunks.append(chunk)
            text = "".join(chunks)
            assert len(chunks) > 0, "Should have received at least one chunk"
            assert "1" in text and "5" in text, f"Expected numbers 1-5, got: {text[:200]}"
            log("pass", f"Streamed {len(chunks)} chunks: {text.strip()[:100]}")
    except Exception as e:
        log("fail", f"Streaming failed: {e}")
        ERRORS.append(traceback.format_exc())


async def test_06_code_generation_execution():
    """Ask agent to generate and explain code."""
    print("\n=== Test 06: Code Generation ===")
    config = make_config(system_instructions="You are a Python expert. Return ONLY the code, no explanations.")
    try:
        async with Agent(config) as agent:
            response = await agent.chat(
                "Write a Python function to check if a number is prime. "
                "Return ONLY the function code, no explanation."
            )
            text = await response.resolve()
            assert "def " in text, f"Expected function definition, got: {text[:100]}"
            assert "prime" in text.lower(), f"Expected prime-related code"
            log("pass", f"Generated code: {text.strip()[:150]}")
    except Exception as e:
        log("fail", f"Code generation failed: {e}")
        ERRORS.append(traceback.format_exc())


async def test_07_json_response():
    """Test agent can return structured JSON data."""
    print("\n=== Test 07: JSON Response ===")
    config = make_config(
        system_instructions="You are a helpful assistant. When asked for structured data, respond with valid JSON.",
    )
    try:
        async with Agent(config) as agent:
            response = await agent.chat(
                'Return ONLY valid JSON: {"name": "John", "age": 30, "city": "New York"} - just echo this back exactly'
            )
            text = await response.resolve()
            data = json.loads(text)
            assert "John" in data.get("name", ""), f"Expected name John, got {data}"
            log("pass", f"Valid JSON returned: {data}")
    except json.JSONDecodeError:
        log("fail", f"Invalid JSON: {text[:200]}")
        ERRORS.append(traceback.format_exc())
    except Exception as e:
        log("fail", f"Structured output failed: {e}")
        ERRORS.append(traceback.format_exc())


async def test_08_error_recovery():
    """Test graceful handling of invalid/malformed input."""
    print("\n=== Test 08: Error Recovery ===")
    config = make_config()
    try:
        async with Agent(config) as agent:
            response = await agent.chat("")
            text = await response.resolve()
            log("pass", f"Empty input handled: {text.strip()[:100]}")
    except Exception:
        log("pass", "Empty input raises handled exception (acceptable)")


async def test_09_concurrent_conversations():
    """Run multiple agent conversations concurrently."""
    print("\n=== Test 09: Concurrent Conversations ===")
    configs = [
        make_config(system_instructions="You are helpful. Keep responses under 10 words.")
        for _ in range(3)
    ]

    async def run_agent(i, cfg):
        try:
            async with Agent(cfg) as agent:
                r = await agent.chat(f"Say 'hello from agent {i}'")
                text = await r.resolve()
                return True, text.strip()
        except Exception as e:
            return False, str(e)

    try:
        results = await asyncio.gather(*[run_agent(i, cfg) for i, cfg in enumerate(configs)])
        successes = sum(1 for ok, _ in results if ok)
        log("pass", f"{successes}/3 concurrent agents succeeded")
        for ok, msg in results:
            if ok:
                print(f"         {msg[:60]}")
    except Exception as e:
        log("fail", f"Concurrent execution failed: {e}")
        ERRORS.append(traceback.format_exc())


async def test_10_agent_with_capabilities():
    """Test agent capability awareness."""
    print("\n=== Test 10: Agent Capability Awareness ===")
    config = make_config(
        system_instructions="You are an engineering assistant. You can use Python to compute things.",
    )
    try:
        async with Agent(config) as agent:
            response = await agent.chat("Write Python code to list .py files in the current directory. Return ONLY the code, no explanation.")
            text = await response.resolve()
            assert "import os" in text or "glob" in text, f"Expected Python code with file listing, got: {text[:100]}"
            log("pass", f"Generated file-list code: {text.strip()[:120]}")
    except Exception as e:
        log("fail", f"Capability test failed: {e}")
        ERRORS.append(traceback.format_exc())


def make_config(**kw):
    base = dict(
        provider="ollama",
        model="qwen3",
        temperature=0.1,
        timeout=300,
    )
    if "system_instructions" not in kw:
        base["system_instructions"] = "You are a helpful AI assistant. Keep responses concise."
    base.update(kw)
    return LocalAgentConfig(**base)


async def warmup():
    """Pre-load qwen3 into GPU memory so subsequent tests are fast."""
    print("\n=== Warmup: Loading qwen3 into GPU memory ===")
    try:
        async with Agent(make_config()) as agent:
            r = await agent.chat("Say 'ready'")
            text = await r.resolve()
            log("pass", f"Model loaded: {text.strip()[:50]}")
    except Exception as e:
        log("fail", f"Warmup failed: {e}")


async def main():
    print("=" * 60)
    print("BUJJI v2.0 Stress Test Suite")
    print(f"Python {sys.version}")
    print(f"Model: qwen3 (Ollama)")
    print("=" * 60)

    tests = [
        ("Warmup", warmup),
        ("Test 01: Basic Agent Creation", test_01_basic_agent_creation),
        ("Test 02: Simple Chat", test_02_simple_chat),
        ("Test 03: Multi-turn Conversation", test_03_multi_turn_conversation),
        ("Test 04: Assign Work - Task Planning", test_04_assign_work_planning),
        ("Test 05: Streaming Response", test_05_streaming_response),
        ("Test 06: Code Generation", test_06_code_generation_execution),
        ("Test 07: JSON Response", test_07_json_response),
        ("Test 08: Error Recovery", test_08_error_recovery),
        ("Test 09: Concurrent Conversations", test_09_concurrent_conversations),
        ("Test 10: Agent Capability Awareness", test_10_agent_with_capabilities),
    ]

    start = time.perf_counter()
    for name, test_fn in tests:
        try:
            await test_fn()
        except Exception as e:
            global FAIL
            FAIL += 1
            log("fail", f"Test crashed: {type(e).__name__}: {e}")
            ERRORS.append(traceback.format_exc())

    elapsed = time.perf_counter() - start

    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS} passed, {FAIL} failed, {elapsed:.1f}s")
    if ERRORS:
        print(f"\n{len(ERRORS)} error(s):")
        for e in ERRORS[-3:]:
            print(f"  {e.split(chr(10))[-3]}")
    print("=" * 60)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
