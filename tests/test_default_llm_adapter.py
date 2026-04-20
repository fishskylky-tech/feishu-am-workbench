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
