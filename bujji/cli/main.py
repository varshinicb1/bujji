import asyncio
from pathlib import Path

import click
from bujji import __version__
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from bujji.agents.assistant import AssistantAgent
from bujji.core.config import Settings, load_config

console = Console()
_settings: Settings | None = None
_agent: AssistantAgent | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        config_path = Path.cwd() / "bujji.yaml"
        _settings = load_config(str(config_path) if config_path.exists() else None)
    return _settings


def get_agent(model: str | None = None) -> AssistantAgent:
    global _agent
    settings = get_settings()
    if model:
        settings.llm.model = model
        _agent = None
    if _agent is None:
        _agent = AssistantAgent(settings)
    return _agent


@click.group()
@click.version_option(version=__version__, prog_name="bujji")
def cli() -> None:
    """BUJJI - AI Engineering Assistant for OpenCode."""


@cli.command()
@click.argument("message", required=False)
@click.option("--stream", is_flag=True, help="Stream the response")
@click.option("--model", default=None, help="Model to use (overrides config)")
def chat(message: str | None, stream: bool, model: str | None) -> None:
    """Chat with BUJJI."""
    if not message:
        message = click.prompt("You")
    asyncio.run(_chat(message, stream, model))


async def _chat(message: str, stream: bool, model: str | None = None) -> None:
    from bujji.core.models import ChatRequest
    agent = get_agent(model)
    await agent.initialize()
    response = await agent.process(ChatRequest(message=message, stream=stream))
    console.print(Panel(Markdown(response.response), title="BUJJI", border_style="blue"))


@cli.command()
@click.argument("task")
@click.option("--model", default=None, help="Model to use (overrides config)")
def plan(task: str, model: str | None) -> None:
    """Create a plan for a task."""
    asyncio.run(_plan(task, model))


async def _plan(task: str, model: str | None = None) -> None:
    agent = get_agent(model)
    await agent.initialize()
    plan_result = await agent.planner.plan(task)
    console.print(Panel(f"Goal: {plan_result.goal}", title="Plan", border_style="green"))
    console.print(f"\nConfidence: {plan_result.confidence_score:.2f}")
    console.print(f"Complexity: {plan_result.estimated_complexity:.2f}")
    console.print("\nSubtasks:")
    for i, sub in enumerate(plan_result.subtasks):
        console.print(f"  {i+1}. {sub.description}")
    if plan_result.reasoning:
        console.print(f"\nReasoning: {plan_result.reasoning}")


@cli.command()
def tools() -> None:
    """List available tools."""
    agent = get_agent()
    table = Table(title="BUJJI Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Requires Approval", style="yellow")

    for tool_meta in agent.tools.list_tools():
        table.add_row(
            tool_meta.name,
            tool_meta.description,
            "Yes" if tool_meta.requires_approval else "No",
        )

    console.print(table)


@cli.command()
def doctor() -> None:
    """Run system diagnostics."""
    import sys
    from importlib.metadata import version as pkg_version

    settings = get_settings()

    table = Table(title="BUJJI System Diagnostics")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Detail")

    table.add_row("Python", "OK", sys.version)
    table.add_row("Config", "OK", f"Provider: {settings.llm.provider}")
    table.add_row("Memory", "OK", f"Type: {settings.memory.type}")
    table.add_row("Logging", "OK", f"Level: {settings.logging.level}")

    try:
        ver = pkg_version("bujji")
        table.add_row("Package", "OK", f"v{ver}")
    except Exception:
        table.add_row("Package", "INFO", "Development mode")

    console.print(table)


@cli.command()
def memory() -> None:
    """Show memory statistics."""
    asyncio.run(_memory())


async def _memory() -> None:
    agent = get_agent()
    await agent.initialize()
    stats = await agent.memory.get_stats()
    console.print(Panel(str(stats), title="Memory Stats", border_style="magenta"))


@cli.command()
def status() -> None:
    """Show BUJJI status."""
    settings = get_settings()
    table = Table(title="BUJJI Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Detail")

    table.add_row("LLM Provider", "Ready", f"{settings.llm.provider}/{settings.llm.model}")
    table.add_row("Memory", "Ready", f"{settings.memory.type}")
    table.add_row("Planner", "Ready", "LangGraph")
    table.add_row("Router", "Ready", f"Threshold: {settings.router.local_threshold}")

    console.print(table)


if __name__ == "__main__":
    cli()
