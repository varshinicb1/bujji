from typing import Any, Optional

from bujji.agents.base import Agent
from bujji.core.config import Settings
from bujji.core.models import ChatRequest, ChatResponse, Plan, RouterDecision
from bujji.llm.service import LLMService
from bujji.memory.manager import MemoryManager
from bujji.planner.engine import Planner
from bujji.providers.factory import get_provider
from bujji.router.engine import Router
from bujji.tools.base import ToolRegistry


class AssistantAgent(Agent):
    """Main BUJJI assistant agent coordinating all subsystems."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        provider = get_provider(settings)
        self.llm = LLMService(provider)
        self.memory = MemoryManager(settings)
        self.planner = Planner(self.llm)
        self.router = Router(settings)
        self.tools = ToolRegistry()

    async def initialize(self) -> None:
        await self.memory.initialize()

    def register_tool(self, tool: Any) -> None:
        self.tools.register(tool)

    async def process(
        self,
        request: ChatRequest,
        context: Optional[dict[str, Any]] = None,
    ) -> ChatResponse:
        await self._ensure_initialized()

        plan = await self.plan_task(request.message)
        route = await self.route_task(request.message, plan)

        if route.can_handle_locally:
            response = await self.llm.generate(
                messages=[{"role": "user", "content": request.message}],
            )
            result = response.content
        else:
            result = (
                f"This task requires senior review.\n\n"
                f"Escalation Request:\n{route.escalation_request}"
            )

        await self.memory.store(
            content=f"Q: {request.message}\nA: {result[:500]}",
            entry_type="conversation",
            metadata={"conversation_id": request.conversation_id or ""},
        )

        return ChatResponse(
            response=result,
            conversation_id=request.conversation_id or "new",
            plan=plan,
            router_decision=route,
        )

    async def plan_task(self, task: str) -> Plan:
        return await self.planner.plan(task)

    async def route_task(self, task: str, plan: Plan) -> RouterDecision:
        return await self.router.decide(task, plan)

    async def _ensure_initialized(self) -> None:
        if not self.memory._initialized:
            await self.initialize()
