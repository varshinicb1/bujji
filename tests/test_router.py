from bujji.core.models import Plan, RouterDecision
from bujji.router.engine import Router


class TestRouter:
    def test_initialization(self, test_settings):
        router = Router(test_settings)
        assert router.local_threshold == 0.7

    def test_custom_threshold(self, test_settings):
        test_settings.router.local_threshold = 0.5
        router = Router(test_settings)
        assert router.local_threshold == 0.5

    def test_router_decision_model(self):
        decision = RouterDecision(
            task="test task",
            confidence=0.95,
            can_handle_locally=True,
            reason="Simple task",
        )
        assert decision.confidence == 0.95
        assert decision.can_handle_locally
        assert decision.escalation_request is None

    def test_escalation_model(self):
        decision = RouterDecision(
            task="complex task",
            confidence=0.3,
            can_handle_locally=False,
            reason="Too complex",
            escalation_request="This requires senior review",
        )
        assert not decision.can_handle_locally
        assert decision.escalation_request is not None
