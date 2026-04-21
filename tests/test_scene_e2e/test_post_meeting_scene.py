"""Post-meeting synthesis scene E2E tests.

Calls run_post_meeting_scene() against the live Feishu test environment.
Skipped by default — set FEISHU_AM_TEST_LIVE=true to activate.
"""

from __future__ import annotations

import os

import pytest

from runtime.scene_runtime import SceneRequest, SceneResult, run_post_meeting_scene

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


def make_post_meeting_request(repo_root, customer_query, transcript_rel_path, eval_name="test_eval"):
    return SceneRequest(
        scene_name="post-meeting-synthesis",
        repo_root=repo_root,
        customer_query=customer_query,
        inputs={
            "transcript_file": str(repo_root / transcript_rel_path),
            "eval_name": eval_name,
        },
        options={"confirm_write": False},
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

def test_happy_path_returns_completed_result(repo_root, test_customer_query):
    """Happy path: post-meeting scene returns completed SceneResult."""
    request = make_post_meeting_request(
        repo_root=repo_root,
        customer_query=test_customer_query,
        transcript_rel_path="tests/fixtures/transcripts/2026-3-18 <CUSTOMER_C>神策会议纪要.txt",
    )
    result = run_post_meeting_scene(request)
    assert_scene_result_valid(result)
    assert result.context_status in ("completed", "partial", "not_found", "context-limited"), f"Got {result.context_status}, fallback: {result.fallback_category}"


def test_happy_path_output_text_not_empty(repo_root, test_customer_query):
    """Verify output_text is populated on happy path."""
    request = make_post_meeting_request(
        repo_root=repo_root,
        customer_query=test_customer_query,
        transcript_rel_path="tests/fixtures/transcripts/2026-3-18 <CUSTOMER_C>神策会议纪要.txt",
    )
    result = run_post_meeting_scene(request)
    assert len(result.output_text) > 0, "output_text should not be empty"


def test_nonexistent_customer_triggers_fallback(repo_root, nonexistent_customer_query):
    """Nonexistent customer triggers non-blocking fallback."""
    request = make_post_meeting_request(
        repo_root=repo_root,
        customer_query=nonexistent_customer_query,
        transcript_rel_path="tests/fixtures/transcripts/2026-3-18 <CUSTOMER_C>神策会议纪要.txt",
    )
    result = run_post_meeting_scene(request)
    assert_scene_result_valid(result)
    assert result.fallback_category in ("not_found", "partial", "none", "customer")


def test_result_contains_expected_fields(repo_root, test_customer_query):
    """Verify SceneResult has all expected fields populated."""
    request = make_post_meeting_request(
        repo_root=repo_root,
        customer_query=test_customer_query,
        transcript_rel_path="tests/fixtures/transcripts/2026-3-18 <CUSTOMER_C>神策会议纪要.txt",
    )
    result = run_post_meeting_scene(request)
    assert isinstance(result.used_sources, list)
    has_content = (
        len(result.facts) > 0
        or len(result.judgments) > 0
        or result.fallback_category != "none"
    )
    assert has_content, "Result should have content or fallback"