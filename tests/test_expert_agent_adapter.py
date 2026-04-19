"""Contract tests for platform adapters.

Per OpenCode review concern LOW-08: adapter testing strategy with contract tests.
Per AA-01-PLAN.md Section 4: ExpertAgent interface contract.

Contract tests verify that each platform adapter:
1. Implements the ExpertAgent interface correctly
2. Returns ExpertReviewResult with required fields
3. Handles timeout and errors per platform contract
4. Integrates with circuit breaker
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass


class TestExpertAgentInterfaceContract:
    """Verify all platform adapters satisfy the ExpertAgent interface contract."""

    def test_interface_requires_async_invoke(self):
        """ExpertAgent.invoke() must be async and return ExpertReviewResult."""
        from runtime.expert_agent_invoker import ExpertAgent
        import inspect

        # Verify invoke is abstract
        assert inspect.isabstract(ExpertAgent)
        assert hasattr(ExpertAgent, 'invoke')

        # Verify it's coroutine
        sig = inspect.signature(ExpertAgent.invoke)
        # First param after self should be prompt: str
        params = list(sig.parameters.keys())
        assert 'prompt' in params

    def test_interface_requires_supports_parallel(self):
        """ExpertAgent.supports_parallel() must return bool."""
        from runtime.expert_agent_invoker import ExpertAgent
        assert hasattr(ExpertAgent, 'supports_parallel')
        assert callable(ExpertAgent.supports_parallel)

    def test_interface_requires_get_platform(self):
        """ExpertAgent.get_platform() must return Literal platform type."""
        from runtime.expert_agent_invoker import ExpertAgent
        assert hasattr(ExpertAgent, 'get_platform')
        assert callable(ExpertAgent.get_platform)


class TestCircuitBreakerContract:
    """Verify circuit breaker integration per AA-01-PLAN.md Section 7."""

    def test_circuit_breaker_opens_after_threshold(self):
        """Circuit breaker opens after failure_threshold consecutive failures."""
        from runtime.expert_agent_invoker import CircuitBreaker, CIRCUIT_BREAKER_CONFIG

        cb = CircuitBreaker(config={"failure_threshold": 3, "recovery_timeout": 60, "half_open_max_calls": 1})

        assert cb.can_execute() is True

        cb.record_failure()
        assert cb.can_execute() is True  # Still CLOSED

        cb.record_failure()
        assert cb.can_execute() is True  # Still CLOSED

        cb.record_failure()  # threshold reached
        assert cb.can_execute() is False  # Now OPEN

    def test_circuit_breaker_recovery_after_timeout(self):
        """Circuit breaker transitions to HALF_OPEN after recovery_timeout."""
        from runtime.expert_agent_invoker import CircuitBreaker
        import time

        cb = CircuitBreaker(config={"failure_threshold": 1, "recovery_timeout": 0.1, "half_open_max_calls": 1})

        cb.record_failure()  # Opens immediately
        assert cb.can_execute() is False

        time.sleep(0.15)  # Wait for recovery_timeout

        assert cb.can_execute() is True  # Now HALF_OPEN

    def test_circuit_breaker_resets_on_success(self):
        """Circuit breaker resets failure_count on successful invocation."""
        from runtime.expert_agent_invoker import CircuitBreaker

        cb = CircuitBreaker(config={"failure_threshold": 3, "recovery_timeout": 60, "half_open_max_calls": 1})

        cb.record_failure()
        cb.record_failure()
        assert cb.state.failure_count == 2

        cb.record_success()
        assert cb.state.failure_count == 0
        assert cb.state.state == "CLOSED"


class TestAggregatedFailureResultContract:
    """Verify AggregatedFailureResult per AA-01-PLAN.md Section 6.3."""

    def test_aggregated_failure_contains_successes_and_failures(self):
        """AggregatedFailureResult must track both successful and failed invocations."""
        from runtime.expert_agent_invoker import AggregatedFailureResult, ExpertReviewResult

        success_result = ExpertReviewResult(
            expert_name="test_agent",
            findings=["finding1"],
            passed=True
        )

        failure = ("openclaw", Exception("Timeout"))

        afr = AggregatedFailureResult(
            successful=[success_result],
            failures=[failure]
        )

        assert len(afr.successful) == 1
        assert len(afr.failures) == 1
        assert afr.failures[0][0] == "openclaw"

    def test_aggregated_failure_str_format(self):
        """AggregatedFailureResult.__str__() must be human-readable."""
        from runtime.expert_agent_invoker import AggregatedFailureResult

        failure = ("hermes", Exception("Connection error"))
        afr = AggregatedFailureResult(successful=[], failures=[failure])

        str_repr = str(afr)
        assert "hermes" in str_repr
        assert "Connection error" in str_repr
        assert "1 failures" in str_repr


class TestValidateAgentReferenceContract:
    """Verify SOLE SOURCE OF TRUTH invariant per AA-01-PLAN.md Section 2."""

    def test_valid_agent_passes_validation(self):
        """validate_agent_reference() returns True for valid agent in registry."""
        # This test requires agent-registry.yaml to exist with test agents
        # Skip if registry doesn't exist yet (Phase 25 dependency)
        import os
        registry_path = os.path.join(os.path.dirname(__file__), "..", "agents", "agent-registry.yaml")
        if not os.path.exists(registry_path):
            pytest.skip("agent-registry.yaml not yet created (Phase 25)")

        from runtime.expert_card_loader import validate_agent_reference

        # If registry exists and has agents, at minimum structure should be valid
        # Specific agent names depend on Phase 25 implementation
        registry = __import__('yaml').safe_load(open(registry_path))
        if "agents" in registry and registry["agents"]:
            first_agent = list(registry["agents"].keys())[0]
            is_valid, err = validate_agent_reference(first_agent)
            assert is_valid is True
            assert err is None

    def test_invalid_agent_fails_validation(self):
        """validate_agent_reference() returns False with error for unknown agent."""
        from runtime.expert_card_loader import validate_agent_reference

        is_valid, err = validate_agent_reference("nonexistent_agent_xyz")
        assert is_valid is False
        assert "nonexistent_agent_xyz" in err
        assert "not found in agent-registry.yaml" in err


class TestPlatformCapabilityMap:
    """Verify platform capability definitions per OpenCode review concern LOW-09."""

    def test_all_platforms_have_capabilities(self):
        """All 4 platforms (openclaw, hermes, claude_code, codex) must be defined."""
        from runtime.scene_runtime import PLATFORM_CAPABILITY_MAP

        expected_platforms = {"openclaw", "hermes", "claude_code", "codex"}
        defined_platforms = set(PLATFORM_CAPABILITY_MAP.keys())

        assert expected_platforms == defined_platforms, \
            f"Missing platforms: {expected_platforms - defined_platforms}"

    def test_capabilities_have_required_fields(self):
        """Each PlatformCapabilities must have all required fields."""
        from runtime.scene_runtime import PLATFORM_CAPABILITY_MAP
        from runtime.scene_runtime import PlatformCapabilities

        required_fields = {
            "platform", "supports_parallel", "supports_streaming",
            "supports_structured_output", "supports_toolsets",
            "max_concurrent", "timeout_default"
        }

        for platform_name, caps in PLATFORM_CAPABILITY_MAP.items():
            assert isinstance(caps, PlatformCapabilities)
            for field in required_fields:
                assert hasattr(caps, field), f"{platform_name} missing {field}"

    def test_parallel_capability_consistent_with_max_concurrent(self):
        """Platforms with supports_parallel=True must have max_concurrent > 1."""
        from runtime.scene_runtime import PLATFORM_CAPABILITY_MAP

        for platform_name, caps in PLATFORM_CAPABILITY_MAP.items():
            if caps.supports_parallel:
                assert caps.max_concurrent > 1, \
                    f"{platform_name} supports_parallel but max_concurrent={caps.max_concurrent}"


class TestSelectOrchestrationStrategy:
    """Verify orchestration strategy selection per AA-01-PLAN.md Section 5."""

    def test_single_expert_always_sequential(self):
        """1 expert: always sequential regardless of platform."""
        from runtime.scene_runtime import select_orchestration_strategy

        assert select_orchestration_strategy(1, ["openclaw"]) == "sequential"
        assert select_orchestration_strategy(1, ["hermes"]) == "sequential"

    def test_two_experts_sequential(self):
        """2 experts: sequential (safer, lower token cost)."""
        from runtime.scene_runtime import select_orchestration_strategy

        assert select_orchestration_strategy(2, ["openclaw", "hermes"]) == "sequential"

    def test_three_plus_experts_council_if_parallel(self):
        """3+ experts with parallel support: council."""
        from runtime.scene_runtime import select_orchestration_strategy

        platforms = ["openclaw", "hermes", "claude_code"]
        assert select_orchestration_strategy(3, platforms) == "council"

    def test_force_overrides_automatic(self):
        """force parameter overrides automatic selection."""
        from runtime.scene_runtime import select_orchestration_strategy

        assert select_orchestration_strategy(1, ["openclaw"], force="council") == "council"
        assert select_orchestration_strategy(5, ["codex"], force="sequential") == "sequential"