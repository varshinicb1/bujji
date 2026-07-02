"""Utility modules for BUJJI SDK."""

import logging

from bujji.agent import Agent

__all__ = ["run_interactive_loop"]


async def run_interactive_loop(
    agent: Agent,
    *,
    prompt: str = ">>> ",
    handle_exceptions: bool = True,
) -> None:
    """Run an interactive REPL loop with the given agent.

    Each line of input is sent as a chat message. Type /exit or /quit to stop.
    """
    logging.info("Starting interactive loop. Type /exit or /quit to exit.")
    first = True
    try:
        while True:
            try:
                if first:
                    line = input(prompt)
                    first = False
                else:
                    line = input(prompt)
                line = line.strip()
                if line.lower() in ("/exit", "/quit", "/q"):
                    break
                if not line:
                    continue
                response = await agent.chat(line)
                text = await response.resolve()
                if text:
                    print(text)
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as exc:
                if handle_exceptions:
                    logging.exception("Error in interactive loop")
                    print(f"Error: {exc}")
                else:
                    raise
    finally:
        logging.info("Exiting interactive loop.")
