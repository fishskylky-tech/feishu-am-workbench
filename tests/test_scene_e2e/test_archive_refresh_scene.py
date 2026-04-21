"""Archive refresh scene E2E tests.

Calls run_archive_refresh_scene() against the live Feishu test environment.
Skipped by default — set FEISHU_AM_TEST_LIVE=true to activate.
"""

from __future__ import annotations

import os

import pytest

from runtime.scene_runtime import SceneRequest, SceneResult, run_archive_refresh_scene

RUN_LIVE_TESTS = os.environ.get("FEISHU_AM_TEST_LIVE", "false").lower() == "true"

pytestmark = [
    pytest.mark.skipif(not RUN_LIVE_TESTS, reason="Set FEISHU_AM_TEST_LIVE=true to run live scene E2E tests"),
    pytest.mark.scene_e2e,
]


@pytest.fixture
def repo_root():
    from pathlib import Path
    return Path(__file__).parent.parent.parent


@pytest.fixture
def test_customer_query():
    return "测试客户"


@pytest.fixture
def nonexistent_customer_query():
    return "__test_nonexistent_customer_xyz999__"


def make_archive_refresh_request(repo_root, customer_query, topic_text="客户档案测试"):
    return SceneRequest(
        scene_name="archive-refresh",
        repo_root=repo_root,
        customer_query=customer_query,
        inputs={"topic_text": topic_text},
        options={},
    )


def assert_scene_result_valid(result: SceneResult) -> None:
    assert isinstance(result, SceneResult)
    assert result.scene_name is not None
    assert result.resource_status is not None
    assert result.customer_status is not None
    assert result.context_status is not None
    assert result.write_ceiling is not None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_happy_path_returns_result(repo_root, test_customer_query):
    """Archive refresh scene returns a SceneResult."""
    request = make_archive_refresh_request(
        repo_root=repo_root,
        customer_query=test_customer_query,
    )
    result = run_archive_refresh_scene(request)
    assert_scene_result_valid(result)
    assert result.context_status in ("completed", "partial", "not_found", "context-limited")


def test_output_text_populated(repo_root, test_customer_query):
    """Verify output_text is populated on happy path."""
    request = make_archive_refresh_request(
        repo_root=repo_root,
        customer_query=test_customer_query,
    )
    result = run_archive_refresh_scene(request)
    assert isinstance(result.output_text, str)


def test_nonexistent_customer_triggers_fallback(repo_root, nonexistent_customer_query):
    """Nonexistent customer triggers fallback path."""
    request = make_archive_refresh_request(
        repo_root=repo_root,
        customer_query=nonexistent_customer_query,
    )
    result = run_archive_refresh_scene(request)
    assert_scene_result_valid(result)
    assert result.fallback_category in ("not_found", "partial", "none", "customer")


def test_result_contains_expected_fields(repo_root, test_customer_query):
    """Verify SceneResult has expected structure."""
    request = make_archive_refresh_request(
        repo_root=repo_root,
        customer_query=test_customer_query,
    )
    result = run_archive_refresh_scene(request)
    assert isinstance(result.used_sources, list)
    assert isinstance(result.fallback_category, str)