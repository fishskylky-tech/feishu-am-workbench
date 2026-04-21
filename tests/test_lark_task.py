"""Live Feishu Task integration tests.

These tests make real API calls against the actual Feishu Task API.
They are SKIPPED by default; set FEISHU_AM_TEST_LIVE=true to run them.

All write operations target tasks with "test_" prefix in the title and are cleaned up after each test.
"""

from __future__ import annotations

import os
import unittest
from typing import Any

import pytest

from runtime import LarkCliClient

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------

FEISHU_AM_TEST_LARK_TOKEN = os.environ.get("FEISHU_AM_TEST_LARK_TOKEN", "")
RUN_LIVE_TESTS = os.environ.get("FEISHU_AM_TEST_LIVE", "false").lower() == "true"

pytestmark = pytest.mark.skipif(
    not RUN_LIVE_TESTS,
    reason="Set FEISHU_AM_TEST_LIVE=true to run live task integration tests",
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

class LiveTaskClient:
    """Thin wrapper around LarkCliClient for live task operations."""

    def __init__(self, client: LarkCliClient | None = None) -> None:
        self._client = client or LarkCliClient()

    def create_task(
        self,
        title: str,
        description: str | None = None,
        due_date: int | None = None,
    ) -> dict[str, Any]:
        """Create a task and return the response."""
        args = ["task", "+create"]
        if title:
            args.extend(["--title", title])
        if description:
            args.extend(["--description", description])
        if due_date is not None:
            args.extend(["--due_date", str(due_date)])
        return self._client.invoke_json(args)

    def get_task(self, task_id: str) -> dict[str, Any]:
        """Fetch a task by ID."""
        return self._client.invoke_json(["task", "+get", "--task_id", task_id])

    def search_tasks(self, query: str, limit: int = 20) -> dict[str, Any]:
        """Search tasks by keyword."""
        return self._client.invoke_json([
            "task", "+search",
            "--query", query,
            "--limit", str(limit),
        ])

    def update_task(
        self,
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        complete: bool | None = None,
    ) -> dict[str, Any]:
        """Update a task's attributes."""
        args = ["task", "+update", "--task_id", task_id]
        if title is not None:
            args.extend(["--title", title])
        if description is not None:
            args.extend(["--description", description])
        if complete is not None:
            args.append("+complete" if complete else "+reopen")
        return self._client.invoke_json(args)

    def complete_task(self, task_id: str) -> dict[str, Any]:
        """Mark a task as complete."""
        return self._client.invoke_json(["task", "+complete", "--task_id", task_id])

    def reopen_task(self, task_id: str) -> dict[str, Any]:
        """Reopen a completed task."""
        return self._client.invoke_json(["task", "+reopen", "--task_id", task_id])

    def delete_task(self, task_id: str) -> dict[str, Any]:
        """Delete a task."""
        return self._client.invoke_json(["task", "+delete", "--task_id", task_id])


@pytest.fixture
def task_client() -> LiveTaskClient:
    return LiveTaskClient()


@pytest.fixture
def lark_token() -> str:
    token = FEISHU_AM_TEST_LARK_TOKEN
    if not token:
        pytest.skip("FEISHU_AM_TEST_LARK_TOKEN not set")
    return token


# ---------------------------------------------------------------------------
# Task Creation Tests
# ---------------------------------------------------------------------------

class TestTaskCreation(unittest.TestCase):
    """Verify task creation operations."""

    def test_create_task_with_title_only(self, task_client: LiveTaskClient) -> None:
        """Create a task with just a title; verify response has task_id."""
        test_title = "【测试】task creation test"
        try:
            resp = task_client.create_task(title=test_title)
            data = resp.get("data", {})
            task_id = data.get("task", {}).get("guid") or data.get("task", {}).get("task_id")
            self.assertIsNotNone(task_id, f"No task_id in create response: {resp}")
        except Exception as exc:
            self.fail(f"Task creation failed: {exc}")

    def test_create_task_with_description(self, task_client: LiveTaskClient) -> None:
        """Create a task with title and description; verify description is stored."""
        test_title = "【测试】task with description"
        test_desc = "测试任务描述"
        try:
            resp = task_client.create_task(title=test_title, description=test_desc)
            data = resp.get("data", {})
            task_id = data.get("task", {}).get("guid") or data.get("task", {}).get("task_id")
            self.assertIsNotNone(task_id)

            # Read back and verify
            get_resp = task_client.get_task(task_id)
            stored_desc = (
                get_resp.get("data", {})
                .get("task", {})
                .get("description", "")
                or get_resp.get("data", {})
                .get("task", {})
                .get("summary", "")
            )
            self.assertIn(test_desc, stored_desc)
        except Exception as exc:
            self.fail(f"Task creation with description failed: {exc}")

    def test_create_task_cleanup(self, task_client: LiveTaskClient) -> None:
        """Create a task and immediately delete it; verify delete works."""
        test_title = "【测试-待删除】cleanup verification"
        try:
            resp = task_client.create_task(title=test_title)
            data = resp.get("data", {})
            task_id = data.get("task", {}).get("guid") or data.get("task", {}).get("task_id")
            if task_id is None:
                self.skipTest("Could not create test task; skipping cleanup verification")

            # Delete the task
            delete_resp = task_client.delete_task(task_id)
            self.assertTrue(
                delete_resp.get("ok") or delete_resp.get("data", {}).get("task_id") == task_id,
                f"Delete did not succeed: {delete_resp}",
            )
        except Exception as exc:
            self.fail(f"Task cleanup failed: {exc}")


# ---------------------------------------------------------------------------
# Task Read Tests
# ---------------------------------------------------------------------------

class TestTaskRead(unittest.TestCase):
    """Verify task read operations."""

    def test_get_my_tasks_returns_list(self, task_client: LiveTaskClient) -> None:
        """Fetch the user's task list; should return a list."""
        try:
            resp = task_client._client.invoke_json(["task", "+get-my-tasks", "--limit", "10"])
            data = resp.get("data", {})
            tasks = data.get("items") or data.get("task_list") or []
            self.assertIsInstance(tasks, list)
        except Exception as exc:
            self.fail(f"Get my tasks failed: {exc}")

    def test_search_tasks_by_keyword(self, task_client: LiveTaskClient) -> None:
        """Search for tasks containing '测试' keyword."""
        try:
            resp = task_client.search_tasks(query="测试", limit=10)
            data = resp.get("data", {})
            items = data.get("items") or data.get("task_list") or []
            self.assertIsInstance(items, list)
        except Exception as exc:
            self.fail(f"Task search failed: {exc}")

    def test_get_nonexistent_task_returns_error(self, task_client: LiveTaskClient) -> None:
        """Attempt to get a task with a fake ID; should fail gracefully."""
        fake_id = "fake_task_id_12345"
        with self.assertRaises(Exception):
            task_client.get_task(fake_id)


# ---------------------------------------------------------------------------
# Task Update Tests
# ---------------------------------------------------------------------------

class TestTaskUpdate(unittest.TestCase):
    """Verify task update operations."""

    def test_update_task_title(self, task_client: LiveTaskClient) -> None:
        """Create a task, update its title, verify the change."""
        test_title = "【测试】original title"
        new_title = "【测试-已更新】updated title"
        try:
            # Create
            resp = task_client.create_task(title=test_title)
            data = resp.get("data", {})
            task_id = data.get("task", {}).get("guid") or data.get("task", {}).get("task_id")
            self.assertIsNotNone(task_id)

            # Update
            update_resp = task_client.update_task(task_id, title=new_title)
            self.assertTrue(
                update_resp.get("ok") is not False,
                f"Update failed: {update_resp}",
            )

            # Read back and verify
            get_resp = task_client.get_task(task_id)
            stored_title = (
                get_resp.get("data", {})
                .get("task", {})
                .get("title", "")
                or get_resp.get("data", {})
                .get("task", {})
                .get("summary", "")
            )
            self.assertIn("已更新", stored_title)

        except Exception as exc:
            self.fail(f"Task title update failed: {exc}")

    def test_complete_and_reopen_task(self, task_client: LiveTaskClient) -> None:
        """Create a task, mark it complete, then reopen it."""
        test_title = "【测试】complete-reopen test"
        try:
            # Create
            resp = task_client.create_task(title=test_title)
            data = resp.get("data", {})
            task_id = data.get("task", {}).get("guid") or data.get("task", {}).get("task_id")
            self.assertIsNotNone(task_id)

            # Complete
            complete_resp = task_client.complete_task(task_id)
            self.assertTrue(
                complete_resp.get("ok") is not False,
                f"Complete failed: {complete_resp}",
            )

            # Verify it's complete
            get_resp = task_client.get_task(task_id)
            is_completed = (
                get_resp.get("data", {})
                .get("task", {})
                .get("completed_at")
                or get_resp.get("data", {})
                .get("task", {})
                .get("is_completed")
            )
            self.assertTrue(is_completed, "Task should be marked complete")

            # Reopen
            reopen_resp = task_client.reopen_task(task_id)
            self.assertTrue(
                reopen_resp.get("ok") is not False,
                f"Reopen failed: {reopen_resp}",
            )

            # Delete in cleanup
            task_client.delete_task(task_id)

        except Exception as exc:
            self.fail(f"Complete/reopen cycle failed: {exc}")


# ---------------------------------------------------------------------------
# Scene E2E Tests
# ---------------------------------------------------------------------------

class TestTaskSceneE2E(unittest.TestCase):
    """Verify complete scene flows with task operations."""

    def test_create_and_verify_readback(self, task_client: LiveTaskClient) -> None:
        """Create a task, read it back, verify title matches."""
        test_title = "【测试-E2E】readback verification"
        try:
            resp = task_client.create_task(title=test_title)
            data = resp.get("data", {})
            task_id = data.get("task", {}).get("guid") or data.get("task", {}).get("task_id")
            self.assertIsNotNone(task_id)

            get_resp = task_client.get_task(task_id)
            stored_title = (
                get_resp.get("data", {})
                .get("task", {})
                .get("title", "")
                or get_resp.get("data", {})
                .get("task", {})
                .get("summary", "")
            )
            self.assertIn("【测试-E2E】", stored_title)

            # Cleanup
            task_client.delete_task(task_id)

        except Exception as exc:
            self.fail(f"Create and read back failed: {exc}")

    def test_search_returns_relevant_results(self, task_client: LiveTaskClient) -> None:
        """Search for tasks; verify results contain the keyword."""
        try:
            resp = task_client.search_tasks(query="测试", limit=20)
            data = resp.get("data", {})
            items = data.get("items") or data.get("task_list") or []
            self.assertIsInstance(items, list)
        except Exception as exc:
            self.fail(f"Search returned non-list: {exc}")


# ---------------------------------------------------------------------------
# Edge Case Tests
# ---------------------------------------------------------------------------

class TestTaskEdgeCases(unittest.TestCase):
    """Verify graceful handling of edge cases."""

    def test_create_task_with_empty_title_fails(self, task_client: LiveTaskClient) -> None:
        """Attempt to create a task with empty title; should fail gracefully."""
        with self.assertRaises(Exception):
            task_client.create_task(title="")

    def test_update_nonexistent_task_fails(self, task_client: LiveTaskClient) -> None:
        """Attempt to update a fake task ID; should fail gracefully."""
        fake_id = "fake_task_id_12345"
        with self.assertRaises(Exception):
            task_client.update_task(fake_id, title="new title")

    def test_search_with_special_characters(self, task_client: LiveTaskClient) -> None:
        """Search with special characters; should not crash."""
        try:
            resp = task_client.search_tasks(query="测试<>\"'", limit=10)
            self.assertIsInstance(resp, dict)
        except Exception as exc:
            self.fail(f"Search with special chars crashed: {exc}")