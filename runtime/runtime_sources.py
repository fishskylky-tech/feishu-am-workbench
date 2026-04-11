"""Load current runtime source hints from repository reference files."""

from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import parse_qs, urlparse

from .models import ResourceHint, RuntimeSources


class RuntimeSourceLoader:
    """Parses current repository references into runtime source hints."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root)

    def load(self) -> RuntimeSources:
        actual_mapping = self._read("references/actual-field-mapping.md")
        architecture = self._read("references/workbench-information-architecture.md")
        skill = self._read("SKILL.md")
        routing = self._read("references/update-routing.md")
        live_links = self._read_optional("references/live-resource-links.md")
        base_url = self._extract_single(
            live_links,
            r"Workbench Base: `([^`]+)`",
            "references/live-resource-links.md",
            "base_url",
        )
        base_parts = self._parse_base_link(base_url.value if base_url else None)

        sources = RuntimeSources(
            base_token=self._hint_from_value(
                "base_token",
                "references/live-resource-links.md",
                base_parts.get("base_token"),
            ),
            customer_master_table_id=self._hint_from_value(
                "customer_master_table_id",
                "references/live-resource-links.md",
                base_parts.get("table_id"),
            ),
            customer_archive_folder=self._extract_folder(
                architecture,
                label="customer_archive_folder",
                pattern=r"Layer 4: Customer archive.*?Location: Feishu docs folder `([^`]+)`",
                source_file="references/workbench-information-architecture.md",
            ),
            meeting_notes_folder=self._extract_first(
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
            ),
            todo_tasklist_guid=self._extract_single(
                actual_mapping,
                r"`tasklist_guid`: `([^`]+)`",
                "references/actual-field-mapping.md",
                "todo_tasklist_guid",
            ),
            todo_customer_field_guid=self._extract_single(
                actual_mapping,
                r"`客户`.*?`guid`: `([^`]+)`",
                "references/actual-field-mapping.md",
                "todo_customer_field_guid",
            ),
            todo_priority_field_guid=self._extract_single(
                actual_mapping,
                r"`优先级`.*?`guid`: `([^`]+)`",
                "references/actual-field-mapping.md",
                "todo_priority_field_guid",
            ),
            todo_priority_options=self._extract_priority_options(actual_mapping),
            todo_priority_option_guids=self._extract_priority_option_guids(actual_mapping),
            source_files=[
                "SKILL.md",
                "references/update-routing.md",
                "references/workbench-information-architecture.md",
                "references/actual-field-mapping.md",
                "references/live-resource-links.md",
            ],
        )
        return sources

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
        section_match = re.search(
            r"- `优先级`.*?current known options:(.*?)(?:Treat these task custom fields|Current validated custom fields:)",
            text,
            flags=re.S,
        )
        if not section_match:
            return []
        return re.findall(r"- `([^`]+)`", section_match.group(1))

    def _extract_priority_option_guids(self, text: str) -> dict[str, str]:
        matches = re.findall(r"- `([^`]+)` -> `([^`]+)`", text)
        return {name: guid for name, guid in matches}

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
