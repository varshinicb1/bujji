from typing import Any

from bujji.core.models import ToolResult
from bujji.tools.base import BaseTool, ToolMetadata


class DockerTool(BaseTool):
    """Execute Docker commands."""

    metadata = ToolMetadata(
        name="docker",
        description="Execute Docker commands: ps, images, build, run, exec, logs, stop",
        permissions=["execute"],
        requires_approval=True,
        tool_schema={
            "type": "function",
            "function": {
                "name": "docker",
                "description": "Execute Docker commands",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "args": {
                            "type": "string",
                            "description": "Docker arguments (e.g., 'ps -a', 'images', 'logs container_id')",
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
        start = time.monotonic()

        try:
            proc = await asyncio.create_subprocess_exec(
                "docker",
                *args.split(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            elapsed = time.monotonic() - start
            output = stdout.decode("utf-8", errors="replace") if stdout else ""
            error = stderr.decode("utf-8", errors="replace") if stderr else ""

            return ToolResult(
                call_id="",
                tool_name="docker",
                success=proc.returncode == 0,
                output=output[:10000],
                error=error if error else None,
                execution_time=elapsed,
            )

        except Exception as e:
            elapsed = time.monotonic() - start
            return ToolResult(
                call_id="",
                tool_name="docker",
                success=False,
                output="",
                error=str(e),
                execution_time=elapsed,
            )
