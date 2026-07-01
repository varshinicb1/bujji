from typing import Any, Optional

import httpx

from bujji.core.models import ToolResult
from bujji.tools.base import BaseTool, ToolMetadata


class DocumentationTool(BaseTool):
    """Search documentation sites for answers."""

    metadata = ToolMetadata(
        name="documentation",
        description="Search documentation from various sources (Python, FastAPI, general web docs)",
        permissions=["read"],
        requires_approval=False,
        tool_schema={
            "type": "function",
            "function": {
                "name": "documentation",
                "description": "Search documentation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Documentation search query",
                        },
                        "source": {
                            "type": "string",
                            "enum": ["python", "fastapi", "general"],
                            "description": "Documentation source",
                            "default": "general",
                        },
                    },
                    "required": ["query"],
                },
            },
        },
    )

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        source = kwargs.get("source", "general")

        search_urls = {
            "python": f"https://docs.python.org/3/search.html?q={query}",
            "fastapi": f"https://fastapi.tiangolo.com/search/?q={query}",
            "general": f"https://duckduckgo.com/html/?q={query}+documentation",
        }

        url = search_urls.get(source, search_urls["general"])

        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()

            from html.parser import HTMLParser

            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                    self._skip = False

                def handle_data(self, data):
                    stripped = data.strip()
                    if stripped:
                        self.text.append(stripped)

            parser = TextExtractor()
            parser.feed(resp.text)
            content = " ".join(parser.text)[:5000]

            return ToolResult(
                call_id="",
                tool_name="documentation",
                success=True,
                output=content if content else f"No documentation found for: {query}",
            )

        except Exception as e:
            return ToolResult(
                call_id="",
                tool_name="documentation",
                success=False,
                output="",
                error=str(e),
            )
