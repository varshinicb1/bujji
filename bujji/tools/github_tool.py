import os
from typing import Any

import httpx

from bujji.core.models import ToolResult
from bujji.tools.base import BaseTool, ToolMetadata


class GitHubTool(BaseTool):
    """Interact with GitHub API."""

    metadata = ToolMetadata(
        name="github",
        description="Interact with GitHub API: issues, PRs, repos, search",
        permissions=["read", "write"],
        requires_approval=False,
        tool_schema={
            "type": "function",
            "function": {
                "name": "github",
                "description": "GitHub API operations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": [
                                "get",
                                "post",
                                "list_issues",
                                "create_issue",
                                "search_repos",
                                "get_repo",
                                "list_prs",
                            ],
                            "description": "GitHub operation",
                        },
                        "endpoint": {
                            "type": "string",
                            "description": "API endpoint path (e.g., /repos/owner/repo)",
                        },
                        "data": {
                            "type": "object",
                            "description": "Request body data",
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                    },
                    "required": ["operation"],
                },
            },
        },
    )

    async def execute(self, **kwargs: Any) -> ToolResult:
        operation = kwargs.get("operation", "get")
        token = self.config.get("token") or os.getenv("GITHUB_TOKEN")

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "bujji-agent",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if operation == "get":
                    endpoint = kwargs.get("endpoint", "")
                    resp = await client.get(
                        f"https://api.github.com{endpoint}", headers=headers
                    )
                elif operation == "post":
                    endpoint = kwargs.get("endpoint", "")
                    data = kwargs.get("data", {})
                    resp = await client.post(
                        f"https://api.github.com{endpoint}",
                        headers=headers,
                        json=data,
                    )
                elif operation in ("list_issues", "list_prs"):
                    endpoint = kwargs.get("endpoint", "/repos/owner/repo/issues")
                    resp = await client.get(
                        f"https://api.github.com{endpoint}", headers=headers
                    )
                elif operation == "create_issue":
                    endpoint = kwargs.get("endpoint", "")
                    data = kwargs.get("data", {})
                    resp = await client.post(
                        f"https://api.github.com{endpoint}",
                        headers=headers,
                        json=data,
                    )
                elif operation == "search_repos":
                    query = kwargs.get("query", "")
                    resp = await client.get(
                        f"https://api.github.com/search/repositories?q={query}",
                        headers=headers,
                    )
                elif operation == "get_repo":
                    endpoint = kwargs.get("endpoint", "")
                    resp = await client.get(
                        f"https://api.github.com{endpoint}", headers=headers
                    )
                else:
                    return ToolResult(
                        call_id="",
                        tool_name="github",
                        success=False,
                        output="",
                        error=f"Unknown operation: {operation}",
                    )

                resp.raise_for_status()
                data = resp.json()

                import json
                return ToolResult(
                    call_id="",
                    tool_name="github",
                    success=True,
                    output=json.dumps(data, indent=2)[:10000],
                )

        except Exception as e:
            return ToolResult(
                call_id="",
                tool_name="github",
                success=False,
                output="",
                error=str(e),
            )
