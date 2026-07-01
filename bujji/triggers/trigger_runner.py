"""Runner that monitors and fires triggers during an agent session."""

import asyncio
import logging
from typing import Any

from bujji.triggers.triggers import Trigger


class TriggerRunner:
    """Manages trigger lifecycle: checks triggers and fires them."""

    def __init__(
        self,
        triggers: list[Trigger],
        connection: Any,
        *,
        check_interval: float = 1.0,
    ) -> None:
        self._triggers = triggers
        self._connection = connection
        self._check_interval = check_interval
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def __aenter__(self) -> "TriggerRunner":
        self._task = asyncio.create_task(self._run())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                for trigger in list(self._triggers):
                    try:
                        result = await trigger.check()
                        if result:
                            logging.info(f"Trigger {trigger.name} fired")
                            await self._connection.send_trigger_notification(result)
                    except Exception:
                        logging.exception(f"Trigger {trigger.name} check failed")
            except Exception:
                logging.exception("Trigger runner error")
            await asyncio.sleep(self._check_interval)
