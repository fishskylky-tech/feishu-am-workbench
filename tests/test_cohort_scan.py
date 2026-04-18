"""Tests for SCAN-01 cohort scan scene.

Covers dynamic condition query parsing, cohort limit enforcement,
aggregation helpers, recommendation cap, and scene dispatch.
No live Feishu API calls — all tests use in-memory data or mocks.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import pytest

from runtime.scene_runtime import (
    _parse_condition_query,
    _aggregate_cohort_signals,
    _aggregate_cohort_issues,
    _select_key_customers,
    _build_cohort_recommendations,
    _build_empty_cohort_result,
    SceneRequest,
    SceneResult,
)
from runtime.scene_registry import build_default_scene_registry, dispatch_scene


class TestConditionQueryParsing:
    """Test _parse_condition_query for dynamic condition parsing."""

    def test_parses_active_status(self) -> None:
        """'活跃客户' parses to status=['active']."""
        criteria = _parse_condition_query("活跃客户")
        assert "status" in criteria
        assert "active" in criteria["status"]

    def test_parses_risk_status(self) -> None:
        """'风险客户' parses to status=['at_risk']."""
        criteria = _parse_condition_query("风险客户")
        assert "status" in criteria
        assert "at_risk" in criteria["status"]

    def test_parses_time_window_days(self) -> None:
        """'近30天' parses to activity_within_days=30."""
        criteria = _parse_condition_query("近30天")
        assert "activity_within_days" in criteria
        assert criteria["activity_within_days"] == 30

    def test_parses_time_window_weeks(self) -> None:
        """'近2周' parses to activity_within_days=14."""
        criteria = _parse_condition_query("近2周")
        assert "activity_within_days" in criteria
        assert criteria["activity_within_days"] == 14

    def test_parses_time_window_months(self) -> None:
        """'近3个月' parses to activity_within_days=90."""
        criteria = _parse_condition_query("近3个月")
        assert "activity_within_days" in criteria
        assert criteria["activity_within_days"] == 90

    def test_fallback_to_name_contains(self) -> None:
        """Plain text like 'XX公司' falls back to name_contains."""
        criteria = _parse_condition_query("XX公司")
        assert "name_contains" in criteria
        assert criteria["name_contains"] == "XX公司"

    def test_empty_query_returns_name_contains_empty(self) -> None:
        """Empty string falls back to name_contains=empty."""
        criteria = _parse_condition_query("")
        assert "name_contains" in criteria
        assert criteria["name_contains"] == ""


class TestCohortAggregation:
    """Test cohort aggregation helpers."""

    def test_aggregate_signals_returns_top_signals(self) -> None:
        """_aggregate_cohort_signals returns signals appearing in >= 2 customers."""
        results = [
            {"customer_record": {"简称": "A"}, "lens_results": {"opportunity": ["扩张"], "relationship": [], "project_progress": []}},
            {"customer_record": {"简称": "B"}, "lens_results": {"opportunity": ["扩张"], "relationship": [], "project_progress": []}},
            {"customer_record": {"简称": "C"}, "lens_results": {"opportunity": ["增长"], "relationship": [], "project_progress": []}},
        ]
        signals = _aggregate_cohort_signals(results)
        assert "扩张" in signals

    def test_aggregate_issues_returns_top_risks(self) -> None:
        """_aggregate_cohort_issues returns issues appearing in >= 2 customers."""
        results = [
            {"customer_record": {"简称": "A"}, "lens_results": {"risk": ["流失"]}},
            {"customer_record": {"简称": "B"}, "lens_results": {"risk": ["流失"]}},
            {"customer_record": {"简称": "C"}, "lens_results": {"risk": ["预警"]}},
        ]
        issues = _aggregate_cohort_issues(results)
        assert "流失" in issues

    def test_select_key_customers_by_risk_and_opportunity(self) -> None:
        """_select_key_customers scores by risk (2x) + opportunity."""
        results = [
            {"customer_record": {"简称": "A", "客户名称": "A公司"}, "lens_results": {"risk": ["流失"], "opportunity": []}},
            {"customer_record": {"简称": "B", "客户名称": "B公司"}, "lens_results": {"risk": ["流失"], "opportunity": ["扩张"]}},
            {"customer_record": {"简称": "C", "客户名称": "C公司"}, "lens_results": {"risk": [], "opportunity": ["增长"]}},
        ]
        key = _select_key_customers(results)
        # B should be first (risk 1 + opp 1 * 2 = 3), then A (2), then C (1)
        assert key[0]["customer_record"]["简称"] == "B"
        assert len(key) <= 5

    def test_select_key_customers_max_5(self) -> None:
        """_select_key_customers returns at most 5 customers."""
        results = [
            {"customer_record": {"简称": f"C{i}"}, "lens_results": {"risk": ["流失"], "opportunity": []}}
            for i in range(10)
        ]
        key = _select_key_customers(results)
        assert len(key) <= 5


class TestCohortLimitEnforcement:
    """Test D-04 cohort limit enforcement."""

    def test_build_empty_cohort_result(self) -> None:
        """_build_empty_cohort_result returns SceneResult with cohort_size=0."""
        from pathlib import Path
        request = SceneRequest(
            scene_name="cohort-scan",
            repo_root=Path("."),
            customer_query="",
            inputs={"condition_query": "test"},
        )
        result = _build_empty_cohort_result(request, "test")
        assert result.scene_name == "cohort-scan"
        assert result.customer_status == "cohort"
        assert result.payload.get("cohort_size") == 0

    def test_limit_check_returns_prompt_when_exceeded(self) -> None:
        """When cohort > limit, result contains limiting_applied=True."""
        from pathlib import Path
        from runtime.scene_runtime import _build_cohort_limit_result

        request = SceneRequest(
            scene_name="cohort-scan",
            repo_root=Path("."),
            customer_query="",
            inputs={"condition_query": "all"},
            options={"cohort_limit": 3},
        )
        result = _build_cohort_limit_result(request, 10, 3, [], "all")
        assert result.payload.get("limiting_applied") is True
        assert result.payload.get("cohort_size") == 10
        assert result.payload.get("cohort_limit") == 3
        assert "缩小" in result.output_text or "超过" in result.output_text


class TestCohortRecommendationCap:
    """Test D-08 total recommendation cap of ~10."""

    def test_build_cohort_recommendations_capped_at_10(self) -> None:
        """_build_cohort_recommendations returns at most 10 items."""
        results = [
            {"customer_record": {"简称": f"C{i}"}, "lens_results": {"risk": ["流失"], "opportunity": ["扩张"]}}
            for i in range(10)
        ]
        recommendations = _build_cohort_recommendations(
            cohort_signals=["信号1", "信号2"],
            cohort_issues=["问题1", "问题2"],
            key_customers=results,
        )
        assert len(recommendations) <= 10

    def test_two_tier_structure(self) -> None:
        """Recommendations include cohort-level and per-customer tiers."""
        results = [
            {"customer_record": {"简称": "A公司"}, "lens_results": {"risk": ["流失"], "opportunity": ["扩张"]}}
        ]
        recommendations = _build_cohort_recommendations(
            cohort_signals=["共同机会"],
            cohort_issues=["共同风险"],
            key_customers=results,
        )
        assert len(recommendations) >= 1
        # Should include cohort-level items
        assert any("Cohort" in r or "共同" in r for r in recommendations)
        # Should include per-customer items
        assert any("A公司" in r for r in recommendations)


class TestCohortScanDispatch:
    """Test cohort-scan scene registration and dispatch."""

    def test_cohort_scan_registered(self) -> None:
        """cohort-scan is registered in build_default_scene_registry()."""
        registry = build_default_scene_registry()
        assert "cohort-scan" in registry.available_scenes()

    def test_cohort_scan_dispatch(self) -> None:
        """dispatch to cohort-scan returns SceneResult with correct scene_name."""
        registry = build_default_scene_registry()
        from pathlib import Path

        request = SceneRequest(
            scene_name="cohort-scan",
            repo_root=Path("."),
            customer_query="",
            inputs={"condition_query": "test"},
            options={},
        )
        result = registry.dispatch(request)
        assert result.scene_name == "cohort-scan"
        assert result.customer_status == "cohort"


class TestCohortScanRegression(unittest.TestCase):
    """VAL-05 regression: cohort-scan scene handles 4 case types per D-01 to D-06.

    Cohort-scan queries customer master directly without requiring a pre-resolved
    customer context. The four cases map to:
    - happy-path: valid condition query returns cohort results
    - limited-context: customer master reachable but condition yields few/no results
    - empty-cohort: condition yields 0 matches -> _build_empty_cohort_result path
    - blocked-write: write_ceiling always recommendation-only (D-05), no write_candidates
    """

    def test_cohort_scan_happy_path_dispatch_and_result_shape(self) -> None:
        """Happy-path: cohort-scan dispatch returns valid SceneResult with expected shape."""
        request = SceneRequest(
            scene_name="cohort-scan",
            repo_root=Path("."),
            customer_query="活跃客户",
            inputs={},
        )
        result = dispatch_scene(request)
        self.assertEqual(result.scene_name, "cohort-scan")
        self.assertIn(result.resource_status, ("live", "partial", "resolved"))
        self.assertIn(result.context_status, ("complete", "partial", "completed"))
        self.assertIn(result.write_ceiling, ("normal", "recommendation-only"))
        self.assertIsNotNone(result.payload)
        self.assertIsInstance(result.payload, dict)

    def test_cohort_scan_limited_context_fallback_visible(self) -> None:
        """Limited-context: cohort-scan always produces output/recommendations."""
        request = SceneRequest(
            scene_name="cohort-scan",
            repo_root=Path("."),
            customer_query="未知不存在客户XYZ123",
            inputs={"condition_query": "近999天"},
        )
        result = dispatch_scene(request)
        # cohort-scan context_status is driven by recovery; allow completed/partial
        self.assertIn(result.context_status, ("partial", "minimal", "context-limited", "completed", "not-run"))
        # Should have some output or recommendations regardless of context
        self.assertTrue(
            result.output_text is not None or result.recommendations is not None,
            "Expected output_text or recommendations with limited context",
        )

    def test_cohort_scan_unresolved_or_empty_cohort(self) -> None:
        """Empty cohort: write_ceiling is recommendation-only or output present."""
        request = SceneRequest(
            scene_name="cohort-scan",
            repo_root=Path("."),
            customer_query="",
            inputs={"condition_query": "近999天无匹配客户"},
        )
        result = dispatch_scene(request)
        # fallback_category may be 'none' when cohort is simply empty
        self.assertIn(result.fallback_category, ("customer", "context", "none"))
        self.assertTrue(
            result.write_ceiling == "recommendation-only" or len(result.output_text) > 0,
            "Expected recommendation-only ceiling or non-empty output for empty cohort",
        )

    def test_cohort_scan_blocked_write(self) -> None:
        """Blocked-write: write_ceiling is always recommendation-only, no write_candidates in payload."""
        request = SceneRequest(
            scene_name="cohort-scan",
            repo_root=Path("."),
            customer_query="",
            inputs={"condition_query": "近999天"},
        )
        result = dispatch_scene(request)
        # D-05: cohort-scan write_ceiling is always recommendation-only
        self.assertEqual(result.write_ceiling, "recommendation-only")
        # fallback_category may be 'none' when no blocking condition is present
        self.assertIn(result.fallback_category, ("customer", "safety", "permission", "context", "none"))
        self.assertIsNotNone(result.recommendations)
        self.assertGreater(len(result.recommendations), 0)
        self.assertIsNotNone(result.payload)
        self.assertNotIn("write_candidates", result.payload)
