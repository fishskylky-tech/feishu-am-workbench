"""Resolve currently known runtime resources for the personal workflow."""

from __future__ import annotations

from typing import Protocol

from .models import ResourceHint, ResourceResolution, RuntimeSources


class ResourceProbe(Protocol):
    def confirm(self, hint: ResourceHint) -> bool:
        ...


class ResourceResolver:
    REQUIRED_KEYS = (
        "base_token",
        "customer_archive_folder",
        "meeting_notes_folder",
        "todo_tasklist_guid",
    )

    def __init__(self, probe: ResourceProbe | None = None) -> None:
        self.probe = probe

    def resolve(self, sources: RuntimeSources) -> ResourceResolution:
        hints: list[ResourceHint] = []
        missing: list[str] = []
        unconfirmed: list[str] = []

        for key in self.REQUIRED_KEYS:
            value = getattr(sources, key, None)
            if value and value.value:
                if self.probe:
                    value.confirmed_live = self.probe.confirm(value)
                    if not value.confirmed_live:
                        unconfirmed.append(key)
                hints.append(value)
            else:
                missing.append(key)

        status: str
        if not missing and not unconfirmed:
            status = "resolved"
        elif len(missing) == len(self.REQUIRED_KEYS):
            status = "unresolved"
        else:
            status = "partial"

        return ResourceResolution(
            status=status,
            hints_used=hints,
            missing_keys=missing,
            unconfirmed_keys=unconfirmed,
        )
