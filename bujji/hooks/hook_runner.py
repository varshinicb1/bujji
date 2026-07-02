"""Hook runner executes registered hooks at the appropriate lifecycle points."""

import logging

from bujji.hooks.hooks import Hook, HookEvent, HookResult


class HookRunner:
    def __init__(self) -> None:
        self._hooks: list[Hook] = []

    def register_hook(self, hook: Hook) -> None:
        self._hooks.append(hook)

    async def run_on_turn(
        self, event: HookEvent
    ) -> list[HookResult]:
        results: list[HookResult] = []
        for hook in list(self._hooks):
            try:
                result = await hook.on_turn(event)
                if result:
                    results.append(result)
            except Exception:
                logging.exception(f"Hook {hook.name} failed on_turn")
        return results

    async def run_after_turn(
        self, event: HookEvent
    ) -> list[HookResult]:
        results: list[HookResult] = []
        for hook in list(self._hooks):
            try:
                result = await hook.on_after_turn(event)
                if result:
                    results.append(result)
            except Exception:
                logging.exception(f"Hook {hook.name} failed on_after_turn")
        return results

    async def run_before_tool_call(
        self, event: HookEvent
    ) -> list[HookResult]:
        results: list[HookResult] = []
        for hook in list(self._hooks):
            try:
                result = await hook.on_before_tool_call(event)
                if result and result.blocked:
                    results.append(result)
                    return results
            except Exception:
                logging.exception(f"Hook {hook.name} failed on_before_tool_call")
        return results

    async def run_after_tool_call(
        self, event: HookEvent
    ) -> list[HookResult]:
        results: list[HookResult] = []
        for hook in list(self._hooks):
            try:
                result = await hook.on_after_tool_call(event)
                if result:
                    results.append(result)
            except Exception:
                logging.exception(f"Hook {hook.name} failed on_after_tool_call")
        return results
