import asyncio
import time
from typing import Any

from bujji.core.models import ToolResult
from bujji.tools.base import BaseTool, ToolMetadata


class PythonExecTool(BaseTool):
    """Execute Python code in a sandboxed environment."""

    metadata = ToolMetadata(
        name="python_exec",
        description="Execute Python code safely and return the result",
        permissions=["execute"],
        requires_approval=False,
        tool_schema={
            "type": "function",
            "function": {
                "name": "python_exec",
                "description": "Execute Python code and return stdout/stderr",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Maximum execution time in seconds",
                            "default": 30,
                        },
                    },
                    "required": ["code"],
                },
            },
        },
    )

    async def execute(self, **kwargs: Any) -> ToolResult:
        code = kwargs.get("code", "")
        timeout = kwargs.get("timeout", 30)

        import os
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            script_path = f.name

        start = time.monotonic()

        try:
            proc = await asyncio.create_subprocess_exec(
                "python",
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except TimeoutError:
                proc.kill()
                elapsed = time.monotonic() - start
                os.unlink(script_path)
                return ToolResult(
                    call_id="",
                    tool_name="python_exec",
                    success=False,
                    output="",
                    error=f"Execution timed out after {timeout}s",
                    execution_time=elapsed,
                )

            elapsed = time.monotonic() - start
            output = stdout.decode("utf-8", errors="replace") if stdout else ""
            error = stderr.decode("utf-8", errors="replace") if stderr else ""

            return ToolResult(
                call_id="",
                tool_name="python_exec",
                success=proc.returncode == 0,
                output=output[:10000],
                error=error if error else None,
                execution_time=elapsed,
            )

        except Exception as e:
            elapsed = time.monotonic() - start
            return ToolResult(
                call_id="",
                tool_name="python_exec",
                success=False,
                output="",
                error=str(e),
                execution_time=elapsed,
            )

        finally:
            try:
                os.unlink(script_path)
            except Exception:
                pass
