"""Live lark-cli adapters for the local runtime layer."""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from typing import Any

from .lark_cli import LarkCliClient, LarkCliCommandError
from .models import (
    CapabilityCheck,
    CapabilityReport,
    ResourceHint,
    ResourceProbeOutcome,
    RuntimeSources,
)
from .semantic_registry import (
    SEMANTIC_FIELD_REGISTRY,
    get_integrated_base_tables,
    get_required_base_tables,
)


def _extract_base_tables(payload: dict[str, Any]) -> list[dict[str, str]]:
    data = payload.get("data")
    if not isinstance(data, dict):
        return []
    raw_tables = data.get("items")
    if not isinstance(raw_tables, list):
        raw_tables = data.get("tables")
    if not isinstance(raw_tables, list):
        return []
    tables: list[dict[str, str]] = []
    for item in raw_tables:
        if not isinstance(item, dict):
            continue
        table_id = item.get("table_id")
        if table_id is None:
            table_id = item.get("id")
        table_name = item.get("table_name")
        if table_name is None:
            table_name = item.get("name")
        normalized: dict[str, str] = {}
        if table_id is not None:
            normalized["table_id"] = str(table_id)
        if table_name is not None:
            normalized["table_name"] = str(table_name)
        if normalized:
            tables.append(normalized)
    return tables


@dataclass
class LiveWorkbenchConfig:
    base_token: str | None
    table_targets: dict[str, str] = field(default_factory=dict)
    customer_archive_folder: str | None = None
    meeting_notes_folder: str | None = None
    tasklist_guid: str | None = None
    todo_customer_field_guid: str | None = None
    todo_priority_field_guid: str | None = None
    todo_priority_options: list[str] = field(default_factory=list)
    todo_priority_option_guids: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_sources(cls, sources: RuntimeSources) -> "LiveWorkbenchConfig":
        table_targets = {
            table_name: table_name for table_name in get_integrated_base_tables()
        }
        table_targets["客户主数据"] = os.getenv(
            "FEISHU_AM_CUSTOMER_MASTER_TABLE",
            (
                sources.customer_master_table_id.value
                if sources.customer_master_table_id
                else "客户主数据"
            ),
        )
        table_targets["客户联系记录"] = os.getenv(
            "FEISHU_AM_CONTACT_LOG_TABLE", "客户联系记录"
        )
        table_targets["行动计划"] = os.getenv(
            "FEISHU_AM_ACTION_PLAN_TABLE", "行动计划"
        )
        return cls(
            base_token=os.getenv("FEISHU_AM_BASE_TOKEN")
            or (sources.base_token.value if sources.base_token else None),
            table_targets=table_targets,
            customer_archive_folder=(
                sources.customer_archive_folder.value
                if sources.customer_archive_folder
                else None
            ),
            meeting_notes_folder=(
                sources.meeting_notes_folder.value
                if sources.meeting_notes_folder
                else None
            ),
            tasklist_guid=(
                sources.todo_tasklist_guid.value
                if sources.todo_tasklist_guid
                else None
            ),
            todo_customer_field_guid=(
                sources.todo_customer_field_guid.value
                if sources.todo_customer_field_guid
                else None
            ),
            todo_priority_field_guid=(
                sources.todo_priority_field_guid.value
                if sources.todo_priority_field_guid
                else None
            ),
            todo_priority_options=list(sources.todo_priority_options),
            todo_priority_option_guids=dict(sources.todo_priority_option_guids),
        )

    def table_target(self, table_name: str) -> str:
        return self.table_targets.get(table_name, table_name)

    @property
    def customer_master_table(self) -> str:
        return self.table_target("客户主数据")

    @property
    def contact_log_table(self) -> str:
        return self.table_target("客户联系记录")

    @property
    def action_plan_table(self) -> str:
        return self.table_target("行动计划")


class LarkCliResourceProbe:
    def __init__(self, client: LarkCliClient, config: LiveWorkbenchConfig) -> None:
        self.client = client
        self.config = config
        self.last_outcomes: dict[str, ResourceProbeOutcome] = {}

    def confirm(self, hint: ResourceHint) -> bool:
        outcome = self.inspect(hint)
        self.last_outcomes[hint.key] = outcome
        return outcome.confirmed

    def inspect(self, hint: ResourceHint) -> ResourceProbeOutcome:
        if not hint.value:
            return ResourceProbeOutcome(
                key=hint.key,
                confirmed=False,
                status="blocked",
                reason="resource_missing",
            )
        if hint.key == "todo_tasklist_guid":
            return self._confirm_tasklist(hint.value)
        if hint.key == "base_token":
            return self._confirm_base(hint.value)
        if hint.key in {"customer_archive_folder", "meeting_notes_folder"}:
            return self._confirm_folder(hint.value)
        return ResourceProbeOutcome(
            key=hint.key,
            confirmed=False,
            status="blocked",
            reason="unsupported_probe",
        )

    def _confirm_tasklist(self, guid: str) -> ResourceProbeOutcome:
        try:
            payload = self.client.invoke_json(["task", "tasklists", "list"])
        except LarkCliCommandError as exc:
            return ResourceProbeOutcome(
                key="todo_tasklist_guid",
                confirmed=False,
                status="blocked",
                reason=exc.error_type,
                hint=exc.hint,
                details={"message": exc.message},
            )
        items = self._extract_list(payload, "items")
        if any(str(item.get("guid")) == guid for item in items):
            return ResourceProbeOutcome(
                key="todo_tasklist_guid",
                confirmed=True,
                status="available",
            )
        return ResourceProbeOutcome(
            key="todo_tasklist_guid",
            confirmed=False,
            status="degraded",
            reason="tasklist_not_found",
        )

    def _confirm_folder(self, folder_token: str) -> ResourceProbeOutcome:
        try:
            self.client.invoke_json(
                [
                    "drive",
                    "files",
                    "list",
                    "--params",
                    f'{{"folder_token":"{folder_token}"}}',
                ]
            )
        except LarkCliCommandError as exc:
            status = "degraded" if exc.error_type in {"permission", "missing_scope"} else "blocked"
            return ResourceProbeOutcome(
                key="drive_folder",
                confirmed=False,
                status=status,
                reason=exc.error_type,
                hint=exc.hint,
                details={"message": exc.message},
            )
        return ResourceProbeOutcome(
            key="drive_folder",
            confirmed=True,
            status="available",
        )

    def _confirm_base(self, base_token: str) -> ResourceProbeOutcome:
        try:
            self.client.invoke_json(
                [
                    "base",
                    "+table-list",
                    "--base-token",
                    base_token,
                    "--limit",
                    "1",
                ]
            )
        except LarkCliCommandError as exc:
            status = "degraded" if exc.error_type in {"permission", "missing_scope"} else "blocked"
            return ResourceProbeOutcome(
                key="base_token",
                confirmed=False,
                status=status,
                reason=exc.error_type,
                hint=exc.hint,
                details={"message": exc.message},
            )
        return ResourceProbeOutcome(
            key="base_token",
            confirmed=True,
            status="available",
        )

    def _extract_list(
        self, payload: dict[str, Any], preferred_key: str
    ) -> list[dict[str, Any]]:
        data = payload.get("data")
        if isinstance(data, dict):
            value = data.get(preferred_key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []


class LarkCliCustomerBackend:
    def __init__(self, client: LarkCliClient, config: LiveWorkbenchConfig) -> None:
        self.client = client
        self.config = config

    def search_customer_master(self, query: str) -> list[dict[str, str]]:
        if not self.config.base_token:
            return []
        precise_rows = self._search_customer_master_precise(query)
        if precise_rows:
            return precise_rows
        rows = self._list_records(self.config.table_target("客户主数据"), limit=200)
        matches: list[dict[str, str]] = []
        for row in rows:
            haystacks = [
                str(row.get("简称", "")),
                str(row.get("客户名称", "")),
                str(row.get("公司名称", "")),
                str(row.get("客户ID", "")),
                str(row.get("客户 ID", "")),
            ]
            if any(query in item or query == item for item in haystacks if item):
                matches.append({key: self._stringify(value) for key, value in row.items()})
        return matches

    def _search_customer_master_precise(self, query: str) -> list[dict[str, str]]:
        fields = self._list_field_names(self.config.table_target("客户主数据"))
        if not fields:
            return []
        searchable_fields = [
            field_name
            for field_name in ("简称", "客户名称", "公司名称", "客户ID", "客户 ID")
            if field_name in fields
        ]
        if not searchable_fields:
            return []
        dimensions = []
        alias_map = {
            "客户ID": "dim_customer_id",
            "客户 ID": "dim_customer_id_alt",
            "简称": "dim_short_name",
            "客户名称": "dim_customer_name",
            "公司名称": "dim_company_name",
            "客户档案": "dim_archive_link",
        }
        for field_name in ("客户ID", "客户 ID", "简称", "客户名称", "公司名称", "客户档案"):
            if field_name in fields:
                dimensions.append(
                    {
                        "field_name": field_name,
                        "alias": alias_map[field_name],
                    }
                )
        conditions = []
        for field_name in searchable_fields:
            conditions.append(
                {"field_name": field_name, "operator": "is", "value": [query]}
            )
            if field_name not in {"客户ID", "客户 ID"}:
                conditions.append(
                    {
                        "field_name": field_name,
                        "operator": "contains",
                        "value": [query],
                    }
                )
        dsl = {
            "datasource": {
                "type": "table",
                "table": {"tableId": self.config.table_target("客户主数据")},
            },
            "dimensions": dimensions,
            "filters": {
                "type": 1,
                "conjunction": "or",
                "conditions": conditions,
            },
            "pagination": {"limit": 20},
            "shaper": {"format": "flat"},
        }
        try:
            payload = self.client.invoke_json(
                [
                    "base",
                    "+data-query",
                    "--base-token",
                    self.config.base_token or "",
                    "--dsl",
                    json.dumps(dsl, ensure_ascii=False),
                ]
            )
        except LarkCliCommandError:
            return []
        data = payload.get("data")
        main_data = data.get("main_data") if isinstance(data, dict) else []
        if not isinstance(main_data, list):
            return []
        rows: list[dict[str, str]] = []
        for item in main_data:
            if not isinstance(item, dict):
                continue
            row = {
                "客户ID": self._extract_cell_value(item.get("dim_customer_id")),
                "客户 ID": self._extract_cell_value(item.get("dim_customer_id_alt")),
                "简称": self._extract_cell_value(item.get("dim_short_name")),
                "客户名称": self._extract_cell_value(item.get("dim_customer_name")),
                "公司名称": self._extract_cell_value(item.get("dim_company_name")),
                "客户档案": self._extract_cell_value(item.get("dim_archive_link")),
            }
            normalized = {
                key: value for key, value in row.items() if value not in ("", None)
            }
            if normalized:
                rows.append(normalized)
        return rows

    def _list_records(
        self, table_id_or_name: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        payload = self.client.invoke_json(
            [
                "base",
                "+record-list",
                "--base-token",
                self.config.base_token or "",
                "--table-id",
                table_id_or_name,
                "--limit",
                str(limit),
            ]
        )
        data = payload.get("data")
        if not isinstance(data, dict):
            return []
        matrix_rows = self._extract_matrix_rows(data)
        if matrix_rows:
            return matrix_rows
        items = data.get("items") or data.get("records") or []
        rows: list[dict[str, Any]] = []
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                fields = item.get("fields")
                if isinstance(fields, dict):
                    rows.append(fields)
                else:
                    rows.append(item)
        return rows

    def _extract_matrix_rows(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        columns = data.get("fields")
        matrix = data.get("data")
        if not isinstance(columns, list) or not isinstance(matrix, list):
            return []
        normalized_columns = [self._normalize_column_name(item) for item in columns]
        rows: list[dict[str, Any]] = []
        for row in matrix:
            if not isinstance(row, list):
                continue
            record: dict[str, Any] = {}
            for index, column in enumerate(normalized_columns):
                if not column:
                    continue
                record[column] = row[index] if index < len(row) else None
            if record:
                rows.append(record)
        return rows

    def _list_field_names(self, table_id_or_name: str) -> set[str]:
        try:
            payload = self.client.invoke_json(
                [
                    "base",
                    "+field-list",
                    "--base-token",
                    self.config.base_token or "",
                    "--table-id",
                    table_id_or_name,
                    "--limit",
                    "200",
                ]
            )
        except LarkCliCommandError:
            return set()
        data = payload.get("data")
        items = data.get("items") if isinstance(data, dict) else []
        if not isinstance(items, list):
            return set()
        result: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            field_name = item.get("field_name") or item.get("name")
            if field_name is not None:
                result.add(str(field_name))
        return result

    def _normalize_column_name(self, value: Any) -> str:
        column = self._stringify(value).strip()
        if column == "客户 ID":
            return "客户ID"
        return column

    def _stringify(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, list):
            return ", ".join(self._stringify(item) for item in value)
        if isinstance(value, dict):
            for key in ("text", "name", "url", "link"):
                if key in value:
                    return self._stringify(value[key])
        return str(value)

    def _extract_cell_value(self, value: Any) -> str:
        if isinstance(value, dict) and "value" in value:
            return self._stringify(value.get("value"))
        return self._stringify(value)

    def list_all_customers(self, limit: int = 200) -> list[dict[str, str]]:
        """List all customers from customer master for cohort scanning.

        Per D-12: cohort scan is user-triggered analytical entry, not scheduled.
        Uses _list_records with limit=200 to fetch customer master records.
        Returns list of customer record dicts with fields like 简称, 客户名称, 客户ID, 状态.
        """
        if not self.config.base_token:
            return []
        return self._list_records(self.config.table_target("客户主数据"), limit=limit)

    def filter_customers(
        self,
        customers: list[dict[str, str]],
        criteria: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Apply filter criteria to customer list.

        Supports:
          - name_contains: text match against 简称 and 客户名称 (case-insensitive)
          - status: list of status values to match against 状态 field
          - activity_within_days: filter by last activity date if field present (placeholder)

        Per D-03: user defines cohort via dynamic condition query interpreted into filter criteria.
        """
        filtered = list(customers)
        if "name_contains" in criteria:
            term = str(criteria["name_contains"]).lower()
            filtered = [
                c for c in filtered
                if term in str(c.get("简称") or "").lower()
                or term in str(c.get("客户名称") or "").lower()
            ]
        if "status" in criteria:
            statuses = criteria["status"]
            filtered = [c for c in filtered if c.get("状态") in statuses]
        # activity_within_days: check if last_activity field exists and is within window
        if "activity_within_days" in criteria:
            days = int(criteria["activity_within_days"])
            # Placeholder: requires actual last_activity field in customer master
            # Filter is a no-op if field is not present
            pass
        return filtered


class LarkCliBaseQueryBackend:
    """Thin Base query adapter.

    This layer only provides direct table reads and simple server-side filtering.
    It does not decide which business tables a scene should read.
    """

    def __init__(self, client: LarkCliClient, config: LiveWorkbenchConfig) -> None:
        self.client = client
        self.config = config
        self._customer_backend = LarkCliCustomerBackend(client, config)

    def query_rows_by_customer_id(
        self, table_name: str, customer_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        return self.query_rows_by_field_value(
            table_name=table_name,
            field_names=("客户ID", "客户 ID"),
            value=customer_id,
            limit=limit,
        )

    def discover_archive_candidates(
        self, customer_id: str, short_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        return self._discover_drive_candidates(
            folder_token=self.config.customer_archive_folder,
            customer_id=customer_id,
            short_name=short_name,
            topic_text="客户档案",
            limit=limit,
        )

    def discover_meeting_note_candidates(
        self,
        customer_id: str,
        short_name: str,
        topic_text: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return self._discover_drive_candidates(
            folder_token=self.config.meeting_notes_folder,
            customer_id=customer_id,
            short_name=short_name,
            topic_text=topic_text,
            limit=limit,
        )

    def query_rows_by_field_value(
        self,
        table_name: str,
        field_names: tuple[str, ...],
        value: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if not self.config.base_token:
            return []
        precise_rows = self._query_rows_precise(table_name, field_names, value, limit)
        if precise_rows:
            return precise_rows
        return self._query_rows_fallback(table_name, field_names, value, limit)

    def _query_rows_precise(
        self,
        table_name: str,
        field_names: tuple[str, ...],
        value: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        table_target = self.config.table_target(table_name)
        fields = self._customer_backend._list_field_names(table_target)
        matched_fields = [field_name for field_name in field_names if field_name in fields]
        if not matched_fields:
            return []
        alias_map = {
            field_name: f"dim_field_{index}"
            for index, field_name in enumerate(sorted(fields))
        }
        dimensions = [
            {"field_name": field_name, "alias": alias_map[field_name]}
            for field_name in sorted(fields)
        ]
        conditions = [
            {"field_name": field_name, "operator": "is", "value": [value]}
            for field_name in matched_fields
        ]
        dsl = {
            "datasource": {
                "type": "table",
                "table": {"tableId": table_target},
            },
            "dimensions": dimensions,
            "filters": {
                "type": 1,
                "conjunction": "or",
                "conditions": conditions,
            },
            "pagination": {"limit": limit},
            "shaper": {"format": "flat"},
        }
        try:
            payload = self.client.invoke_json(
                [
                    "base",
                    "+data-query",
                    "--base-token",
                    self.config.base_token or "",
                    "--dsl",
                    json.dumps(dsl, ensure_ascii=False),
                ]
            )
        except LarkCliCommandError:
            return []
        data = payload.get("data")
        main_data = data.get("main_data") if isinstance(data, dict) else []
        if not isinstance(main_data, list):
            return []
        rows: list[dict[str, Any]] = []
        for item in main_data:
            if not isinstance(item, dict):
                continue
            row: dict[str, Any] = {}
            for field_name, alias in alias_map.items():
                cell_value = item.get(alias)
                extracted = self._customer_backend._extract_cell_value(cell_value)
                if extracted != "":
                    row[field_name] = extracted
            if row:
                rows.append(row)
        return rows

    def _query_rows_fallback(
        self,
        table_name: str,
        field_names: tuple[str, ...],
        value: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        rows = self._customer_backend._list_records(
            self.config.table_target(table_name), limit=200
        )
        matches: list[dict[str, Any]] = []
        for row in rows:
            if any(
                self._customer_backend._stringify(row.get(field_name)) == value
                for field_name in field_names
            ):
                matches.append(row)
            if len(matches) >= limit:
                break
        return matches

    def _discover_drive_candidates(
        self,
        *,
        folder_token: str | None,
        customer_id: str,
        short_name: str,
        topic_text: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        if not folder_token:
            return []
        items = self._list_drive_items(folder_token, limit=max(limit * 5, 20))
        query_terms = [term for term in {customer_id, short_name, topic_text} if term]
        candidates: list[dict[str, Any]] = []
        for item in items:
            title = self._customer_backend._stringify(
                item.get("name") or item.get("title")
            ).strip()
            if not title:
                continue
            if query_terms and not any(term in title for term in query_terms):
                continue
            candidates.append(
                {
                    "title": title,
                    "url": self._customer_backend._stringify(
                        item.get("url") or item.get("link") or item.get("permalink")
                    ).strip(),
                    "token": self._customer_backend._stringify(
                        item.get("file_token") or item.get("token") or item.get("id")
                    ).strip(),
                }
            )
            if len(candidates) >= limit:
                break
        return candidates

    def _list_drive_items(self, folder_token: str, limit: int) -> list[dict[str, Any]]:
        try:
            payload = self.client.invoke_json(
                [
                    "drive",
                    "files",
                    "list",
                    "--params",
                    json.dumps(
                        {
                            "folder_token": folder_token,
                            "page_size": limit,
                        },
                        ensure_ascii=False,
                    ),
                ]
            )
        except LarkCliCommandError:
            return []
        data = payload.get("data")
        if not isinstance(data, dict):
            return []
        for key in ("items", "files", "list"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []


class LarkCliSchemaBackend:
    def __init__(self, client: LarkCliClient, config: LiveWorkbenchConfig) -> None:
        self.client = client
        self.config = config

    def get_table_schema(self, object_name: str) -> dict[str, dict[str, object]] | None:
        if object_name == "待办":
            return self._get_todo_schema()
        if not self.config.base_token:
            return None
        try:
            payload = self.client.invoke_json(
                [
                    "base",
                    "+field-list",
                    "--base-token",
                    self.config.base_token,
                    "--table-id",
                    object_name,
                    "--limit",
                    "200",
                ]
            )
        except LarkCliCommandError:
            return None
        fields = self._extract_fields(payload)
        if not fields:
            return None

        semantic_map = SEMANTIC_FIELD_REGISTRY.get(object_name, {})
        schema: dict[str, dict[str, object]] = {}
        for field in fields:
            field_name = str(field.get("field_name") or field.get("name") or "")
            if not field_name:
                continue
            field_type = self._normalize_field_type(field.get("type"))
            field_id = self._optional_str(field.get("field_id"))
            entry = {
                "field_id": field_id,
                "name": field_name,
                "type": field_type,
                "aliases": [],
                "options": self._extract_options(field),
                "synonyms": {},
            }
            if field_type in {"single_select", "multi_select"} and not entry["options"] and field_id:
                entry["options"] = self._load_live_options(object_name, field_id)
            schema[field_name] = entry
        for semantic_field, slot in semantic_map.items():
            canonical_name = str(slot.get("canonical_name", semantic_field))
            aliases = [str(item) for item in slot.get("aliases", [])]
            target = schema.get(canonical_name)
            if not target:
                for alias in aliases:
                    target = schema.get(alias)
                    if target:
                        break
            if target:
                target_aliases = target.setdefault("aliases", [])
                target_aliases.extend([canonical_name, *aliases])
                target["allowed_live_types"] = [
                    str(item) for item in slot.get("allowed_live_types", [])
                ]
                target["write_policy"] = slot.get("write_policy")
                target["strict_enum"] = bool(slot.get("strict_enum", False))
                schema[semantic_field] = target
        return schema

    def _get_todo_schema(self) -> dict[str, dict[str, object]] | None:
        if not self.config.tasklist_guid:
            return None
        tasklist = self._load_tasklist()
        if not tasklist:
            return None

        valid_member_ids = self._extract_tasklist_member_ids(tasklist)
        schema: dict[str, dict[str, object]] = {
            "summary": {
                "field_id": "summary",
                "name": "标题",
                "type": "text",
                "aliases": [],
                "options": [],
                "synonyms": {},
                "allowed_live_types": ["text"],
                "write_policy": "required_create",
            },
            "description": {
                "field_id": "description",
                "name": "描述",
                "type": "text",
                "aliases": [],
                "options": [],
                "synonyms": {},
                "allowed_live_types": ["text"],
                "write_policy": "safe_update",
            },
            "due_at": {
                "field_id": "due",
                "name": "截止时间",
                "type": "datetime",
                "aliases": [],
                "options": [],
                "synonyms": {},
                "allowed_live_types": ["datetime"],
                "write_policy": "safe_update",
            },
            "owner": {
                "field_id": "members.assignee",
                "name": "负责人",
                "type": "user",
                "aliases": ["assignee"],
                "options": [],
                "synonyms": {},
                "allowed_live_types": ["user"],
                "write_policy": "required_create",
                "valid_member_ids": valid_member_ids,
            },
        }
        if self.config.todo_customer_field_guid:
            schema["customer"] = {
                "field_id": self.config.todo_customer_field_guid,
                "name": "客户",
                "type": "text",
                "aliases": [],
                "options": [],
                "synonyms": {},
                "allowed_live_types": ["text"],
                "write_policy": "safe_update",
            }
        if self.config.todo_priority_field_guid:
            schema["priority"] = {
                "field_id": self.config.todo_priority_field_guid,
                "name": "优先级",
                "type": "single_select",
                "aliases": [],
                "options": list(self.config.todo_priority_options),
                "synonyms": {"高优先级": "高", "中优先级": "中", "低优先级": "低"},
                "allowed_live_types": ["single_select"],
                "write_policy": "safe_update",
                "strict_enum": True,
            }
        return schema

    def _extract_fields(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        data = payload.get("data")
        if not isinstance(data, dict):
            return []
        items = data.get("items") or data.get("fields") or []
        if not isinstance(items, list):
            return []
        return [item for item in items if isinstance(item, dict)]

    def _extract_options(self, field: dict[str, Any]) -> list[str]:
        property_keys = ("property", "properties", "field_property")
        for key in property_keys:
            props = field.get(key)
            if not isinstance(props, dict):
                continue
            options = props.get("options")
            if isinstance(options, list):
                names: list[str] = []
                for option in options:
                    if isinstance(option, dict):
                        name = option.get("name")
                        if name is not None:
                            names.append(str(name))
                    elif option is not None:
                        names.append(str(option))
                return names
        return []

    def _normalize_field_type(self, raw_type: object) -> str:
        if isinstance(raw_type, str):
            normalized = raw_type.lower()
        else:
            normalized = str(raw_type)
        mapping = {
            "text": "text",
            "1": "text",
            "number": "number",
            "2": "number",
            "single_select": "single_select",
            "3": "single_select",
            "select": "single_select",
            "multi_select": "multi_select",
            "4": "multi_select",
            "datetime": "datetime",
            "5": "datetime",
            "url": "url",
            "15": "url",
        }
        return mapping.get(normalized, normalized)

    def _optional_str(self, value: object) -> str | None:
        if value is None:
            return None
        return str(value)

    def _load_tasklist(self) -> dict[str, Any] | None:
        try:
            payload = self.client.invoke_json(
                [
                    "task",
                    "tasklists",
                    "get",
                    "--params",
                    json.dumps({"tasklist_guid": self.config.tasklist_guid}),
                ]
            )
        except LarkCliCommandError:
            return None
        data = payload.get("data")
        tasklist = data.get("tasklist") if isinstance(data, dict) else None
        return tasklist if isinstance(tasklist, dict) else None

    def _extract_tasklist_member_ids(self, tasklist: dict[str, Any]) -> list[str]:
        ids: list[str] = []
        for field_name in ("owner", "creator"):
            member = tasklist.get(field_name)
            if isinstance(member, dict):
                member_id = member.get("id")
                if member_id is not None:
                    ids.append(str(member_id))
        members = tasklist.get("members")
        if isinstance(members, list):
            for member in members:
                if not isinstance(member, dict):
                    continue
                member_id = member.get("id")
                if member_id is not None:
                    ids.append(str(member_id))
        return list(dict.fromkeys(ids))

    def _load_live_options(self, object_name: str, field_id: str) -> list[str]:
        try:
            payload = self.client.invoke_json(
                [
                    "base",
                    "+field-search-options",
                    "--base-token",
                    self.config.base_token or "",
                    "--table-id",
                    object_name,
                    "--field-id",
                    field_id,
                    "--limit",
                    "100",
                ]
            )
        except LarkCliCommandError:
            return []
        data = payload.get("data")
        options = data.get("options") if isinstance(data, dict) else []
        if not isinstance(options, list):
            return []
        return [
            str(option.get("name"))
            for option in options
            if isinstance(option, dict) and option.get("name") is not None
        ]


class LiveCapabilityReporter:
    def __init__(
        self,
        client: LarkCliClient,
        config: LiveWorkbenchConfig,
        resource_probe: LarkCliResourceProbe,
    ) -> None:
        self.client = client
        self.config = config
        self.resource_probe = resource_probe

    def build(self, sources: RuntimeSources) -> CapabilityReport:
        checks = [
            self._build_base_check(),
            self._build_docs_check(sources),
            self._build_task_check(sources),
        ]
        return CapabilityReport(checks=checks)

    def _build_base_check(self) -> CapabilityCheck:
        if not self.config.base_token:
            return CapabilityCheck(
                name="base_access",
                status="blocked",
                reasons=["missing_base_token"],
                details={"env_var": "FEISHU_AM_BASE_TOKEN"},
            )
        try:
            payload = self.client.invoke_json(
                [
                    "base",
                    "+table-list",
                    "--base-token",
                    self.config.base_token,
                    "--limit",
                    "200",
                ]
            )
        except LarkCliCommandError as exc:
            status = "degraded" if exc.error_type in {"permission", "missing_scope"} else "blocked"
            return CapabilityCheck(
                name="base_access",
                status=status,
                reasons=[exc.error_type],
                details={"message": exc.message, "hint": exc.hint},
            )
        items = _extract_base_tables(payload)
        available_table_ids = {
            str(item.get("table_id") or item.get("id"))
            for item in items
            if isinstance(item, dict) and (item.get("table_id") is not None or item.get("id") is not None)
        }
        available_table_names = {
            str(item.get("table_name") or item.get("name"))
            for item in items
            if isinstance(item, dict) and (item.get("table_name") is not None or item.get("name") is not None)
        }
        required_table_names = set(get_required_base_tables())
        required_tables = {
            table_name: self.config.table_target(table_name)
            for table_name in required_table_names
        }
        missing = [
            table_name
            for table_name, target in required_tables.items()
            if target not in available_table_ids and target not in available_table_names
        ]
        if missing:
            return CapabilityCheck(
                name="base_access",
                status="degraded",
                reasons=["required_tables_missing"],
                details={
                    "missing_tables": missing,
                    "required_tables": required_tables,
                },
            )
        return CapabilityCheck(
            name="base_access",
            status="available",
            details={
                "table_targets": self.config.table_targets,
                "required_tables": required_tables,
                "required_tables_verified": True,
            },
        )

    def _build_docs_check(self, sources: RuntimeSources) -> CapabilityCheck:
        checks: list[ResourceProbeOutcome] = []
        for hint in (
            sources.customer_archive_folder,
            sources.meeting_notes_folder,
        ):
            if hint:
                checks.append(self.resource_probe.inspect(hint))
        if not checks:
            return CapabilityCheck(
                name="docs_access",
                status="blocked",
                reasons=["docs_resource_missing"],
            )
        if all(item.confirmed for item in checks):
            return CapabilityCheck(
                name="docs_access",
                status="available",
                details={"folders": [item.key for item in checks]},
            )
        statuses = {item.status for item in checks}
        status = "degraded" if "degraded" in statuses else "blocked"
        reasons = [item.reason or "docs_unconfirmed" for item in checks if not item.confirmed]
        details = {
            "outcomes": [
                {
                    "status": item.status,
                    "reason": item.reason,
                    "hint": item.hint,
                }
                for item in checks
            ]
        }
        return CapabilityCheck(
            name="docs_access",
            status=status,
            reasons=reasons,
            details=details,
        )

    def _build_task_check(self, sources: RuntimeSources) -> CapabilityCheck:
        hint = sources.todo_tasklist_guid
        if not hint:
            return CapabilityCheck(
                name="task_access",
                status="blocked",
                reasons=["tasklist_missing"],
            )
        outcome = self.resource_probe.inspect(hint)
        reasons = [outcome.reason] if outcome.reason else []
        details = {"hint": outcome.hint, **outcome.details}
        return CapabilityCheck(
            name="task_access",
            status=outcome.status,
            reasons=reasons,
            details=details,
        )
