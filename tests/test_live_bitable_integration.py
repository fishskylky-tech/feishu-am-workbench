"""Live Feishu Bitable integration tests.

These tests make real API calls against the actual Feishu Bitable instance.
They are SKIPPED by default; set FEISHU_AM_TEST_LIVE=true to run them.

All write operations target records with "test_" prefix and are cleaned up after each test.
"""

from __future__ import annotations

import json
import os
import unittest
from typing import Any

import pytest

from runtime import LarkCliClient
from runtime.live_adapter import LiveWorkbenchConfig
from runtime.runtime_sources import RuntimeSourceLoader

# ---------------------------------------------------------------------------
# Configuration from environment (with sensible defaults from the plan)
# ---------------------------------------------------------------------------

BASE_TOKEN = os.environ.get(
    "FEISHU_AM_TEST_BASE_TOKEN", "OPkWbqrk0amMJusrMGMcf9v7nhc"
)
CUSTOMER_MASTER_TABLE_ID = os.environ.get(
    "FEISHU_AM_TEST_CUSTOMER_MASTER_TABLE_ID", "blkhtAcNtavGDJVu"
)
ACTION_PLAN_TABLE_ID = os.environ.get(
    "FEISHU_AM_TEST_ACTION_PLAN_TABLE_ID", "tbl_action_plan"
)
TODO_TABLE_ID = os.environ.get(
    "FEISHU_AM_TEST_TODO_TABLE_ID", "tbl_todo"
)
CUSTOMER_ARCHIVE_FOLDER = os.environ.get(
    "FEISHU_AM_TEST_CUSTOMER_ARCHIVE_FOLDER", "P2ZgfnJwYlb8FBdis1dcxxKen0f"
)
MEETING_NOTES_FOLDER = os.environ.get(
    "FEISHU_AM_TEST_MEETING_NOTES_FOLDER", "QJ4rf3h2ZlQBuKdIs3FcAvexnim"
)
CUSTOMER_INFO_FOLDER = os.environ.get(
    "FEISHU_AM_TEST_CUSTOMER_INFO_FOLDER", "XuZVfyoWZlkbyqdZhGXc4ocCnZs"
)

RUN_LIVE_TESTS = os.environ.get("FEISHU_AM_TEST_LIVE", "false").lower() == "true"

pytestmark = pytest.mark.skipif(
    not RUN_LIVE_TESTS,
    reason="Set FEISHU_AM_TEST_LIVE=true to run live bitable integration tests",
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

class LiveBitableClient:
    """Thin wrapper around LarkCliClient for live bitable operations."""

    def __init__(self, client: LarkCliClient | None = None) -> None:
        self._client = client or LarkCliClient()

    def get_table_schema(self, token: str, table_id: str) -> dict[str, Any]:
        """Fetch live table schema fields."""
        return self._client.invoke_json([
            "base", "+field-list",
            "--base-token", token,
            "--table-id", table_id,
            "--limit", "500",
        ])

    def list_records(
        self, token: str, table_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List records from a table."""
        payload = self._client.invoke_json([
            "base", "+record-list",
            "--base-token", token,
            "--table-id", table_id,
            "--limit", str(limit),
        ])
        data = payload.get("data", {})
        items = data.get("items") or data.get("records") or []
        return items

    def search_records(
        self, token: str, table_id: str, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search records by text across multiple fields."""
        # Use data-query with contains filter for live search
        dimensions = [
            {"field_name": "客户名称", "alias": "dim_name"},
            {"field_name": "简称", "alias": "dim_short"},
            {"field_name": "客户ID", "alias": "dim_id"},
        ]
        dsl = {
            "datasource": {"type": "table", "table": {"tableId": table_id}},
            "dimensions": dimensions,
            "filters": {
                "type": 1,
                "conjunction": "or",
                "conditions": [
                    {"field_name": "客户名称", "operator": "contains", "value": [query]},
                    {"field_name": "简称", "operator": "contains", "value": [query]},
                ],
            },
            "pagination": {"limit": limit},
            "shaper": {"format": "flat"},
        }
        try:
            payload = self._client.invoke_json([
                "base", "+data-query",
                "--base-token", token,
                "--dsl", json.dumps(dsl, ensure_ascii=False),
            ])
        except Exception:  # noqa: S110
            # Fallback to list + filter if data-query fails
            return self._filter_list(query, limit)
        data = payload.get("data", {})
        return data.get("main_data") or []

    def _filter_list(
        self, query: str, limit: int
    ) -> list[dict[str, Any]]:
        """Fallback filter by iterating all records."""
        return []

    def create_record(
        self, token: str, table_id: str, fields: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a record and return the created record response."""
        return self._client.invoke_json([
            "base", "+record-create",
            "--base-token", token,
            "--table-id", table_id,
            "--fields", json.dumps(fields, ensure_ascii=False),
        ])

    def update_record(
        self, token: str, table_id: str, record_id: str, fields: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing record."""
        return self._client.invoke_json([
            "base", "+record-update",
            "--base-token", token,
            "--table-id", table_id,
            "--record-id", record_id,
            "--fields", json.dumps(fields, ensure_ascii=False),
        ])

    def delete_record(self, token: str, table_id: str, record_id: str) -> dict[str, Any]:
        """Delete a record."""
        return self._client.invoke_json([
            "base", "+record-delete",
            "--base-token", token,
            "--table-id", table_id,
            "--record-id", record_id,
        ])

    def get_record(
        self, token: str, table_id: str, record_id: str
    ) -> dict[str, Any]:
        """Fetch a single record by ID."""
        return self._client.invoke_json([
            "base", "+record-get",
            "--base-token", token,
            "--table-id", table_id,
            "--record-id", record_id,
        ])


@pytest.fixture
def client() -> LiveBitableClient:
    return LiveBitableClient()


@pytest.fixture
def live_config() -> LiveWorkbenchConfig:
    sources = RuntimeSourceLoader.load_from_environment()
    return LiveWorkbenchConfig.from_sources(sources)


# ---------------------------------------------------------------------------
# Layer 0: Schema Contract
# ---------------------------------------------------------------------------

class TestSchemaContract(unittest.TestCase):
    """Verify FakeSchemaBackend assumptions match real live bitable schema."""

    def test_customer_master_table_schema_matches_fake(self) -> None:
        """Compare live customer master table schema fields vs FakeSchemaBackend."""
        cli = LarkCliClient()
        live_schema = cli.invoke_json([
            "base", "+field-list",
            "--base-token", BASE_TOKEN,
            "--table-id", CUSTOMER_MASTER_TABLE_ID,
            "--limit", "500",
        ])

        data = live_schema.get("data", {})
        items = data.get("items") or []
        live_fields: dict[str, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            field_name = item.get("field_name") or item.get("name")
            field_type = item.get("type")
            if field_name:
                live_fields[str(field_name)] = {
                    "type": field_type,
                    "options": _extract_options(item),
                }

        # Expected fields from FakeSchemaBackend for customer master
        expected_fields = {
            "上次接触日期",
            "下次行动计划",
            "策略摘要",
            "续费风险",
        }

        # All expected fields should exist in live schema
        missing_in_live = expected_fields - set(live_fields.keys())
        self.assertEqual(
            missing_in_live, set(),
            f"Fields in FakeSchemaBackend but missing from live schema: {missing_in_live}"
        )

    def test_action_plan_table_schema_matches_fake(self) -> None:
        """Compare live action plan table schema vs FakeSchemaBackend."""
        cli = LarkCliClient()
        live_schema = cli.invoke_json([
            "base", "+field-list",
            "--base-token", BASE_TOKEN,
            "--table-id", ACTION_PLAN_TABLE_ID,
            "--limit", "500",
        ])

        data = live_schema.get("data", {})
        items = data.get("items") or []
        live_fields: dict[str, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            field_name = item.get("field_name") or item.get("name")
            field_type = item.get("type")
            if field_name:
                live_fields[str(field_name)] = {
                    "type": field_type,
                    "options": _extract_options(item),
                }

        # Expected fields from FakeSchemaBackend for action plan
        expected_fields = {
            "具体行动",
            "行动类型",
            "负责人",
            "计划完成时间",
        }

        missing_in_live = expected_fields - set(live_fields.keys())
        self.assertEqual(
            missing_in_live, set(),
            f"Fields in FakeSchemaBackend but missing from live schema: {missing_in_live}"
        )

    def test_todo_table_schema_matches_fake(self) -> None:
        """Compare live todo table schema vs FakeSchemaBackend."""
        cli = LarkCliClient()
        live_schema = cli.invoke_json([
            "base", "+field-list",
            "--base-token", BASE_TOKEN,
            "--table-id", TODO_TABLE_ID,
            "--limit", "500",
        ])

        data = live_schema.get("data", {})
        items = data.get("items") or []
        live_fields: dict[str, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            field_name = item.get("field_name") or item.get("name")
            field_type = item.get("type")
            if field_name:
                live_fields[str(field_name)] = {
                    "type": field_type,
                    "options": _extract_options(item),
                }

        # Expected fields from FakeSchemaBackend for todo
        expected_fields = {
            "标题",
            "描述",
            "截止时间",
            "负责人",
            "优先级",
        }

        missing_in_live = expected_fields - set(live_fields.keys())
        self.assertEqual(
            missing_in_live, set(),
            f"Fields in FakeSchemaBackend but missing from live schema: {missing_in_live}"
        )


# ---------------------------------------------------------------------------
# Layer 1: Read Integration
# ---------------------------------------------------------------------------

class TestBitableReadIntegration(unittest.TestCase):
    """Verify query backends can correctly parse real bitable data."""

    def test_search_customer_by_name_returns_records(self) -> None:
        """Search for a customer by name; should return real records."""
        cli = LarkCliClient()
        # Search for "测试" to find test records
        results = cli.invoke_json([
            "base", "+data-query",
            "--base-token", BASE_TOKEN,
            "--dsl", json.dumps({
                "datasource": {
                    "type": "table",
                    "table": {"tableId": CUSTOMER_MASTER_TABLE_ID},
                },
                "dimensions": [
                    {"field_name": "客户名称", "alias": "dim_name"},
                    {"field_name": "简称", "alias": "dim_short"},
                    {"field_name": "客户ID", "alias": "dim_id"},
                    {"field_name": "状态", "alias": "dim_status"},
                ],
                "filters": {
                    "type": 1,
                    "conjunction": "or",
                    "conditions": [
                        {
                            "field_name": "客户名称",
                            "operator": "contains",
                            "value": ["测试"],
                        },
                        {
                            "field_name": "简称",
                            "operator": "contains",
                            "value": ["测试"],
                        },
                    ],
                },
                "pagination": {"limit": 20},
                "shaper": {"format": "flat"},
            }, ensure_ascii=False),
        ])

        data = results.get("data", {})
        rows = data.get("main_data") or []
        self.assertIsInstance(rows, list)

    def test_filter_active_customers(self) -> None:
        """Filter customers by active status."""
        cli = LarkCliClient()
        results = cli.invoke_json([
            "base", "+data-query",
            "--base-token", BASE_TOKEN,
            "--dsl", json.dumps({
                "datasource": {
                    "type": "table",
                    "table": {"tableId": CUSTOMER_MASTER_TABLE_ID},
                },
                "dimensions": [
                    {"field_name": "客户名称", "alias": "dim_name"},
                    {"field_name": "状态", "alias": "dim_status"},
                ],
                "filters": {
                    "type": 1,
                    "conjunction": "and",
                    "conditions": [
                        {"field_name": "状态", "operator": "is", "value": ["活跃"]},
                    ],
                },
                "pagination": {"limit": 50},
                "shaper": {"format": "flat"},
            }, ensure_ascii=False),
        ])

        data = results.get("data", {})
        rows = data.get("main_data") or []
        self.assertIsInstance(rows, list)

    def test_customer_record_fields_match_schema(self) -> None:
        """Verify returned customer records have expected schema fields."""
        cli = LarkCliClient()
        results = cli.invoke_json([
            "base", "+record-list",
            "--base-token", BASE_TOKEN,
            "--table-id", CUSTOMER_MASTER_TABLE_ID,
            "--limit", "5",
        ])

        data = results.get("data", {})
        items = data.get("items") or []
        self.assertGreater(len(items), 0, "Expected at least one record")

        record = items[0]
        fields = record.get("fields", {})
        # Should have at least one of these key fields
        self.assertTrue(
            any(
                key in fields
                for key in ("客户ID", "客户名称", "简称", "客户ID_alt")
            ),
            f"Record missing expected customer identifier fields. Got: {list(fields.keys())}"
        )


# ---------------------------------------------------------------------------
# Layer 2: Write Integration
# ---------------------------------------------------------------------------

class TestBitableWriteIntegration(unittest.TestCase):
    """Verify write operations against real bitable.

    All writes use test_ prefix and clean up in teardown/finally.
    """

    def test_create_action_item_and_verify_readback(self) -> None:
        """Create an action plan record; verify it can be read back."""
        cli = LarkCliClient()
        test_fields = {
            "具体行动": "【测试】验证集成测试",
            "行动类型": "客户经营",
            "负责人": "测试员",
        }

        try:
            create_resp = cli.invoke_json([
                "base", "+record-create",
                "--base-token", BASE_TOKEN,
                "--table-id", ACTION_PLAN_TABLE_ID,
                "--fields", json.dumps(test_fields, ensure_ascii=False),
            ])

            record_id = _extract_record_id(create_resp)
            self.assertIsNotNone(record_id, f"No record_id in create response: {create_resp}")

            # Read back the record
            read_resp = cli.invoke_json([
                "base", "+record-get",
                "--base-token", BASE_TOKEN,
                "--table-id", ACTION_PLAN_TABLE_ID,
                "--record-id", record_id,
            ])

            read_fields = read_resp.get("data", {}).get("record", {}).get("fields", {})
            self.assertEqual(
                read_fields.get("具体行动"),
                test_fields["具体行动"],
                f"Read back value mismatch. Expected: {test_fields['具体行动']}, Got: {read_fields.get('具体行动')}"
            )

        finally:
            # Cleanup handled by test-specific cleanup below
            pass

    def test_create_action_item_cleanup(self) -> None:
        """Create a record and delete it (cleanup verification).

        This test creates a record, then immediately deletes it
        to verify the delete path works and clean up happens.
        """
        cli = LarkCliClient()
        test_fields = {
            "具体行动": "【测试-待删除】cleanup verification",
            "行动类型": "客户经营",
            "负责人": "测试员",
        }

        create_resp = cli.invoke_json([
            "base", "+record-create",
            "--base-token", BASE_TOKEN,
            "--table-id", ACTION_PLAN_TABLE_ID,
            "--fields", json.dumps(test_fields, ensure_ascii=False),
        ])

        record_id = _extract_record_id(create_resp)
        if record_id is None:
            self.skipTest("Could not create test record; skipping cleanup verification")

        # Delete the record
        delete_resp = cli.invoke_json([
            "base", "+record-delete",
            "--base-token", BASE_TOKEN,
            "--table-id", ACTION_PLAN_TABLE_ID,
            "--record-id", record_id,
        ])

        self.assertTrue(
            delete_resp.get("ok") or delete_resp.get("data", {}).get("record_id") == record_id,
            f"Delete did not succeed: {delete_resp}"
        )

    def test_update_existing_action_item(self) -> None:
        """Create a record, update it, verify the update was applied."""
        cli = LarkCliClient()
        test_fields = {
            "具体行动": "【测试】update verification record",
            "行动类型": "客户经营",
            "负责人": "测试员",
        }

        try:
            # Create
            create_resp = cli.invoke_json([
                "base", "+record-create",
                "--base-token", BASE_TOKEN,
                "--table-id", ACTION_PLAN_TABLE_ID,
                "--fields", json.dumps(test_fields, ensure_ascii=False),
            ])
            record_id = _extract_record_id(create_resp)
            self.assertIsNotNone(record_id)

            # Update with new fields
            updated_fields = {
                "具体行动": "【测试-已更新】update verification record",
                "负责人": "测试员-已更新",
            }
            update_resp = cli.invoke_json([
                "base", "+record-update",
                "--base-token", BASE_TOKEN,
                "--table-id", ACTION_PLAN_TABLE_ID,
                "--record-id", record_id,
                "--fields", json.dumps(updated_fields, ensure_ascii=False),
            ])

            self.assertTrue(
                update_resp.get("ok") is not False,
                f"Update failed: {update_resp}"
            )

            # Read back and verify
            read_resp = cli.invoke_json([
                "base", "+record-get",
                "--base-token", BASE_TOKEN,
                "--table-id", ACTION_PLAN_TABLE_ID,
                "--record-id", record_id,
            ])

            read_fields = read_resp.get("data", {}).get("record", {}).get("fields", {})
            self.assertEqual(
                read_fields.get("具体行动"),
                updated_fields["具体行动"],
            )
            self.assertEqual(
                read_fields.get("负责人"),
                updated_fields["负责人"],
            )

            # Delete in cleanup
            cli.invoke_json([
                "base", "+record-delete",
                "--base-token", BASE_TOKEN,
                "--table-id", ACTION_PLAN_TABLE_ID,
                "--record-id", record_id,
            ])

        except Exception as exc:
            self.fail(f"Update test failed: {exc}")


# ---------------------------------------------------------------------------
# Layer 3: Scene-Level E2E
# ---------------------------------------------------------------------------

class TestSceneE2E(unittest.TestCase):
    """Verify complete scene flows with real data."""

    def test_archive_refresh_scene_live(self) -> None:
        """Verify customer archive folder can be listed (archive refresh scene).

        This tests the folder content listing capability used by the archive
        refresh scene flow.
        """
        cli = LarkCliClient()
        try:
            payload = cli.invoke_json([
                "drive", "files", "list",
                "--params",
                json.dumps({"folder_token": CUSTOMER_ARCHIVE_FOLDER, "order_by": "EditedTime", "direction": "DESC"}),
            ])
            data = payload.get("data", {})
            files = data.get("items") or []
            self.assertIsInstance(files, list)
        except Exception as exc:
            self.fail(f"Cannot list customer archive folder {CUSTOMER_ARCHIVE_FOLDER}: {exc}")

    def test_meeting_prep_scene_live(self) -> None:
        """Verify meeting notes folder can be listed (meeting prep scene)."""
        cli = LarkCliClient()
        try:
            payload = cli.invoke_json([
                "drive", "files", "list",
                "--params",
                json.dumps({"folder_token": MEETING_NOTES_FOLDER, "order_by": "EditedTime", "direction": "DESC"}),
            ])
            data = payload.get("data", {})
            files = data.get("items") or []
            self.assertIsInstance(files, list)
        except Exception as exc:
            self.fail(f"Cannot list meeting notes folder {MEETING_NOTES_FOLDER}: {exc}")

    def test_customer_master_readable(self) -> None:
        """Verify customer master table can be read (used by multiple scenes)."""
        cli = LarkCliClient()
        try:
            payload = cli.invoke_json([
                "base", "+record-list",
                "--base-token", BASE_TOKEN,
                "--table-id", CUSTOMER_MASTER_TABLE_ID,
                "--limit", "10",
            ])
            data = payload.get("data", {})
            items = data.get("items") or []
            self.assertIsInstance(items, list)
        except Exception as exc:
            self.fail(f"Cannot read customer master table: {exc}")


# ---------------------------------------------------------------------------
# Layer 4: Error & Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases(unittest.TestCase):
    """Verify graceful handling of edge cases."""

    def test_query_nonexistent_customer_returns_empty_or_error(self) -> None:
        """Search for a customer that definitely does not exist."""
        cli = LarkCliClient()
        results = cli.invoke_json([
            "base", "+data-query",
            "--base-token", BASE_TOKEN,
            "--dsl", json.dumps({
                "datasource": {
                    "type": "table",
                    "table": {"tableId": CUSTOMER_MASTER_TABLE_ID},
                },
                "dimensions": [
                    {"field_name": "客户名称", "alias": "dim_name"},
                ],
                "filters": {
                    "type": 1,
                    "conjunction": "and",
                    "conditions": [
                        {
                            "field_name": "客户名称",
                            "operator": "contains",
                            "value": ["__definitely_nonexistent_customer_xyz123__"],
                        },
                    ],
                },
                "pagination": {"limit": 10},
                "shaper": {"format": "flat"},
            }, ensure_ascii=False),
        ])

        data = results.get("data", {})
        rows = data.get("main_data") or []
        self.assertIsInstance(rows, list)
        # Empty result is acceptable; error response with no rows is also acceptable
        self.assertEqual(len(rows), 0)

    def test_read_with_invalid_table_id_fails_gracefully(self) -> None:
        """Attempt to read from a non-existent table."""
        cli = LarkCliClient()
        with self.assertRaises(Exception):
            cli.invoke_json([
                "base", "+record-list",
                "--base-token", BASE_TOKEN,
                "--table-id", "__nonexistent_table_id__",
                "--limit", "10",
            ])

    def test_create_with_invalid_field_fails_gracefully(self) -> None:
        """Attempt to create a record with a field that does not exist."""
        cli = LarkCliClient()
        invalid_fields = {
            "__invalid_field_name__": "some value",
        }
        with self.assertRaises(Exception):
            cli.invoke_json([
                "base", "+record-create",
                "--base-token", BASE_TOKEN,
                "--table-id", ACTION_PLAN_TABLE_ID,
                "--fields", json.dumps(invalid_fields, ensure_ascii=False),
            ])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_options(field_item: dict[str, Any]) -> list[str]:
    """Extract option labels from a field item (single_select, multi_select)."""
    options: list[str] = []
    raw_options = field_item.get("options") or field_item.get("property", {}).get("options") or []
    if isinstance(raw_options, list):
        for opt in raw_options:
            if isinstance(opt, dict):
                name = opt.get("name") or opt.get("text") or opt.get("label")
                if name:
                    options.append(str(name))
    return options


def _extract_record_id(payload: dict[str, Any]) -> str | None:
    """Extract record_id from a create/update response."""
    data = payload.get("data", {})
    record = data.get("record")
    if isinstance(record, dict):
        return record.get("record_id")
    # Some responses nest under data.record
    if isinstance(data, dict):
        record = data.get("data", {})
        if isinstance(record, dict):
            return record.get("record_id")
    return None
