from typing import Any, Optional

from bujji.core.config import Settings
from bujji.core.exceptions import RoutingError
from bujji.core.models import Plan, RouterDecision


CONFIDENCE_PROMPT = """You are a confidence assessment engine.

Given a task and its plan, determine whether this task can be handled
by a local LLM or requires escalation to a stronger model.

Consider:
1. Does this require deep reasoning or creative problem-solving?
2. Is the domain knowledge specialized?
3. Are there security concerns?
4. Is the task well-defined with clear success criteria?
5. Could errors cause significant harm?

Return a JSON object:
{{
  "confidence": <float 0.0-1.0>,
  "can_handle_locally": <bool>,
  "reason": "<brief explanation>",
  "escalation_request": "<if confidence < threshold, detailed escalation request>"
}}

Task: {task}
Plan: {plan}
"""


class Router:
    """Routes tasks based on confidence assessment."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.local_threshold = settings.router.local_threshold

    async def decide(
        self,
        task: str,
        plan: Optional[Plan] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> RouterDecision:
        plan_summary = plan.model_dump_json(indent=2) if plan else "No plan available"

        prompt = CONFIDENCE_PROMPT.format(task=task, plan=plan_summary)

        try:
            from bujji.llm.service import LLMService
            from bujji.providers.factory import get_provider

            provider = get_provider(self.settings)
            llm = LLMService(provider)

            response = await llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            import json
            import re

            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response.content)

            confidence = float(data.get("confidence", 0.5))
            can_handle = data.get("can_handle_locally", False)
            reason = data.get("reason", "")
            escalation = data.get("escalation_request")

            if isinstance(confidence, bool):
                confidence = 0.9 if confidence else 0.3

            can_handle_locally = can_handle and confidence >= self.local_threshold

            return RouterDecision(
                task=task,
                confidence=confidence,
                can_handle_locally=can_handle_locally,
                reason=reason,
                escalation_request=escalation if not can_handle_locally else None,
            )

        except Exception as e:
            raise RoutingError(f"Routing decision failed: {e}") from e
