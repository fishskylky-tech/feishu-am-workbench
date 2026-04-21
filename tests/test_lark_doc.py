"""Live Feishu Doc integration tests.

These tests make real API calls against the actual Feishu Doc API.
They are SKIPPED by default; set FEISHU_AM_TEST_LIVE=true to run them.
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

# Test folder tokens from plan
CUSTOMER_ARCHIVE_FOLDER = os.environ.get(
    "FEISHU_AM_TEST_CUSTOMER_ARCHIVE_FOLDER",
    "P2ZgfnJwYlb8FBdis1dcxxKen0f",
)
MEETING_NOTES_FOLDER = os.environ.get(
    "FEISHU_AM_TEST_MEETING_NOTES_FOLDER",
    "QJ4rf3h2ZlQBuKdIs3FcAvexnim",  # pragma: allowlist secret
)

pytestmark = pytest.mark.skipif(
    not RUN_LIVE_TESTS,
    reason="Set FEISHU_AM_TEST_LIVE=true to run live doc integration tests",
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

class LiveDocClient:
    """Thin wrapper around LarkCliClient for live doc operations."""

    def __init__(self, client: LarkCliClient | None = None) -> None:
        self._client = client or LarkCliClient()

    def create_doc(
        self,
        title: str,
        content: str | None = None,
        folder_token: str | None = None,
    ) -> dict[str, Any]:
        """Create a Lark document and return the response."""
        args = ["docs", "+create", "--title", title]
        if folder_token:
            args.extend(["--folder-token", folder_token])
        if content:
            args.extend(["--markdown", content])
        return self._client.invoke_json(args)

    def fetch_doc(self, doc_token: str) -> dict[str, Any]:
        """Fetch document content by token."""
        return self._client.invoke_json(["docs", "+fetch", "--doc_token", doc_token])

    def search_docs(self, query: str, limit: int = 20) -> dict[str, Any]:
        """Search for documents by keyword."""
        return self._client.invoke_json([
            "docs", "+search",
            "--query", query,
            "--limit", str(limit),
        ])

    def list_folder_docs(self, folder_token: str, limit: int = 20) -> dict[str, Any]:
        """List documents in a folder."""
        return self._client.invoke_json([
            "drive", "files", "list",
            "--params",
            '{"folder_token":"' + folder_token + '","order_by":"EditedTime","direction":"DESC","page_size":' + str(limit) + "}",
        ])


@pytest.fixture
def doc_client() -> LiveDocClient:
    return LiveDocClient()


@pytest.fixture
def lark_token() -> str:
    token = FEISHU_AM_TEST_LARK_TOKEN
    if not token:
        pytest.skip("FEISHU_AM_TEST_LARK_TOKEN not set")
    return token


# ---------------------------------------------------------------------------
# Doc Creation Tests
# ---------------------------------------------------------------------------

class TestDocCreation(unittest.TestCase):
    """Verify document creation operations."""

    def test_create_doc_with_title_only(self, doc_client: LiveDocClient) -> None:
        """Create a document with just a title; verify response has doc_token."""
        test_title = "【测试】doc creation test"
        try:
            resp = doc_client.create_doc(title=test_title)
            data = resp.get("data", {})
            doc_token = (
                data.get("doc", {}).get("token")
                or data.get("token")
                or data.get("document", {}).get("token")
            )
            self.assertIsNotNone(doc_token, f"No doc_token in create response: {resp}")
        except Exception as exc:
            self.fail(f"Doc creation failed: {exc}")

    def test_create_doc_in_folder(self, doc_client: LiveDocClient) -> None:
        """Create a document inside the customer archive folder."""
        test_title = "【测试】doc in folder test"
        try:
            resp = doc_client.create_doc(
                title=test_title,
                folder_token=CUSTOMER_ARCHIVE_FOLDER,
            )
            data = resp.get("data", {})
            doc_token = (
                data.get("doc", {}).get("token")
                or data.get("token")
                or data.get("document", {}).get("token")
            )
            self.assertIsNotNone(doc_token)
        except Exception as exc:
            self.fail(f"Doc creation in folder failed: {exc}")

    def test_create_doc_with_markdown_content(self, doc_client: LiveDocClient) -> None:
        """Create a document with markdown content; verify content is stored."""
        test_title = "【测试】doc with content"
        test_content = "# Test Header\n\nThis is a test paragraph."
        try:
            resp = doc_client.create_doc(
                title=test_title,
                content=test_content,
            )
            data = resp.get("data", {})
            doc_token = (
                data.get("doc", {}).get("token")
                or data.get("token")
                or data.get("document", {}).get("token")
            )
            self.assertIsNotNone(doc_token)

            # Fetch and verify content
            fetch_resp = doc_client.fetch_doc(doc_token)
            content = fetch_resp.get("data", {}).get("content", "") or fetch_resp.get("data", {}).get("text", "")
            # Content should contain our header
            self.assertTrue(
                "Test Header" in content or "test" in content.lower(),
                f"Fetched content missing expected text. Got: {content[:200]}",
            )
        except Exception as exc:
            self.fail(f"Doc creation with content failed: {exc}")


# ---------------------------------------------------------------------------
# Doc Read Tests
# ---------------------------------------------------------------------------

class TestDocRead(unittest.TestCase):
    """Verify document read operations."""

    def test_fetch_doc_returns_content(self, doc_client: LiveDocClient) -> None:
        """Fetch an existing document; verify it returns content."""
        # First create a doc to fetch
        test_title = "【测试】fetch test doc"
        try:
            create_resp = doc_client.create_doc(title=test_title)
            data = create_resp.get("data", {})
            doc_token = (
                data.get("doc", {}).get("token")
                or data.get("token")
                or data.get("document", {}).get("token")
            )
            self.assertIsNotNone(doc_token)

            # Now fetch it
            fetch_resp = doc_client.fetch_doc(doc_token)
            self.assertIsInstance(fetch_resp, dict)
            self.assertIn("data", fetch_resp)

        except Exception as exc:
            self.fail(f"Fetch doc failed: {exc}")

    def test_list_customer_archive_folder(self, doc_client: LiveDocClient) -> None:
        """List documents in the customer archive folder."""
        try:
            resp = doc_client.list_folder_docs(CUSTOMER_ARCHIVE_FOLDER, limit=10)
            data = resp.get("data", {})
            files = data.get("items") or data.get("files") or []
            self.assertIsInstance(files, list)
        except Exception as exc:
            self.fail(f"List customer archive folder failed: {exc}")

    def test_list_meeting_notes_folder(self, doc_client: LiveDocClient) -> None:
        """List documents in the meeting notes folder."""
        try:
            resp = doc_client.list_folder_docs(MEETING_NOTES_FOLDER, limit=10)
            data = resp.get("data", {})
            files = data.get("items") or data.get("files") or []
            self.assertIsInstance(files, list)
        except Exception as exc:
            self.fail(f"List meeting notes folder failed: {exc}")


# ---------------------------------------------------------------------------
# Doc Search Tests
# ---------------------------------------------------------------------------

class TestDocSearch(unittest.TestCase):
    """Verify document search operations."""

    def test_search_docs_by_keyword(self, doc_client: LiveDocClient) -> None:
        """Search for documents containing '测试' keyword."""
        try:
            resp = doc_client.search_docs(query="测试", limit=10)
            data = resp.get("data", {})
            items = data.get("items") or data.get("docs") or []
            self.assertIsInstance(items, list)
        except Exception as exc:
            self.fail(f"Doc search failed: {exc}")

    def test_search_returns_empty_for_nonexistent(self, doc_client: LiveDocClient) -> None:
        """Search for a keyword that should not exist; verify graceful handling."""
        try:
            resp = doc_client.search_docs(query="__definitely_nonexistent_doc_xyz123__", limit=10)
            data = resp.get("data", {})
            items = data.get("items") or data.get("docs") or []
            self.assertIsInstance(items, list)
            self.assertEqual(len(items), 0)
        except Exception as exc:
            self.fail(f"Search for nonexistent returned error: {exc}")


# ---------------------------------------------------------------------------
# Scene E2E Tests
# ---------------------------------------------------------------------------

class TestDocSceneE2E(unittest.TestCase):
    """Verify complete scene flows with doc operations."""

    def test_create_doc_and_fetch_content(self, doc_client: LiveDocClient) -> None:
        """Create a doc, fetch its content, verify structure."""
        test_title = "【测试-E2E】doc readback verification"
        try:
            create_resp = doc_client.create_doc(title=test_title)
            data = create_resp.get("data", {})
            doc_token = (
                data.get("doc", {}).get("token")
                or data.get("token")
                or data.get("document", {}).get("token")
            )
            self.assertIsNotNone(doc_token)

            fetch_resp = doc_client.fetch_doc(doc_token)
            content = fetch_resp.get("data", {})
            self.assertIsInstance(content, dict)

        except Exception as exc:
            self.fail(f"Create and fetch E2E failed: {exc}")

    def test_archive_folder_listing_scene(self, doc_client: LiveDocClient) -> None:
        """Verify customer archive folder can be listed (archive refresh scene)."""
        try:
            resp = doc_client.list_folder_docs(CUSTOMER_ARCHIVE_FOLDER, limit=10)
            data = resp.get("data", {})
            files = data.get("items") or data.get("files") or []
            self.assertIsInstance(files, list)
        except Exception as exc:
            self.fail(f"Archive folder listing scene failed: {exc}")


# ---------------------------------------------------------------------------
# Edge Case Tests
# ---------------------------------------------------------------------------

class TestDocEdgeCases(unittest.TestCase):
    """Verify graceful handling of edge cases."""

    def test_fetch_nonexistent_doc_fails(self, doc_client: LiveDocClient) -> None:
        """Attempt to fetch a fake document token; should fail gracefully."""
        fake_token = "fake_doc_token_12345"
        with self.assertRaises(Exception):
            doc_client.fetch_doc(fake_token)

    def test_create_doc_with_empty_title_fails(self, doc_client: LiveDocClient) -> None:
        """Attempt to create a document with empty title; should fail gracefully."""
        with self.assertRaises(Exception):
            doc_client.create_doc(title="")

    def test_search_with_special_characters(self, doc_client: LiveDocClient) -> None:
        """Search with special characters; should not crash."""
        try:
            resp = doc_client.search_docs(query="测试<>\"'", limit=10)
            self.assertIsInstance(resp, dict)
        except Exception as exc:
            self.fail(f"Search with special chars crashed: {exc}")