"""Tests for LLM dispatch and fallback behavior in expert_analysis_helper.py.

Per plan 26-02 Task 5: Tests for run_input_audit/run_output_audit LLM dispatch.
Per OpenCode HIGH concern: explicit LLM error handling with keyword mode fallback.
"""

from __future__ import annotations

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from runtime.expert_analysis_helper import (
    run_input_audit,
    run_output_audit,
    ExpertCardAuditResult,
)
from runtime.expert_card_loader import ExpertCardConfig


class TestLLMDispatchInputAudit:
    """BEHAVIOR: run_input_audit dispatches to LLM when prompt_file present, falls back on error."""

    def test_keyword_mode_when_no_prompt_file(self):
        """When input_card has no prompt_file, keyword mode is used."""
        card = ExpertCardConfig(
            enabled=True,
            expert_name="Test Expert",
            review_type="input_review",
            check_signals=["signal1"],
            output_field="output",
            prompt_file=None,
        )

        # Create a mock container with evidence containing the signal
        from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource
        container = EvidenceContainer()
        container.sources["customer_master"] = EvidenceSource(
            name="customer_master",
            quality="live",
            available=True,
            content=["signal1 present in content"],
        )

        result = run_input_audit(container, card)

        # Should use keyword mode (findings contain FOUND/MISSING)
        assert "FOUND: signal1" in result.findings

    def test_llm_mode_triggered_when_prompt_file_set(self):
        """When input_card has prompt_file, LLM path is attempted."""
        card = ExpertCardConfig(
            enabled=True,
            expert_name="Test Expert",
            review_type="input_review",
            check_signals=["signal1"],
            output_field="output",
            prompt_file="sales-account-strategist.md",
        )

        from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource
        container = EvidenceContainer()
        container.sources["customer_master"] = EvidenceSource(
            name="customer_master",
            quality="live",
            available=True,
            content=["evidence content"],
        )

        # Mock invoke_llm_expert to return a result
        mock_result = MagicMock()
        mock_result.expert_name = "Test Expert"
        mock_result.findings = ["LLM: signal found"]
        mock_result.passed = True
        mock_result.blocked = False
        mock_result.block_reason = None

        with patch("runtime.expert_analysis_helper.invoke_llm_expert", AsyncMock(return_value=mock_result)) as mock_invoke:
            with patch("runtime.expert_analysis_helper.build_input_review_prompt", return_value="mock prompt") as mock_build:
                result = run_input_audit(container, card)

                mock_build.assert_called_once_with(card, container)
                mock_invoke.assert_called_once()
                assert result.expert_name == "Test Expert"
                assert "LLM: signal found" in result.findings

    def test_fallback_on_timeout(self):
        """asyncio.TimeoutError triggers keyword mode fallback."""
        card = ExpertCardConfig(
            enabled=True,
            expert_name="Test Expert",
            review_type="input_review",
            check_signals=["signal1"],
            output_field="output",
            prompt_file="sales-account-strategist.md",
        )

        from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource
        container = EvidenceContainer()
        container.sources["customer_master"] = EvidenceSource(
            name="customer_master",
            quality="live",
            available=True,
            content=["signal1 in evidence"],
        )

        import asyncio
        with patch("runtime.expert_analysis_helper.invoke_llm_expert", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = asyncio.TimeoutError("LLM timeout")

            with patch("runtime.expert_analysis_helper.build_input_review_prompt", return_value="prompt"):
                result = run_input_audit(container, card)

                # Falls back to keyword mode
                assert "FOUND: signal1" in result.findings

    def test_fallback_on_auth_failure(self):
        """401 auth failure triggers keyword mode fallback."""
        card = ExpertCardConfig(
            enabled=True,
            expert_name="Test Expert",
            review_type="input_review",
            check_signals=["signal1"],
            output_field="output",
            prompt_file="sales-account-strategist.md",
        )

        from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource
        container = EvidenceContainer()
        container.sources["customer_master"] = EvidenceSource(
            name="customer_master",
            quality="live",
            available=True,
            content=["signal1 in evidence"],
        )

        with patch("runtime.expert_analysis_helper.invoke_llm_expert", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = ValueError("401 Unauthorized - API key invalid")

            with patch("runtime.expert_analysis_helper.build_input_review_prompt", return_value="prompt"):
                result = run_input_audit(container, card)

                # Falls back to keyword mode
                assert "FOUND: signal1" in result.findings

    def test_fallback_on_rate_limit(self):
        """429 rate limit triggers keyword mode fallback."""
        card = ExpertCardConfig(
            enabled=True,
            expert_name="Test Expert",
            review_type="input_review",
            check_signals=["signal1"],
            output_field="output",
            prompt_file="sales-account-strategist.md",
        )

        from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource
        container = EvidenceContainer()
        container.sources["customer_master"] = EvidenceSource(
            name="customer_master",
            quality="live",
            available=True,
            content=["signal1 in evidence"],
        )

        with patch("runtime.expert_analysis_helper.invoke_llm_expert", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = ValueError("429 Rate limit exceeded")

            with patch("runtime.expert_analysis_helper.build_input_review_prompt", return_value="prompt"):
                result = run_input_audit(container, card)

                # Falls back to keyword mode
                assert "FOUND: signal1" in result.findings

    def test_fallback_on_parse_failure(self):
        """Parse failure triggers keyword mode fallback."""
        card = ExpertCardConfig(
            enabled=True,
            expert_name="Test Expert",
            review_type="input_review",
            check_signals=["signal1"],
            output_field="output",
            prompt_file="sales-account-strategist.md",
        )

        from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource
        container = EvidenceContainer()
        container.sources["customer_master"] = EvidenceSource(
            name="customer_master",
            quality="live",
            available=True,
            content=["signal1 in evidence"],
        )

        with patch("runtime.expert_analysis_helper.invoke_llm_expert", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = ValueError("No parseable findings in LLM response")

            with patch("runtime.expert_analysis_helper.build_input_review_prompt", return_value="prompt"):
                result = run_input_audit(container, card)

                # Falls back to keyword mode
                assert "FOUND: signal1" in result.findings

    def test_fallback_on_empty_response(self):
        """Empty LLM response triggers keyword mode fallback."""
        card = ExpertCardConfig(
            enabled=True,
            expert_name="Test Expert",
            review_type="input_review",
            check_signals=["signal1"],
            output_field="output",
            prompt_file="sales-account-strategist.md",
        )

        from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource
        container = EvidenceContainer()
        container.sources["customer_master"] = EvidenceSource(
            name="customer_master",
            quality="live",
            available=True,
            content=["signal1 in evidence"],
        )

        with patch("runtime.expert_analysis_helper.invoke_llm_expert", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = ValueError("Empty response from LLM")

            with patch("runtime.expert_analysis_helper.build_input_review_prompt", return_value="prompt"):
                result = run_input_audit(container, card)

                # Falls back to keyword mode
                assert "FOUND: signal1" in result.findings


class TestLLMDispatchOutputAudit:
    """BEHAVIOR: run_output_audit dispatches to LLM when prompt_file present, falls back on error."""

    def test_keyword_mode_when_no_prompt_file(self):
        """When output_card has no prompt_file, keyword mode is used."""
        card = ExpertCardConfig(
            enabled=True,
            expert_name="Test Expert",
            review_type="output_review",
            check_signals=["专业性"],
            output_field="output",
            prompt_file=None,
        )

        recommendations = ["使用规范的专业术语"]

        result = run_output_audit(recommendations, card)

        # Should use keyword mode (findings contain PASS/FLAG)
        assert any("PASS:" in f for f in result.findings)

    def test_llm_mode_triggered_when_prompt_file_set(self):
        """When output_card has prompt_file, LLM path is attempted."""
        card = ExpertCardConfig(
            enabled=True,
            expert_name="Test Expert",
            review_type="output_review",
            check_signals=["专业性"],
            output_field="output",
            prompt_file="sales-account-strategist.md",
        )

        recommendations = ["recommendation 1", "recommendation 2"]

        mock_result = MagicMock()
        mock_result.expert_name = "Test Expert"
        mock_result.findings = ["LLM: 专业性 passed"]
        mock_result.passed = True
        mock_result.blocked = False
        mock_result.block_reason = None

        with patch("runtime.expert_analysis_helper.invoke_llm_expert", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_result
            with patch("runtime.expert_analysis_helper.build_output_review_prompt", return_value="mock prompt") as mock_build:
                result = run_output_audit(recommendations, card)

                mock_build.assert_called_once_with(card, recommendations)
                mock_invoke.assert_called_once()
                assert result.expert_name == "Test Expert"

    def test_fallback_on_llm_error_output(self):
        """Any LLM error in output audit triggers keyword mode fallback."""
        card = ExpertCardConfig(
            enabled=True,
            expert_name="Test Expert",
            review_type="output_review",
            check_signals=["专业性"],
            output_field="output",
            prompt_file="sales-account-strategist.md",
        )

        recommendations = ["使用规范的专业术语"]

        with patch("runtime.expert_analysis_helper.invoke_llm_expert", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = Exception("Unexpected LLM error")

            with patch("runtime.expert_analysis_helper.build_output_review_prompt", return_value="prompt"):
                result = run_output_audit(recommendations, card)

                # Falls back to keyword mode
                assert any("PASS:" in f for f in result.findings)
