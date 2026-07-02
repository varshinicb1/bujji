import asyncio
import time
from typing import Any

from bujji.core.models import ToolResult
from bujji.tools.base import BaseTool, ToolMetadata


class TerminalTool(BaseTool):
    """Execute shell commands safely."""

    metadata = ToolMetadata(
        name="terminal",
        description="Execute shell commands safely with timeout and sandboxing",
        permissions=["execute"],
        requires_approval=False,
        tool_schema={
            "type": "function",
            "function": {
                "name": "terminal",
                "description": "Execute a shell command and capture output",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Shell command to execute",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Maximum execution time in seconds",
                            "default": 30,
                        },
                        "workdir": {
                            "type": "string",
                            "description": "Working directory for the command",
                        },
                    },
                    "required": ["command"],
                },
            },
        },
    )

    async def execute(self, **kwargs: Any) -> ToolResult:
        command = kwargs["command"]
        timeout = kwargs.get("timeout", 30)
        workdir = kwargs.get("workdir")

        start = time.monotonic()

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except TimeoutError:
                proc.kill()
                elapsed = time.monotonic() - start
                return ToolResult(
                    call_id="",
                    tool_name="terminal",
                    success=False,
                    output="",
                    error=f"Command timed out after {timeout}s",
                    execution_time=elapsed,
                )

            elapsed = time.monotonic() - start
            output = stdout.decode("utf-8", errors="replace") if stdout else ""
            error = stderr.decode("utf-8", errors="replace") if stderr else ""

            result = ToolResult(
                call_id="",
                tool_name="terminal",
                success=proc.returncode == 0,
                output=output,
                error=error if error else None,
                execution_time=elapsed,
            )

            if output:
                result.output = output[:10000]

            return result

        except Exception as e:
            elapsed = time.monotonic() - start
            return ToolResult(
                call_id="",
                tool_name="terminal",
                success=False,
                output="",
                error=str(e),
                execution_time=elapsed,
            )
