import uuid
from typing import Any

from bujji.core.exceptions import PlanningError
from bujji.core.models import Plan, Subtask
from bujji.llm.service import LLMService

PLANNER_PROMPT = """You are a software engineering planning assistant.

Given a task, break it down into a structured plan.

Output your response as a JSON object with these fields:
- goal: A clear statement of what needs to be accomplished
- subtasks: A list of subtasks, each with:
  - description: What this subtask does
  - dependencies: List of subtask indices (0-based) that must be done first
  - required_tools: List of tools needed (filesystem, terminal, git, web_search, browser, etc.)
  - estimated_complexity: Float 0.0-1.0 (simple to very complex)
- dependencies: Overall task dependencies
- required_tools: All tools that will be needed
- estimated_complexity: Overall complexity 0.0-1.0
- confidence_score: How confident you are in this plan 0.0-1.0
- reasoning: Brief explanation of your planning approach

Task: {task}
"""


class Planner:
    """Decomposes tasks into structured plans."""

    def __init__(self, llm_service: LLMService) -> None:
        self.llm = llm_service

    async def plan(self, task: str, context: dict[str, Any] | None = None) -> Plan:
        if not task or not task.strip():
            raise PlanningError("Task cannot be empty")

        prompt = PLANNER_PROMPT.format(task=task)

        response = await self.llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        plan_data = self._parse_response(response.content)

        subtasks = []
        for s in plan_data.get("subtasks", []):
            deps = s.get("dependencies", [])
            if deps and isinstance(deps[0], int):
                deps = [str(d) for d in deps]
            subtasks.append(
                Subtask(
                    id=str(uuid.uuid4()),
                    description=s["description"],
                    dependencies=deps,
                    required_tools=s.get("required_tools", []),
                    estimated_complexity=float(s.get("estimated_complexity", 0.5)),
                )
            )

        return Plan(
            task=task,
            goal=plan_data.get("goal", task),
            subtasks=subtasks,
            dependencies=plan_data.get("dependencies", []),
            required_tools=plan_data.get("required_tools", []),
            estimated_complexity=float(plan_data.get("estimated_complexity", 0.5)),
            confidence_score=float(plan_data.get("confidence_score", 0.5)),
            reasoning=plan_data.get("reasoning", ""),
        )

    def _parse_response(self, content: str) -> dict[str, Any]:
        import json
        import re

        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise PlanningError(f"Failed to parse planner response: {e}") from e
