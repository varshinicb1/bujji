import pytest

from bujji.core.exceptions import PlanningError
from bujji.planner.engine import Planner


class TestPlanner:
    def test_parse_json_response(self):
        planner = Planner(None)  # type: ignore

        content = '{"goal": "test", "subtasks": [{"description": "sub1", "estimated_complexity": 0.3}], "confidence_score": 0.9, "reasoning": "simple"}'
        result = planner._parse_response(content)
        assert result["goal"] == "test"
        assert len(result["subtasks"]) == 1

    def test_parse_json_from_markdown(self):
        planner = Planner(None)  # type: ignore

        content = """Here's the plan:
        ```json
        {"goal": "test", "subtasks": [{"description": "sub1", "estimated_complexity": 0.5}], "confidence_score": 0.8, "reasoning": "ok"}
        ```
        """
        result = planner._parse_response(content)
        assert result["goal"] == "test"

    def test_parse_invalid_json(self):
        planner = Planner(None)  # type: ignore

        with pytest.raises(PlanningError):
            planner._parse_response("this is not json")

    def test_plan_with_empty_task(self):
        planner = Planner(None)  # type: ignore

        import asyncio
        with pytest.raises(PlanningError):
            asyncio.run(planner.plan(""))
