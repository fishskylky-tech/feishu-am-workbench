"""Expert-analysis assembly helper for multi-source evidence scenes.

This module provides assembly and combination logic only.
Specific judgment decisions (what evidence means for a customer) remain at the scene layer.
See D-04: helper kept deliberately thin — does not interpret evidence, only assembles it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

WriteCeiling = Literal["normal", "recommendation-only"]

EvidenceQuality = Literal["live", "recovered", "archived", "external", "missing"]

EvidenceSourceName = Literal[
    "transcript",
    "customer_master",
    "contact_records",
    "action_plan",
    "meeting_notes",
    "customer_archive",
    "external_input",
]

LensLabel = Literal["risk", "opportunity", "relationship", "project_progress"]


@dataclass
class EvidenceSource:
    name: EvidenceSourceName
    quality: EvidenceQuality
    available: bool
    content: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)
    missing_reason: str | None = None

    def summary(self) -> str:
        if not self.available:
            return f"{self.name}: UNAVAILABLE ({self.missing_reason or 'source missing'})"
        return f"{self.name}: {self.quality} | {len(self.content)} items"


@dataclass
class LensAttribution:
    lens: LensLabel
    source_names: list[EvidenceSourceName]
    conclusions: list[str]
    confidence: float = 1.0


CRITICAL_SOURCES: set[EvidenceSourceName] = {"customer_master", "contact_records"}

LENS_SOURCE_MAP: dict[LensLabel, list[EvidenceSourceName]] = {
    "risk": ["customer_master", "contact_records", "action_plan"],
    "opportunity": ["customer_master", "meeting_notes", "action_plan"],
    "relationship": ["contact_records", "meeting_notes"],
    "project_progress": ["action_plan", "meeting_notes", "customer_archive"],
}


@dataclass
class EvidenceContainer:
    sources: dict[EvidenceSourceName, EvidenceSource] = field(default_factory=dict)
    overall_quality: EvidenceQuality = "missing"
    write_ceiling: WriteCeiling = "recommendation-only"
    missing_source_count: int = 0
    critical_source_missing: bool = False
    missing_critical_sources: list[EvidenceSourceName] = field(default_factory=list)
    fallback_reason: str | None = None

    def get_source(self, name: EvidenceSourceName) -> EvidenceSource | None:
        return self.sources.get(name)

    def is_complete(self) -> bool:
        return self.missing_source_count == 0 and not self.critical_source_missing

    def available_sources(self) -> list[EvidenceSourceName]:
        return [name for name, src in self.sources.items() if src.available]

    def render_source_summary(self) -> list[str]:
        return [src.summary() for src in self.sources.values()]


@dataclass
class EvidenceAssemblyInput:
    """Raw inputs for evidence assembly — collected before container is built."""

    transcript_content: list[str] = field(default_factory=list)
    customer_master_content: list[str] = field(default_factory=list)
    contact_records_content: list[str] = field(default_factory=list)
    action_plan_content: list[str] = field(default_factory=list)
    meeting_notes_content: list[str] = field(default_factory=list)
    customer_archive_content: list[str] = field(default_factory=list)
    external_inputs: dict[str, list[str]] = field(default_factory=dict)

    # Availability flags
    transcript_available: bool = True
    customer_master_available: bool = True
    contact_records_available: bool = True
    action_plan_available: bool = True
    meeting_notes_available: bool = True
    customer_archive_available: bool = True

    # Missing reasons (when unavailable)
    transcript_missing_reason: str | None = None
    customer_master_missing_reason: str | None = None
    contact_records_missing_reason: str | None = None
    action_plan_missing_reason: str | None = None
    meeting_notes_missing_reason: str | None = None
    customer_archive_missing_reason: str | None = None


class ExpertAnalysisHelper:
    """Assembly and combination logic for multi-source evidence.

    Per D-04: kept deliberately thin — provides assembly and combination logic only.
    Scene layer retains all specific judgment decisions.
    """

    def __init__(self, input_data: EvidenceAssemblyInput) -> None:
        self._input = input_data

    def assemble(self) -> EvidenceContainer:
        """Build an EvidenceContainer from the provided inputs.

        Returns a container with all sources labelled, quality-rated,
        and missing-source flags set. Scenes use this container
        to produce output without handling raw source heterogeneity.
        """
        container = EvidenceContainer()

        self._add_source(
            container=container,
            name="customer_master",
            content=self._input.customer_master_content,
            available=self._input.customer_master_available,
            missing_reason=self._input.customer_master_missing_reason,
            default_quality="live",
        )
        self._add_source(
            container=container,
            name="contact_records",
            content=self._input.contact_records_content,
            available=self._input.contact_records_available,
            missing_reason=self._input.contact_records_missing_reason,
            default_quality="live",
        )
        self._add_source(
            container=container,
            name="action_plan",
            content=self._input.action_plan_content,
            available=self._input.action_plan_available,
            missing_reason=self._input.action_plan_missing_reason,
            default_quality="recovered",
        )
        self._add_source(
            container=container,
            name="meeting_notes",
            content=self._input.meeting_notes_content,
            available=self._input.meeting_notes_available,
            missing_reason=self._input.meeting_notes_missing_reason,
            default_quality="recovered",
        )
        self._add_source(
            container=container,
            name="customer_archive",
            content=self._input.customer_archive_content,
            available=self._input.customer_archive_available,
            missing_reason=self._input.customer_archive_missing_reason,
            default_quality="archived",
        )
        self._add_source(
            container=container,
            name="transcript",
            content=self._input.transcript_content,
            available=self._input.transcript_available,
            missing_reason=self._input.transcript_missing_reason,
            default_quality="live",
        )

        for ext_name, ext_content in self._input.external_inputs.items():
            source_name = f"external:{ext_name}"  # type: ignore[assignment]
            container.sources[source_name] = EvidenceSource(  # type: ignore[index]
                name=source_name,  # type: ignore[arg-type]
                quality="external",
                available=bool(ext_content),
                content=list(ext_content),
                missing_reason=None if ext_content else "no content provided",
            )

        container.missing_source_count = sum(
            1 for src in container.sources.values() if not src.available
        )
        container.critical_source_missing = any(
            name in CRITICAL_SOURCES and not src.available
            for name, src in container.sources.items()
        )
        container.missing_critical_sources = [
            name for name, src in container.sources.items()
            if name in CRITICAL_SOURCES and not src.available
        ]
        container.overall_quality = self._compute_overall_quality(container)
        container.write_ceiling = self._compute_write_ceiling(container)
        container.fallback_reason = self._compute_fallback_reason(container)

        return container

    def _add_source(
        self,
        *,
        container: EvidenceContainer,
        name: EvidenceSourceName,
        content: list[str],
        available: bool,
        missing_reason: str | None,
        default_quality: EvidenceQuality,
    ) -> None:
        quality: EvidenceQuality = default_quality if available else "missing"
        container.sources[name] = EvidenceSource(
            name=name,
            quality=quality,
            available=available,
            content=list(content) if available else [],
            missing_reason=missing_reason if not available else None,
        )

    def _compute_overall_quality(self, container: EvidenceContainer) -> EvidenceQuality:
        if container.critical_source_missing:
            return "missing"
        available_qualities = [
            src.quality for src in container.sources.values() if src.available
        ]
        if not available_qualities:
            return "missing"
        if all(q == "live" for q in available_qualities):
            return "live"
        if any(q == "live" for q in available_qualities):
            return "recovered"
        return "archived"

    def _compute_write_ceiling(self, container: EvidenceContainer) -> WriteCeiling:
        if container.critical_source_missing:
            return "recommendation-only"
        if container.missing_source_count > 2:
            return "recommendation-only"
        return "normal"

    def _compute_fallback_reason(self, container: EvidenceContainer) -> str | None:
        if container.critical_source_missing:
            missing = ", ".join(container.missing_critical_sources)
            return f"Critical sources missing: {missing}. Results cannot proceed to write."
        if container.missing_source_count > 0:
            unavailable = [name for name, src in container.sources.items() if not src.available]
            return f"Partial evidence — unavailable: {', '.join(unavailable)}"
        return None

    def combine_evidence_texts(
        self,
        container: EvidenceContainer,
        *,
        priority_sources: list[EvidenceSourceName] | None = None,
    ) -> list[str]:
        """Combine evidence texts from available sources, in priority order.

        Per D-05: scene code must remain readable. This helper only
        assembles; it does not filter or interpret.
        """
        combined: list[str] = []
        priority_sources = priority_sources or [
            "customer_master",
            "contact_records",
            "action_plan",
            "meeting_notes",
            "customer_archive",
            "transcript",
        ]
        for name in priority_sources:
            source = container.sources.get(name)
            if source and source.available and source.content:
                combined.extend(source.content)
        return combined

    def detect_conflicts(
        self,
        container: EvidenceContainer,
    ) -> list[str]:
        """Detect obvious evidence conflicts across sources.

        Per D-04: thin helper — only detects structural conflicts
        (same fact stated differently across sources). Semantic judgment
        about what conflicts mean remains at the scene layer.
        """
        conflicts: list[str] = []
        # Group content by normalized form to find potential duplicates/conflicts
        source_contents: dict[str, list[tuple[EvidenceSourceName, str]]] = {}
        for name, source in container.sources.items():
            if not source.available:
                continue
            for item in source.content:
                normalized = item.casefold().strip()
                if normalized:
                    source_contents.setdefault(normalized, []).append((name, item))

        for normalized, appearances in source_contents.items():
            if len(appearances) > 1:
                sources_str = ", ".join(name for name, _ in appearances)
                conflicts.append(
                    f"Evidence conflict: '{appearances[0][1]}' appears in {sources_str}"
                )
        return conflicts


def build_lens_attributions(
    container: EvidenceContainer,
    lens_results: dict[LensLabel, list[str]],
) -> list[LensAttribution]:
    """Build per-lens source attribution for STAT-01 output.

    Per D-10: each lens draws from relevant EvidenceContainer sources.
    """
    attributions: list[LensAttribution] = []
    for lens_name, conclusions in lens_results.items():
        if not conclusions:
            continue
        source_names = LENS_SOURCE_MAP.get(lens_name, [])
        attributions.append(LensAttribution(
            lens=lens_name,
            source_names=source_names,
            conclusions=list(conclusions),
        ))
    return attributions
