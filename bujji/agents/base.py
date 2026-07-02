from abc import ABC, abstractmethod
from typing import Any

from bujji.core.models import ChatRequest, ChatResponse, Plan, RouterDecision


class Agent(ABC):
    """Abstract base for all BUJJI agents."""

    @abstractmethod
    async def process(
        self,
        request: ChatRequest,
        context: dict[str, Any] | None = None,
    ) -> ChatResponse:
        """Process a chat request and return a response."""

    @abstractmethod
    async def plan_task(self, task: str) -> Plan:
        """Create a plan for a given task."""

    @abstractmethod
    async def route_task(self, task: str, plan: Plan) -> RouterDecision:
        """Determine if a task can be handled locally."""
