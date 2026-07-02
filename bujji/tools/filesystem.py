from pathlib import Path
from typing import Any

from bujji.core.models import ToolResult
from bujji.tools.base import BaseTool, ToolMetadata


def _result(**kw: Any) -> ToolResult:
    return ToolResult(call_id="", tool_name="filesystem", **kw)


class FilesystemTool(BaseTool):
    """Read, write, list, and manage files."""

    metadata = ToolMetadata(
        name="filesystem",
        description="Read, write, list, and manage files on the local filesystem",
        permissions=["read", "write"],
        requires_approval=False,
        tool_schema={
            "type": "function",
            "function": {
                "name": "filesystem",
                "description": "Read, write, list, and manage files",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": [
                                "read",
                                "write",
                                "list",
                                "copy",
                                "move",
                                "delete",
                                "exists",
                                "glob",
                            ],
                            "description": "File operation to perform",
                        },
                        "path": {
                            "type": "string",
                            "description": "File or directory path",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content for write operations",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern for listing",
                        },
                    },
                    "required": ["operation", "path"],
                },
            },
        },
    )

    async def execute(self, **kwargs: Any) -> ToolResult:
        operation = kwargs.get("operation", "list")
        path = Path(kwargs["path"]).expanduser().resolve()
        content = kwargs.get("content")
        pattern = kwargs.get("pattern")

        try:
            if operation == "read":
                if not path.exists():
                    return _result(success=False, output="", error=f"Path not found: {path}")
                if path.is_dir():
                    items = [str(p.relative_to(path)) for p in path.iterdir()]
                    return _result(success=True, output="\n".join(sorted(items)))
                return _result(success=True, output=path.read_text(encoding="utf-8"))

            elif operation == "write":
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content or "", encoding="utf-8")
                return _result(success=True, output=f"Written {len(content or '')} bytes to {path}")

            elif operation == "list":
                if not path.exists():
                    return _result(success=False, output="", error=f"Path not found: {path}")
                items = []
                for p in path.iterdir():
                    suffix = "/" if p.is_dir() else ""
                    items.append(f"{p.name}{suffix}")
                return _result(success=True, output="\n".join(sorted(items)))

            elif operation == "glob":
                if pattern:
                    matches = list(path.glob(pattern))
                    return _result(success=True, output="\n".join(str(m) for m in matches))
                return _result(success=True, output="")

            elif operation == "exists":
                return _result(success=True, output=str(path.exists()))

            elif operation in ("copy", "move"):
                dest = Path(kwargs.get("dest", ""))
                if not dest:
                    return _result(success=False, output="", error="dest required for copy/move")
                if operation == "copy":
                    path.write_text(path.read_text(encoding="utf-8") if path.exists() else "")
                else:
                    path.rename(dest)
                return _result(success=True, output=f"{operation} {path} -> {dest}")

            elif operation == "delete":
                if path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                else:
                    path.unlink()
                return _result(success=True, output=f"Deleted {path}")

            else:
                return _result(success=False, output="", error=f"Unknown operation: {operation}")

        except Exception as e:
            return _result(success=False, output="", error=str(e))
