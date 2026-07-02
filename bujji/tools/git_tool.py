from typing import Any

from bujji.core.models import ToolResult
from bujji.tools.base import BaseTool, ToolMetadata


class GitTool(BaseTool):
    """Execute git commands safely."""

    _DESTRUCTIVE_COMMANDS = {"push --force", "reset --hard", "clean -fd", "branch -D"}

    metadata = ToolMetadata(
        name="git",
        description="Execute Git operations: status, diff, log, commit, branch, checkout, pull, push",
        permissions=["execute"],
        requires_approval=True,
        tool_schema={
            "type": "function",
            "function": {
                "name": "git",
                "description": "Execute a Git command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "args": {
                            "type": "string",
                            "description": "Git arguments (e.g., 'status', 'diff', 'log --oneline -5')",
                        },
                        "workdir": {
                            "type": "string",
                            "description": "Repository working directory",
                        },
                    },
                    "required": ["args"],
                },
            },
        },
    )

    async def execute(self, **kwargs: Any) -> ToolResult:
        import asyncio
        import time

        args = kwargs["args"]
        workdir = kwargs.get("workdir")

        is_destructive = any(
            cmd in args for cmd in self._DESTRUCTIVE_COMMANDS
        )

        if is_destructive and self.config.get("require_approval", True):
            return ToolResult(
                call_id="",
                tool_name="git",
                success=False,
                output="",
                error=f"Destructive operation requires explicit approval: git {args}",
            )

        start = time.monotonic()

        try:
            proc = await asyncio.create_subprocess_exec(
                "git",
                *args.split(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

            elapsed = time.monotonic() - start
            output = stdout.decode("utf-8", errors="replace") if stdout else ""
            error = stderr.decode("utf-8", errors="replace") if stderr else ""

            return ToolResult(
                call_id="",
                tool_name="git",
                success=proc.returncode == 0,
                output=output[:10000],
                error=error if error else None,
                execution_time=elapsed,
            )

        except Exception as e:
            elapsed = time.monotonic() - start
            return ToolResult(
                call_id="",
                tool_name="git",
                success=False,
                output="",
                error=str(e),
                execution_time=elapsed,
            )
