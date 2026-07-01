from typing import Any, Optional

from bujji.core.models import ToolResult
from bujji.tools.base import BaseTool, ToolMetadata


class BrowserTool(BaseTool):
    """Browser automation via Playwright."""

    metadata = ToolMetadata(
        name="browser",
        description="Browser automation: navigate, click, type, screenshot, extract content",
        permissions=["read", "write"],
        requires_approval=False,
        tool_schema={
            "type": "function",
            "function": {
                "name": "browser",
                "description": "Control a web browser",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "navigate",
                                "click",
                                "type",
                                "screenshot",
                                "extract",
                                "scroll",
                                "wait",
                            ],
                            "description": "Browser action to perform",
                        },
                        "url": {
                            "type": "string",
                            "description": "URL to navigate to",
                        },
                        "selector": {
                            "type": "string",
                            "description": "CSS selector for element interaction",
                        },
                        "text": {
                            "type": "string",
                            "description": "Text to type",
                        },
                        "wait_ms": {
                            "type": "integer",
                            "description": "Wait time in milliseconds",
                        },
                    },
                    "required": ["action"],
                },
            },
        },
    )

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "")

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return ToolResult(
                call_id="",
                tool_name="browser",
                success=False,
                output="",
                error="Playwright not installed. Install with: pip install bujji[browser]",
            )

        headless = self.config.get("headless", True)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=headless)
                page = await browser.new_page()

                try:
                    if action == "navigate":
                        url = kwargs.get("url", "")
                        if not url:
                            return ToolResult(
                                call_id="", tool_name="browser", success=False, output="", error="URL required"
                            )
                        await page.goto(url, wait_until="networkidle")
                        title = await page.title()
                        return ToolResult(
                            call_id="",
                            tool_name="browser",
                            success=True,
                            output=f"Navigated to {url}\nTitle: {title}",
                        )

                    elif action == "click":
                        selector = kwargs.get("selector", "")
                        await page.click(selector)
                        return ToolResult(
                            call_id="", tool_name="browser", success=True, output=f"Clicked {selector}"
                        )

                    elif action == "type":
                        selector = kwargs.get("selector", "")
                        text = kwargs.get("text", "")
                        await page.fill(selector, text)
                        return ToolResult(
                            call_id="", tool_name="browser", success=True, output=f"Typed into {selector}"
                        )

                    elif action == "screenshot":
                        screenshot = await page.screenshot(full_page=True)
                        import base64
                        b64 = base64.b64encode(screenshot).decode()
                        return ToolResult(
                            call_id="",
                            tool_name="browser",
                            success=True,
                            output=f"data:image/png;base64,{b64}",
                        )

                    elif action == "extract":
                        content = await page.content()
                        text = await page.evaluate("() => document.body.innerText")
                        return ToolResult(
                            call_id="",
                            tool_name="browser",
                            success=True,
                            output=text[:10000],
                        )

                    elif action == "scroll":
                        await page.evaluate("window.scrollBy(0, window.innerHeight)")
                        return ToolResult(
                            call_id="", tool_name="browser", success=True, output="Scrolled down"
                        )

                    elif action == "wait":
                        wait_ms = kwargs.get("wait_ms", 1000)
                        import asyncio
                        await asyncio.sleep(wait_ms / 1000)
                        return ToolResult(
                            call_id="", tool_name="browser", success=True, output=f"Waited {wait_ms}ms"
                        )

                    else:
                        return ToolResult(
                            call_id="", tool_name="browser", success=False, output="", error=f"Unknown action: {action}"
                        )

                finally:
                    await browser.close()

        except Exception as e:
            return ToolResult(
                call_id="", tool_name="browser", success=False, output="", error=str(e)
            )
