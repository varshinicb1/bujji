from typing import Any, Optional

import httpx

from bujji.core.models import ToolResult
from bujji.tools.base import BaseTool, ToolMetadata


class WebSearchTool(BaseTool):
    """Pluggable web search with multiple providers."""

    _PROVIDERS = {
        "brave": "https://api.search.brave.com/res/v1/web/search",
        "duckduckgo": "https://api.duckduckgo.com/",
        "tavily": "https://api.tavily.com/search",
    }

    metadata = ToolMetadata(
        name="web_search",
        description="Search the web using a pluggable search provider (Brave, DuckDuckGo, Tavily)",
        permissions=["read"],
        requires_approval=False,
        tool_schema={
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "provider": {
                            "type": "string",
                            "enum": ["brave", "duckduckgo", "tavily"],
                            "description": "Search provider to use",
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
        },
    )

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        provider = kwargs.get("provider", self.config.get("provider", "brave"))
        num_results = kwargs.get("num_results", 5)

        if provider == "duckduckgo":
            return await self._search_duckduckgo(query, num_results)
        elif provider == "brave":
            return await self._search_brave(query, num_results)
        elif provider == "tavily":
            return await self._search_tavily(query, num_results)
        else:
            return ToolResult(
                call_id="",
                tool_name="web_search",
                success=False,
                output="",
                error=f"Unknown provider: {provider}",
            )

    async def _search_brave(self, query: str, count: int) -> ToolResult:
        api_key = self.config.get("brave_key")
        if not api_key:
            return ToolResult(
                call_id="",
                tool_name="web_search",
                success=False,
                output="",
                error="Brave API key not configured",
            )

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    self._PROVIDERS["brave"],
                    headers={"X-Subscription-Token": api_key},
                    params={"q": query, "count": count},
                )
                resp.raise_for_status()
                data = resp.json()

            results = []
            for r in data.get("web", {}).get("results", [])[:count]:
                results.append(f"- {r.get('title')}: {r.get('url')}\n  {r.get('description', '')}")

            return ToolResult(
                call_id="",
                tool_name="web_search",
                success=True,
                output="\n\n".join(results) if results else "No results found",
            )
        except Exception as e:
            return ToolResult(
                call_id="", tool_name="web_search", success=False, output="", error=str(e)
            )

    async def _search_duckduckgo(self, query: str, count: int) -> ToolResult:
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                )
                resp.raise_for_status()

            from html.parser import HTMLParser

            class LinkParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.results = []
                    self._capture = False

                def handle_starttag(self, tag, attrs):
                    attrs_dict = dict(attrs)
                    if tag == "a" and "result__a" in attrs_dict.get("class", ""):
                        self._capture = True

                def handle_data(self, data):
                    if self._capture:
                        self.results.append(data.strip())
                        self._capture = False

            parser = LinkParser()
            parser.feed(resp.text)
            results_text = "\n".join(parser.results[:count])

            return ToolResult(
                call_id="",
                tool_name="web_search",
                success=True,
                output=results_text or "No results found",
            )
        except Exception as e:
            return ToolResult(
                call_id="", tool_name="web_search", success=False, output="", error=str(e)
            )

    async def _search_tavily(self, query: str, count: int) -> ToolResult:
        api_key = self.config.get("tavily_key")
        if not api_key:
            return ToolResult(
                call_id="",
                tool_name="web_search",
                success=False,
                output="",
                error="Tavily API key not configured",
            )

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    self._PROVIDERS["tavily"],
                    json={"api_key": api_key, "query": query, "max_results": count},
                )
                resp.raise_for_status()
                data = resp.json()

            results = []
            for r in data.get("results", [])[:count]:
                results.append(f"- {r.get('title')}: {r.get('url')}\n  {r.get('content', '')}")

            return ToolResult(
                call_id="",
                tool_name="web_search",
                success=True,
                output="\n\n".join(results) if results else "No results found",
            )
        except Exception as e:
            return ToolResult(
                call_id="", tool_name="web_search", success=False, output="", error=str(e)
            )
