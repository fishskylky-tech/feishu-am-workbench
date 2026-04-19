"""Tests for safe Base record operations.

Per references/lark-base-operations-guide.md:
- Verify record_id and business field distinction
- Verify parallel array handling (record_id_list and data)
- Verify pre-modification checks
- Verify post-modification verification
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import Mock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runtime import (  # noqa: E402
    LarkCliClient,
    LarkCliCommandError,
    LarkCliCustomerBackend,
    LiveWorkbenchConfig,
)


class TestRecordIdVsBusinessFields(unittest.TestCase):
    """Test that record_id and business fields are properly distinguished."""

    def setUp(self):
        self.mock_client = Mock(spec=LarkCliClient)
        self.config = LiveWorkbenchConfig(
            base_token="test_token",
            table_targets={"客户联系记录": "tbl_contact_log"},
        )
        self.backend = LarkCliCustomerBackend(self.mock_client, self.config)

    def test_list_records_with_ids_matrix_format(self):
        """Test extracting record_ids from matrix format response."""
        # Simulate +record-list response with parallel arrays
        mock_response = {
            "ok": True,
            "data": {
                "record_id_list": ["recAAA", "recBBB", "recCCC"],
                "fields": ["客户名称", "合同编号", "状态"],
                "data": [
                    ["客户A", "C_20260330_009", "active"],
                    ["客户B", "C_20260330_010", "pending"],
                    ["客户C", "C_20260330_011", "closed"],
                ],
            },
        }
        self.mock_client.invoke_json.return_value = mock_response

        records = self.backend.list_records_with_ids("tbl_contact_log")

        # Verify parallel array mapping is correct
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["record_id"], "recAAA")
        self.assertEqual(records[0]["fields"]["客户名称"], "客户A")
        self.assertEqual(records[0]["fields"]["合同编号"], "C_20260330_009")
        self.assertEqual(records[0]["fields"]["状态"], "active")

        self.assertEqual(records[1]["record_id"], "recBBB")
        self.assertEqual(records[1]["fields"]["客户名称"], "客户B")
        self.assertEqual(records[1]["fields"]["合同编号"], "C_20260330_010")

        self.assertEqual(records[2]["record_id"], "recCCC")
        self.assertEqual(records[2]["fields"]["客户名称"], "客户C")
        self.assertEqual(records[2]["fields"]["合同编号"], "C_20260330_011")

    def test_find_record_by_field_safe_lookup(self):
        """Test finding record_id by business field value (safe pattern)."""
        mock_response = {
            "ok": True,
            "data": {
                "record_id_list": ["recAAA", "recBBB", "recCCC"],
                "fields": ["客户名称", "合同编号", "状态"],
                "data": [
                    ["客户A", "C_20260330_009", "active"],
                    ["客户B", "C_20260330_010", "pending"],
                    ["客户C", "C_20260330_011", "closed"],
                ],
            },
        }
        self.mock_client.invoke_json.return_value = mock_response

        # Find by contract code (business field)
        record = self.backend.find_record_by_field(
            "tbl_contact_log", "合同编号", "C_20260330_010"
        )

        # Should return the correct record_id for 客户B
        self.assertIsNotNone(record)
        self.assertEqual(record["record_id"], "recBBB")
        self.assertEqual(record["fields"]["客户名称"], "客户B")
        self.assertEqual(record["fields"]["合同编号"], "C_20260330_010")

    def test_find_record_by_field_not_found(self):
        """Test finding non-existent business field value."""
        mock_response = {
            "ok": True,
            "data": {
                "record_id_list": ["recAAA", "recBBB"],
                "fields": ["客户名称", "合同编号"],
                "data": [
                    ["客户A", "C_20260330_009"],
                    ["客户B", "C_20260330_010"],
                ],
            },
        }
        self.mock_client.invoke_json.return_value = mock_response

        # Try to find a contract that doesn't exist
        record = self.backend.find_record_by_field(
            "tbl_contact_log", "合同编号", "C_20260330_999"
        )

        self.assertIsNone(record)

    def test_position_not_inferred_from_business_sequence(self):
        """Test that we don't wrongly infer position from business field sequence.

        This is the anti-pattern from the bug report:
        - Contract C_20260330_009 has sequence 009 but might be at any position
        - We must scan the data array, not use the sequence number as index
        """
        # Contract 009 is actually at position 5, not position 9
        mock_response = {
            "ok": True,
            "data": {
                "record_id_list": [
                    "rec001",
                    "rec002",
                    "rec003",
                    "rec004",
                    "rec005",
                    "recTargetHere",  # position 5
                    "rec007",
                ],
                "fields": ["合同编号", "状态"],
                "data": [
                    ["C_20260330_001", "closed"],
                    ["C_20260330_002", "closed"],
                    ["C_20260330_005", "active"],
                    ["C_20260330_007", "pending"],
                    ["C_20260330_008", "active"],
                    ["C_20260330_009", "active"],  # position 5, not 9!
                    ["C_20260330_010", "pending"],
                ],
            },
        }
        self.mock_client.invoke_json.return_value = mock_response

        # Find C_20260330_009 using safe pattern
        record = self.backend.find_record_by_field(
            "tbl_contact_log", "合同编号", "C_20260330_009"
        )

        # Should find it at position 5, not position 9
        self.assertIsNotNone(record)
        self.assertEqual(record["record_id"], "recTargetHere")
        self.assertEqual(record["fields"]["合同编号"], "C_20260330_009")

        # Wrong approach would have looked at position 9, which doesn't exist
        self.assertEqual(len(mock_response["data"]["data"]), 7)


class TestPreModificationVerification(unittest.TestCase):
    """Test pre-modification verification pattern."""

    def setUp(self):
        self.mock_client = Mock(spec=LarkCliClient)
        self.config = LiveWorkbenchConfig(
            base_token="test_token",
            table_targets={"客户联系记录": "tbl_contact_log"},
        )
        self.backend = LarkCliCustomerBackend(self.mock_client, self.config)

    def test_get_record_by_id(self):
        """Test getting a record by its record_id for verification."""
        mock_response = {
            "ok": True,
            "data": {
                "fields": {
                    "客户名称": "客户B",
                    "合同编号": "C_20260330_010",
                    "状态": "pending",
                }
            },
        }
        self.mock_client.invoke_json.return_value = mock_response

        fields = self.backend.get_record("tbl_contact_log", "recBBB")

        self.assertIsNotNone(fields)
        self.assertEqual(fields["客户名称"], "客户B")
        self.assertEqual(fields["合同编号"], "C_20260330_010")

    def test_verify_record_identity_match(self):
        """Test verifying record identity before update (match case)."""
        mock_response = {
            "ok": True,
            "data": {
                "fields": {
                    "客户名称": "客户B",
                    "合同编号": "C_20260330_010",
                    "状态": "pending",
                }
            },
        }
        self.mock_client.invoke_json.return_value = mock_response

        # Verify this record_id points to the expected contract
        is_match, actual_value = self.backend.verify_record_identity(
            table_id_or_name="tbl_contact_log",
            record_id="recBBB",
            verification_field="合同编号",
            expected_value="C_20260330_010",
        )

        self.assertTrue(is_match)
        self.assertEqual(actual_value, "C_20260330_010")

    def test_verify_record_identity_mismatch(self):
        """Test detecting wrong record_id (mismatch case)."""
        # This simulates the bug: we thought recBBB was for contract 010,
        # but it's actually for contract 009
        mock_response = {
            "ok": True,
            "data": {
                "fields": {
                    "客户名称": "客户A",
                    "合同编号": "C_20260330_009",  # Wrong contract!
                    "状态": "active",
                }
            },
        }
        self.mock_client.invoke_json.return_value = mock_response

        # Try to verify, expecting contract 010
        is_match, actual_value = self.backend.verify_record_identity(
            table_id_or_name="tbl_contact_log",
            record_id="recBBB",
            verification_field="合同编号",
            expected_value="C_20260330_010",
        )

        # Should detect the mismatch
        self.assertFalse(is_match)
        self.assertEqual(actual_value, "C_20260330_009")

    def test_verify_record_not_found(self):
        """Test verification when record doesn't exist."""
        self.mock_client.invoke_json.side_effect = LarkCliCommandError(
            command=["base", "+record-get"],
            error_type="not_found",
            message="Record not found",
        )

        is_match, actual_value = self.backend.verify_record_identity(
            table_id_or_name="tbl_contact_log",
            record_id="recNonExistent",
            verification_field="合同编号",
            expected_value="C_20260330_010",
        )

        self.assertFalse(is_match)
        self.assertEqual(actual_value, "")


class TestSafeUpdateWorkflow(unittest.TestCase):
    """Test the complete safe update workflow."""

    def setUp(self):
        self.mock_client = Mock(spec=LarkCliClient)
        self.config = LiveWorkbenchConfig(
            base_token="test_token",
            table_targets={"客户联系记录": "tbl_contact_log"},
        )
        self.backend = LarkCliCustomerBackend(self.mock_client, self.config)

    def test_safe_update_workflow(self):
        """Test the complete safe update pattern from the guide.

        Workflow:
        1. List records to find record_id by business field
        2. Verify identity before update
        3. (In real code: perform update)
        4. (In real code: verify after update)
        """
        # Step 1: List records
        list_response = {
            "ok": True,
            "data": {
                "record_id_list": ["recAAA", "recBBB", "recCCC"],
                "fields": ["客户名称", "合同编号", "状态"],
                "data": [
                    ["客户A", "C_20260330_009", "active"],
                    ["客户B", "C_20260330_010", "pending"],
                    ["客户C", "C_20260330_011", "closed"],
                ],
            },
        }

        # Step 2: Pre-verification
        get_response = {
            "ok": True,
            "data": {
                "fields": {
                    "客户名称": "客户B",
                    "合同编号": "C_20260330_010",
                    "状态": "pending",
                }
            },
        }

        self.mock_client.invoke_json.side_effect = [list_response, get_response]

        # Find the record
        record = self.backend.find_record_by_field(
            "tbl_contact_log", "合同编号", "C_20260330_010"
        )
        self.assertEqual(record["record_id"], "recBBB")

        # Verify before update
        is_match, _ = self.backend.verify_record_identity(
            table_id_or_name="tbl_contact_log",
            record_id=record["record_id"],
            verification_field="合同编号",
            expected_value="C_20260330_010",
        )
        self.assertTrue(is_match)

        # At this point, we know it's safe to call:
        # +record-upsert --record-id recBBB --fields '{"状态": "已完成"}'


if __name__ == "__main__":
    unittest.main()
