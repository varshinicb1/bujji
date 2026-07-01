"""Policy enforcement hook for BUJJI SDK.

Wraps safety/compliance policies as a hook that runs on each turn.
"""

from bujji.hooks.hooks import Hook


def enforce(policies: list) -> Hook:
    """Create a hook from a list of policy instances."""
    from bujji.hooks.hooks import HookEvent
    class EnforceHook(Hook):
        name = "policy_enforcer"

        async def on_turn(self, event: HookEvent) -> None:
            for p in policies:
                p.apply(event)

        async def on_after_turn(self, event: HookEvent) -> None:
            for p in policies:
                p.validate_output(event)

    return EnforceHook()
