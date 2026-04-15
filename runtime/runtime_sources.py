"""Load runtime source hints from private runtime inputs only."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .models import ResourceHint, RuntimeSources


class RuntimeSourceLoader:
    """Builds runtime source hints from env-backed private inputs only."""

    ENV_VARS = {
        "base_url": "FEISHU_AM_WORKBENCH_BASE_URL",
        "base_token": "FEISHU_AM_BASE_TOKEN",
        "customer_master_table_id": "FEISHU_AM_CUSTOMER_MASTER_TABLE_ID",
        "customer_archive_folder": "FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER",
        "meeting_notes_folder": "FEISHU_AM_MEETING_NOTES_FOLDER",
        "todo_tasklist_guid": "FEISHU_AM_TODO_TASKLIST_GUID",
        "todo_customer_field_guid": "FEISHU_AM_TODO_CUSTOMER_FIELD_GUID",
        "todo_priority_field_guid": "FEISHU_AM_TODO_PRIORITY_FIELD_GUID",
    }

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root)

    def load(self) -> RuntimeSources:
        env_base_url = self._env_value("base_url")
        base_parts = self._parse_base_link(env_base_url)

        source_files = [
            f"env:{env_name}"
            for env_name in self.ENV_VARS.values()
            if os.environ.get(env_name, "").strip()
        ]

        sources = RuntimeSources(
            base_token=self._env_or_fallback(
                key="base_token",
                fallback_value=base_parts.get("base_token"),
                fallback_source=f"env:{self.ENV_VARS['base_url']}",
            ),
            customer_master_table_id=self._env_or_fallback(
                key="customer_master_table_id",
                fallback_value=base_parts.get("table_id"),
                fallback_source=f"env:{self.ENV_VARS['base_url']}",
            ),
            customer_archive_folder=self._env_or_fallback(
                key="customer_archive_folder",
                fallback_value=None,
                fallback_source=f"env:{self.ENV_VARS['customer_archive_folder']}",
            ),
            meeting_notes_folder=self._env_or_fallback(
                key="meeting_notes_folder",
                fallback_value=None,
                fallback_source=f"env:{self.ENV_VARS['meeting_notes_folder']}",
            ),
            todo_tasklist_guid=self._env_or_fallback(
                key="todo_tasklist_guid",
                fallback_value=None,
                fallback_source=f"env:{self.ENV_VARS['todo_tasklist_guid']}",
            ),
            todo_customer_field_guid=self._env_or_fallback(
                key="todo_customer_field_guid",
                fallback_value=None,
                fallback_source=f"env:{self.ENV_VARS['todo_customer_field_guid']}",
            ),
            todo_priority_field_guid=self._env_or_fallback(
                key="todo_priority_field_guid",
                fallback_value=None,
                fallback_source=f"env:{self.ENV_VARS['todo_priority_field_guid']}",
            ),
            todo_priority_options=[],
            todo_priority_option_guids={},
            source_files=source_files,
        )
        return sources

    def _env_value(self, key: str) -> str | None:
        env_name = self.ENV_VARS[key]
        value = os.environ.get(env_name)
        if not value:
            return None
        value = value.strip()
        return value or None

    def _env_or_fallback(
        self, key: str, fallback_value: str | None, fallback_source: str
    ) -> ResourceHint | None:
        env_value = self._env_value(key)
        if env_value:
            return ResourceHint(
                key=key,
                source_file=f"env:{self.ENV_VARS[key]}",
                value=env_value,
            )
        return self._hint_from_value(key, fallback_source, fallback_value)

    def _hint_from_value(
        self, key: str, source_file: str, value: str | None
    ) -> ResourceHint | None:
        if not value:
            return None
        return ResourceHint(key=key, source_file=source_file, value=value)

    def _parse_base_link(self, url: str | None) -> dict[str, str]:
        if not url:
            return {}
        parsed = urlparse(url)
        parts = parsed.path.rstrip("/").split("/")
        query = parse_qs(parsed.query)
        result: dict[str, str] = {}
        if parts and len(parts) >= 3 and parts[-2] == "base":
            result["base_token"] = parts[-1]
        table_ids = query.get("table")
        if table_ids:
            result["table_id"] = table_ids[0]
        return result
