"""Trigger abstractions for background agent execution.

Triggers define conditions under which an agent is automatically invoked.
"""

import abc
from typing import Any


class Trigger(abc.ABC):
    """Base class for all triggers."""

    name: str = "unnamed_trigger"

    @abc.abstractmethod
    async def check(self) -> str | None:
        """Return a prompt string if the trigger should fire, None otherwise."""
        ...

    async def cleanup(self) -> None:
        pass


class TimeBasedTrigger(Trigger):
    name = "time_based"

    def __init__(self, interval_seconds: float, prompt_factory: Any) -> None:
        self.interval = interval_seconds
        self._prompt_factory = prompt_factory

    async def check(self) -> str | None:
        import asyncio
        await asyncio.sleep(self.interval)
        if callable(self._prompt_factory):
            return self._prompt_factory()
        return str(self._prompt_factory)


class EventBasedTrigger(Trigger):
    name = "event_based"

    def __init__(self, event_source: Any, prompt_template: str) -> None:
        self._event_source = event_source
        self._prompt_template = prompt_template

    async def check(self) -> str | None:
        event = await self._event_source()
        if event:
            return self._prompt_template.format(event=event)
        return None


class IntervalTrigger(Trigger):
    name = "interval"

    def __init__(self, interval_seconds: float, prompt: str) -> None:
        self.interval = interval_seconds
        self._prompt = prompt

    async def check(self) -> str | None:
        import asyncio
        await asyncio.sleep(self.interval)
        return self._prompt
