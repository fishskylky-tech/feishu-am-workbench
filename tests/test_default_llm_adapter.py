"""Tests for default_llm_adapter.py."""

from __future__ import annotations

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from runtime.default_llm_adapter import DefaultLLMExpertAgent, LLMError, validate_api_key_config


class TestDefaultLLMExpertAgent:
    """Tests for DefaultLLMExpertAgent."""

    def test_agent_initialization(self):
        """Agent initializes with expert_name and prompt_file."""
        agent = DefaultLLMExpertAgent(
            expert_name="Account Strategist",
            prompt_file="sales-account-strategist.md",
        )
        assert agent.expert_name == "Account Strategist"
        assert agent.prompt_file == "sales-account-strategist.md"

    def test_no_hardcoded_credentials(self):
        """Agent does not hardcode API keys."""
        import inspect
        source = inspect.getsource(DefaultLLMExpertAgent)
        assert "OPENAI_API_KEY" not in source or "os.environ" in source
        assert "sk-0" not in source.lower()

    def test_supports_parallel(self):
        """Agent supports parallel execution."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        assert agent.supports_parallel() is True

    def test_error_classification_timeout(self):
        """Timeout errors are classified correctly."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        error = TimeoutError("Request timed out")
        assert agent._classify_error(error) == LLMError.TIMEOUT

    def test_error_classification_auth_failure(self):
        """Auth failure (401) errors are classified correctly."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        error = Exception("401 Unauthorized")
        assert agent._classify_error(error) == LLMError.AUTH_FAILURE

    def test_error_classification_rate_limit(self):
        """Rate limit (429) errors are classified correctly."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        error = Exception("429 Rate limit exceeded")
        assert agent._classify_error(error) == LLMError.RATE_LIMIT

    def test_error_classification_empty_response(self):
        """Empty response errors are classified correctly."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        error = ValueError("Empty response from LLM")
        assert agent._classify_error(error) == LLMError.EMPTY_RESPONSE

    def test_error_classification_parse_failure(self):
        """Parse failure errors are classified correctly."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        error = ValueError("No parseable findings in LLM response")
        assert agent._classify_error(error) == LLMError.PARSE_FAILURE

    def test_error_classification_generic_api_error(self):
        """Generic API errors default to API_ERROR."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        error = Exception("Some other error")
        assert agent._classify_error(error) == LLMError.API_ERROR

    def test_hallucination_guardrail_blocks_fabricated_signal(self) -> None:
        """Single fabricated signal → entire result BLOCKED (per review MEDIUM fix)."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        result = agent._parse_result(
            "PASS: expansion_plan\nPASS: totally_fabricated_signal",
            {"check_signals": ["expansion_plan"]},
            in_eval_context=False
        )
        assert result.passed is False
        assert result.blocked is True
        assert "fabricated_signal" in (result.block_reason or "")

    def test_hallucination_guardrail_all_signals_valid_passes(self) -> None:
        """All LLM findings reference signals in check_signals → PASSED."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        result = agent._parse_result(
            "PASS: expansion_plan\nPASS: timeline",
            {"check_signals": ["expansion_plan", "timeline"]},
            in_eval_context=False
        )
        assert result.passed is True
        assert result.blocked is False

    def test_hallucination_guardrail_eval_context_fallback(self) -> None:
        """No check_signals + in_eval_context=True → all findings accepted (backward compat)."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        result = agent._parse_result(
            "PASS: some_signal\nPASS: another_signal",
            {},
            in_eval_context=True
        )
        assert result.passed is True
        assert result.blocked is False

    def test_hallucination_guardrail_production_requires_check_signals(self) -> None:
        """Production (in_eval_context=False) without check_signals raises ValueError."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        with pytest.raises(ValueError) as ctx:
            agent._parse_result("PASS: some_signal", {}, in_eval_context=False)
        assert "check_signals missing" in str(ctx.value)

    def test_hallucination_guardrail_case_insensitive(self) -> None:
        """Signal matching is case-insensitive."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        result = agent._parse_result(
            "PASS: EXPANSION_PLAN",
            {"check_signals": ["expansion_plan"]},
            in_eval_context=False
        )
        assert result.passed is True
        assert result.blocked is False

    def test_hallucination_guardrail_hyphenated_signal(self) -> None:
        """Hyphenated signal names handled (per review HIGH fix)."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        result = agent._parse_result(
            "PASS: expansion-plan",
            {"check_signals": ["expansion-plan"]},
            in_eval_context=False
        )
        assert result.passed is True
        assert result.blocked is False

    def test_hallucination_guardrail_multi_word_signal(self) -> None:
        """Multi-word signal names handled (per review HIGH fix)."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        result = agent._parse_result(
            "PASS: champion transition plan",
            {"check_signals": ["champion transition plan"]},
            in_eval_context=False
        )
        assert result.passed is True

    def test_hallucination_guardrail_mixed_valid_fabricated(self) -> None:
        """Mixed valid + fabricated: fabricated blocks entire result even if some valid."""
        agent = DefaultLLMExpertAgent("Test", "test.md")
        result = agent._parse_result(
            "PASS: expansion_plan\nPASS: fabricated_signal",
            {"check_signals": ["expansion_plan"]},
            in_eval_context=False
        )
        assert result.passed is False
        assert result.blocked is True
        assert "fabricated_signal" in (result.block_reason or "")


class TestValidateApiKeyConfig:
    """Tests for API key startup validation (per OpenCode review: friendly error)."""

    def test_missing_openai_key_raises_friendly_error(self, monkeypatch):
        """Missing OPENAI_API_KEY raises EnvironmentError with friendly message."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "openai")

        with pytest.raises(EnvironmentError, match="OPENAI_API_KEY is not set"):
            validate_api_key_config()

    def test_missing_anthropic_key_raises_friendly_error(self, monkeypatch):
        """Missing ANTHROPIC_API_KEY raises EnvironmentError with friendly message."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")

        with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY is not set"):
            validate_api_key_config()

    def test_friendly_error_message_mentions_fallback(self, monkeypatch):
        """Friendly error message mentions fallback to keyword mode."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "openai")

        with pytest.raises(EnvironmentError) as exc_info:
            validate_api_key_config()
        assert "keyword mode" in str(exc_info.value).lower()

    def test_openai_key_present_does_not_raise(self, monkeypatch):
        """Valid OpenAI API key does not raise."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "openai")

        # Should not raise
        validate_api_key_config()

    def test_anthropic_key_present_does_not_raise(self, monkeypatch):
        """Valid Anthropic API key does not raise."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-123")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")

        # Should not raise
        validate_api_key_config()
