"""Load current runtime source hints from repository reference files."""

from __future__ import annotations

import os
from pathlib import Path
import re
from urllib.parse import parse_qs, urlparse

from .models import ResourceHint, RuntimeSources


class RuntimeSourceLoader:
    """Parses current repository references into runtime source hints."""

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
        actual_mapping = self._read("references/actual-field-mapping.md")
        architecture = self._read("references/workbench-information-architecture.md")
        skill = self._read("SKILL.md")
        routing = self._read("references/update-routing.md")
        live_links = self._read_optional("references/live-resource-links.example.md")
        env_base_url = self._env_value("base_url")
        base_url = self._extract_single(
            env_base_url or live_links,
            r"^(.+)$" if env_base_url else r"Workbench Base: `([^`]+)`",
            f"env:{self.ENV_VARS['base_url']}" if env_base_url else "references/live-resource-links.example.md",
            "base_url",
        )
        base_parts = self._parse_base_link(base_url.value if base_url else None)
        archive_env = self._env_value("customer_archive_folder")
        todo_tasklist_hint = self._extract_single(
            actual_mapping,
            r"(?i:(?:\*\*|__|`)?(?:tasklist_guid|Tasklist(?:\s+GUID)?)(?:\*\*|__|`)?\s*[:：]\s*`?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})`?)",
            "references/actual-field-mapping.md",
            "todo_tasklist_guid",
        )
        todo_customer_field_hint = self._extract_single(
            actual_mapping,
            r"-\s*`客户`[^`]*?(?:`guid`|guid)\s*[:：]\s*`([a-f0-9\-]+)`",
            "references/actual-field-mapping.md",
            "todo_customer_field_guid",
        )
        todo_priority_field_hint = self._extract_single(
            actual_mapping,
            r"-\s*`优先级`[^`]*?(?:`guid`|guid)\s*[:：]\s*`([a-f0-9\-]+)`",
            "references/actual-field-mapping.md",
            "todo_priority_field_guid",
        )

        sources = RuntimeSources(
            base_token=self._env_or_fallback(
                key="base_token",
                fallback_value=base_parts.get("base_token"),
                fallback_source="references/live-resource-links.example.md",
            ),
            customer_master_table_id=self._env_or_fallback(
                key="customer_master_table_id",
                fallback_value=base_parts.get("table_id"),
                fallback_source="references/live-resource-links.example.md",
            ),
            customer_archive_folder=self._extract_folder(
                archive_env or architecture,
                label="customer_archive_folder",
                pattern=r"^(.+)$"
                if archive_env
                else r"Layer 4: Customer archive.*?Location: Feishu docs folder `([^`]+)`",
                source_file=(
                    f"env:{self.ENV_VARS['customer_archive_folder']}"
                    if archive_env
                    else "references/workbench-information-architecture.md"
                ),
            ),
            meeting_notes_folder=self._meeting_notes_hint(skill, routing, architecture),
            todo_tasklist_guid=self._env_or_fallback(
                key="todo_tasklist_guid",
                fallback_value=todo_tasklist_hint.value if todo_tasklist_hint else None,
                fallback_source="references/actual-field-mapping.md",
            ),
            todo_customer_field_guid=self._env_or_fallback(
                key="todo_customer_field_guid",
                fallback_value=todo_customer_field_hint.value if todo_customer_field_hint else None,
                fallback_source="references/actual-field-mapping.md",
            ),
            todo_priority_field_guid=self._env_or_fallback(
                key="todo_priority_field_guid",
                fallback_value=todo_priority_field_hint.value if todo_priority_field_hint else None,
                fallback_source="references/actual-field-mapping.md",
            ),
            todo_priority_options=self._extract_priority_options(actual_mapping),
            todo_priority_option_guids=self._extract_priority_option_guids(actual_mapping),
            source_files=[
                "SKILL.md",
                "references/update-routing.md",
                "references/workbench-information-architecture.md",
                "references/actual-field-mapping.md",
                "references/live-resource-links.example.md",
            ],
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

    def _meeting_notes_hint(self, skill: str, routing: str, architecture: str) -> ResourceHint | None:
        env_value = self._env_value("meeting_notes_folder")
        if env_value:
            return ResourceHint(
                key="meeting_notes_folder",
                source_file=f"env:{self.ENV_VARS['meeting_notes_folder']}",
                value=env_value,
            )
        return self._extract_first(
            [
                (
                    skill,
                    r"dedicated Feishu folder `([^`]+)`",
                    "SKILL.md",
                    "meeting_notes_folder",
                ),
                (
                    routing,
                    r"Default meeting-note folder: `([^`]+)`",
                    "references/update-routing.md",
                    "meeting_notes_folder",
                ),
                (
                    architecture,
                    r"Layer 5: Meeting-note cold memory.*?Location: Feishu docs folder `([^`]+)`",
                    "references/workbench-information-architecture.md",
                    "meeting_notes_folder",
                ),
            ]
        )

    def _read(self, relative_path: str) -> str:
        return (self.repo_root / relative_path).read_text(encoding="utf-8")

    def _read_optional(self, relative_path: str) -> str:
        path = self.repo_root / relative_path
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def _extract_folder(
        self, text: str, label: str, pattern: str, source_file: str
    ) -> ResourceHint | None:
        return self._extract_single(text, pattern, source_file, label)

    def _extract_single(
        self, text: str, pattern: str, source_file: str, key: str
    ) -> ResourceHint | None:
        match = re.search(pattern, text, flags=re.S)
        if not match:
            return None
        return ResourceHint(key=key, source_file=source_file, value=match.group(1))

    def _extract_first(
        self, candidates: list[tuple[str, str, str, str]]
    ) -> ResourceHint | None:
        for text, pattern, source_file, key in candidates:
            hint = self._extract_single(text, pattern, source_file, key)
            if hint and hint.value:
                return hint
        return None

    def _hint_from_value(
        self, key: str, source_file: str, value: str | None
    ) -> ResourceHint | None:
        if not value:
            return None
        return ResourceHint(key=key, source_file=source_file, value=value)

    def _extract_priority_options(self, text: str) -> list[str]:
        # Support multiple anchor patterns for priority options section
        # The section starts with `优先级` and ends with anchor text like "Treat these" or "Current validated"
        section_match = re.search(
            r"`优先级`[^#]*?(?:current known options|已知选项)[:：]?\s*(.*?)(?:Treat these task custom fields|Current validated custom fields|^#|\Z)",
            text,
            flags=re.S | re.M,
        )
        if not section_match:
            return []
        # Extract all items in backticks after list markers
        return re.findall(r"[-*]\s*`([^`]+)`", section_match.group(1))

    def _extract_priority_option_guids(self, text: str) -> dict[str, str]:
        # Support both -> and → as separators, but be specific about GUID format
        # Look for lines that have an option name mapped to a GUID (UUID format)
        matches = re.findall(
            r"[-*]\s*`([^`]+)`\s*(?:->|→)\s*`([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})`",
            text
        )
        return {name.strip(): guid.strip() for name, guid in matches}

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
