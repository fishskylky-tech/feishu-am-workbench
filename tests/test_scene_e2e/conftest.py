"""Shared fixtures for scene E2E tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Environment setup for live Feishu test environment
# ---------------------------------------------------------------------------

def _ensure_live_env() -> bool:
    """Return True if live test env should be activated."""
    return os.environ.get("FEISHU_AM_TEST_LIVE", "false").lower() == "true"


@pytest.fixture(scope="session", autouse=True)
def live_env():
    """Set up live Feishu test environment for all scene E2E tests.

    Uses dedicated test environment (separate from production):
    - Base token: OPkWbqrk0amMJusrMGMcf9v7nhc (主数据表有测试数据)
    - Customer archive folder: P2ZgfnJwYlb8FBdis1dcxxKen0f (空目录)
    - Meeting notes folder: QJ4rf3h2ZlQBuKdIs3FcAvexnim (空目录)
    - Customer info folder: XuZVfyoWZlkbyqdZhGXc4ocCnZs (空目录)
    """
    if not _ensure_live_env():
        pytest.skip("FEISHU_AM_TEST_LIVE=true not set — skipping live scene E2E tests")

    # Set test environment variables (override any .env settings)
    os.environ["FEISHU_AM_TEST_LIVE"] = "true"
    os.environ["FEISHU_AM_BASE_TOKEN"] = "OPkWbqrk0amMJusrMGMcf9v7nhc"
    os.environ["FEISHU_AM_CUSTOMER_MASTER_TABLE"] = "客户主数据"
    os.environ["FEISHU_AM_ACTION_PLAN_TABLE"] = "行动计划"
    os.environ["FEISHU_AM_TODO_TABLE"] = "待办"
    os.environ["FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER"] = "P2ZgfnJwYlb8FBdis1dcxxKen0f"
    os.environ["FEISHU_AM_MEETING_NOTES_FOLDER"] = "QJ4rf3h2ZlQBuKdIs3FcAvexnim"
    os.environ["FEISHU_AM_CUSTOMER_INFO_FOLDER"] = "XuZVfyoWZlkbyqdZhGXc4ocCnZs"
    os.environ["FEISHU_AM_TODO_TASKLIST_GUID"] = "e50dda19-63e4-410a-a167-6813f3b3c86d"

    yield

    # Cleanup not needed — env vars persist for test session


# ---------------------------------------------------------------------------
# Test customer identifiers
# ---------------------------------------------------------------------------

@pytest.fixture
def test_customer_query() -> str:
    """Customer query used for scene E2E tests — resolves to test data."""
    return "测试客户"


@pytest.fixture
def nonexistent_customer_query() -> str:
    """Customer query guaranteed to not exist — triggers fallback paths."""
    return "__test_nonexistent_customer_xyz999__"


@pytest.fixture
def repo_root() -> Path:
    """Repo root for scene tests."""
    return Path(".")


# ---------------------------------------------------------------------------
# Verify live environment is accessible
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def live_env_accessible(live_env):
    """Verify live Feishu environment is accessible before running tests."""
    from runtime import LarkCliClient

    cli = LarkCliClient()
    # Quick smoke test: list tables in the base
    try:
        resp = cli.invoke_json([
            "base", "+record-list",
            "--base-token", "OPkWbqrk0amMJusrMGMcf9v7nhc",
            "--table-id", "客户主数据",
            "--limit", "1",
        ])
        return True
    except Exception as exc:
        pytest.skip(f"Live Feishu environment not accessible: {exc}")


# ---------------------------------------------------------------------------
# Scene request factories
# ---------------------------------------------------------------------------

def make_post_meeting_request(
    repo_root: Path,
    customer_query: str,
    transcript_file: str = "tests/fixtures/transcripts/test_transcript.txt",
    eval_name: str = "test_eval",
    confirm_write: bool = False,
) -> "SceneRequest":
    """Factory for post-meeting scene requests."""
    from runtime.scene_runtime import SceneRequest
    return SceneRequest(
        scene_name="post-meeting-synthesis",
        repo_root=repo_root,
        customer_query=customer_query,
        inputs={
            "transcript_file": transcript_file,
            "eval_name": eval_name,
        },
        options={"confirm_write": confirm_write},
    )


def make_archive_refresh_request(
    repo_root: Path,
    customer_query: str,
    topic_text: str = "客户档案测试",
) -> "SceneRequest":
    """Factory for archive-refresh scene requests."""
    from runtime.scene_runtime import SceneRequest
    return SceneRequest(
        scene_name="archive-refresh",
        repo_root=repo_root,
        customer_query=customer_query,
        inputs={"topic_text": topic_text},
        options={},
    )


def make_meeting_prep_request(
    repo_root: Path,
    customer_query: str,
    topic_text: str = "会前准备测试",
    meeting_type: str = "Q2目标对齐",
) -> "SceneRequest":
    """Factory for meeting-prep scene requests."""
    from runtime.scene_runtime import SceneRequest
    return SceneRequest(
        scene_name="meeting-prep",
        repo_root=repo_root,
        customer_query=customer_query,
        inputs={"topic_text": topic_text, "meeting_type": meeting_type},
        options={},
    )


def make_proposal_request(
    repo_root: Path,
    customer_query: str,
    proposal_type: str = "proposal",
    topic_text: str = "提案测试",
) -> "SceneRequest":
    """Factory for proposal scene requests."""
    from runtime.scene_runtime import SceneRequest
    return SceneRequest(
        scene_name="proposal",
        repo_root=repo_root,
        customer_query=customer_query,
        inputs={"proposal_type": proposal_type, "topic_text": topic_text},
        options={},
    )


# ---------------------------------------------------------------------------
# Result assertions
# ---------------------------------------------------------------------------

def assert_scene_result_valid(result: "SceneResult") -> None:
    """Assert SceneResult has valid structure and expected fields."""
    from runtime.scene_runtime import SceneResult

    assert isinstance(result, SceneResult)
    assert result.scene_name is not None
    assert result.resource_status is not None
    assert result.customer_status is not None
    assert result.context_status is not None
    assert result.write_ceiling is not None


def assert_scene_result_completed(result: "SceneResult") -> None:
    """Assert SceneResult reached completed context status."""
    assert_scene_result_valid(result)
    assert result.context_status == "completed", (
        f"Expected context_status=completed, got {result.context_status}. "
        f"Fallback: {result.fallback_category} — {result.fallback_reason}"
    )


def assert_no_blocking_fallback(result: "SceneResult") -> None:
    """Assert result doesn't have a blocking fallback category."""
    assert result.fallback_category != "safety", (
        f"Safety blocker: {result.fallback_message}"
    )
    assert result.fallback_category != "validation", (
        f"Validation blocker: {result.fallback_reason}"
    )


# ---------------------------------------------------------------------------
# Pytest markers (used by .pre-commit-config.yaml and CI)
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """Register custom markers for scene E2E tests."""
    config.addinivalue_line(
        "markers",
        "scene_e2e: end-to-end tests that call real scene runtime functions "
        "against the live Feishu test environment",
    )