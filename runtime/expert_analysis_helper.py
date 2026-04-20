"""Expert-analysis assembly helper for multi-source evidence scenes.

This module provides assembly and combination logic only.
Specific judgment decisions (what evidence means for a customer) remain at the scene layer.
See D-04: helper kept deliberately thin — does not interpret evidence, only assembles it.

AGENT-02: Expert card audit layer — input review before evidence assembly,
output review before SceneResult returned.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Literal

logger = logging.getLogger(__name__)

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


# AGENT-02: Expert card audit layer

from runtime.expert_card_loader import ExpertCardConfig


@dataclass
class ExpertCardAuditResult:
    """Result of an expert card audit pass.

    Per interface contract (review MEDIUM-07):
    "load card -> input audit -> evidence assembly -> output audit -> return"
    """

    expert_name: str
    review_type: str
    findings: list[str]  # Signals found or issues flagged
    passed: bool
    blocked: bool = False
    block_reason: str | None = None


def _check_signal_in_evidence(container: EvidenceContainer, signal: str) -> bool:
    """Check if a signal keyword/phrase appears in evidence container sources.

    Signals are matched case-insensitively against all available source content.
    Returns True if found, False if missing.
    """
    if container is None:
        return False
    signal_lower = signal.lower()
    for source in container.sources.values():
        if not source.available:
            continue
        for content_item in source.content:
            if signal_lower in content_item.lower():
                return True
    return False


def _check_dimension_in_recommendations(
    recommendations: list[str], dimension: str
) -> bool:
    """Check if a recommendation dimension is addressed.

    Simple keyword presence check: dimension is considered PASS if any
    recommendation contains a keyword related to the dimension.
    Returns True if addressed, False if flagged.
    """
    dimension_keywords: dict[str, list[str]] = {
        "专业性": ["专业", "规范", "标准", "符合", "proper", "professional"],
        "业务逻辑": ["业务", "逻辑", "合理", "合规", "business", "logic"],
        "可执行性": ["执行", "落地", "实施", "操作", "implement", "actionable"],
    }
    keywords = dimension_keywords.get(dimension, [dimension.lower()])
    for rec in recommendations:
        rec_lower = rec.lower()
        if any(kw in rec_lower for kw in keywords):
            return True
    return False


def run_input_audit(
    container: EvidenceContainer,
    input_card: ExpertCardConfig,
) -> ExpertCardAuditResult:
    """Run input audit: check evidence materials for missed signals.

    Per D-02: If prompt_file is set, use LLM mode instead of keyword mode.
    Per D-06: Fall back to keyword mode on LLM failure.
    Per OpenCode HIGH concern: explicit handling for timeout, auth failure,
    rate limit, empty response, parse failure.

    Interface contract step 2 (input audit before evidence assembly):
    - Runs before evidence assembly in integrated scenes
    - Fail-open: returns passed=True with empty findings if no evidence
    """
    # D-02: LLM mode when prompt_file present
    if input_card.prompt_file:
        try:
            from runtime.expert_agent_invoker import (
                invoke_llm_expert,
                build_input_review_prompt,
            )

            prompt = build_input_review_prompt(input_card, container)
            result = invoke_llm_expert(input_card, prompt)

            return ExpertCardAuditResult(
                expert_name=result.expert_name,
                review_type=input_card.review_type,
                findings=result.findings,
                passed=result.passed,
                blocked=result.blocked,
                block_reason=result.block_reason,
            )

        except asyncio.TimeoutError:
            # LLM timeout — fall back to keyword mode
            logger.warning(f"LLM timeout in input audit for {input_card.expert_name}, falling back to keyword")
        except ValueError as e:
            err_str = str(e).lower()
            if "api_key" in err_str or "auth" in err_str or "401" in err_str:
                # Auth failure (401) — fall back to keyword mode
                logger.warning(f"LLM auth failure in input audit for {input_card.expert_name}: {e}")
            elif "rate limit" in err_str or "429" in err_str:
                # Rate limit (429) — fall back to keyword mode
                logger.warning(f"LLM rate limit in input audit for {input_card.expert_name}, falling back to keyword")
            elif "empty" in err_str or "parse" in err_str or "no parseable" in err_str:
                # Empty response or parse failure — fall back to keyword mode
                logger.warning(f"LLM parse/empty error in input audit for {input_card.expert_name}: {e}")
            else:
                # Other ValueError — fall back to keyword mode
                logger.warning(f"LLM error in input audit for {input_card.expert_name}: {e}")
        except Exception as e:
            # Any other LLM error — fall back to keyword mode
            logger.warning(f"LLM input audit failed for {input_card.expert_name}, falling back to keyword: {e}")

    # Keyword mode (existing behavior)
    findings: list[str] = []
    if container is None:
        logger.warning(
            "run_input_audit: evidence_container is None, skipping audit (fail-open)"
        )
        return ExpertCardAuditResult(
            expert_name=input_card.expert_name,
            review_type=input_card.review_type,
            findings=["Audit skipped: no evidence container available"],
            passed=True,
        )

    for signal in input_card.check_signals:
        if _check_signal_in_evidence(container, signal):
            findings.append(f"FOUND: {signal}")
        else:
            findings.append(f"MISSING: {signal}")

    # passed = all signals found, or no signals defined
    passed = all(not f.startswith("MISSING") for f in findings) or len(findings) == 0
    return ExpertCardAuditResult(
        expert_name=input_card.expert_name,
        review_type=input_card.review_type,
        findings=findings,
        passed=passed,
    )


def run_output_audit(
    recommendations: list[str],
    output_card: ExpertCardConfig,
) -> ExpertCardAuditResult:
    """Run output audit: check recommendations for professionalism and business logic.

    Per D-02: If prompt_file is set, use LLM mode instead of keyword mode.
    Per D-06: Fall back to keyword mode on LLM failure.
    Per OpenCode HIGH concern: explicit handling for timeout, auth failure,
    rate limit, empty response, parse failure.

    Interface contract step 4 (output audit before SceneResult returned):
    - Runs after recommendations built, before SceneResult is returned
    - Fail-open: returns passed=True if no recommendations to audit
    """
    # D-02: LLM mode when prompt_file present
    if output_card.prompt_file:
        try:
            from runtime.expert_agent_invoker import (
                invoke_llm_expert,
                build_output_review_prompt,
            )

            prompt = build_output_review_prompt(output_card, recommendations)
            result = invoke_llm_expert(output_card, prompt)

            return ExpertCardAuditResult(
                expert_name=result.expert_name,
                review_type=output_card.review_type,
                findings=result.findings,
                passed=result.passed,
                blocked=result.blocked,
                block_reason=result.block_reason,
            )

        except asyncio.TimeoutError:
            # LLM timeout — fall back to keyword mode
            logger.warning(f"LLM timeout in output audit for {output_card.expert_name}, falling back to keyword")
        except ValueError as e:
            err_str = str(e).lower()
            if "api_key" in err_str or "auth" in err_str or "401" in err_str:
                # Auth failure (401) — fall back to keyword mode
                logger.warning(f"LLM auth failure in output audit for {output_card.expert_name}: {e}")
            elif "rate limit" in err_str or "429" in err_str:
                # Rate limit (429) — fall back to keyword mode
                logger.warning(f"LLM rate limit in output audit for {output_card.expert_name}, falling back to keyword")
            elif "empty" in err_str or "parse" in err_str or "no parseable" in err_str:
                # Empty response or parse failure — fall back to keyword mode
                logger.warning(f"LLM parse/empty error in output audit for {output_card.expert_name}: {e}")
            else:
                # Other ValueError — fall back to keyword mode
                logger.warning(f"LLM error in output audit for {output_card.expert_name}: {e}")
        except Exception as e:
            # Any other LLM error — fall back to keyword mode
            logger.warning(f"LLM output audit failed for {output_card.expert_name}, falling back to keyword: {e}")

    # Keyword mode (existing behavior)
    findings: list[str] = []
    if not recommendations:
        logger.warning(
            "run_output_audit: no recommendations to audit, skipping (fail-open)"
        )
        return ExpertCardAuditResult(
            expert_name=output_card.expert_name,
            review_type=output_card.review_type,
            findings=["Audit skipped: no recommendations available"],
            passed=True,
        )

    for dimension in output_card.check_signals:
        if _check_dimension_in_recommendations(recommendations, dimension):
            findings.append(f"PASS: {dimension}")
        else:
            findings.append(f"FLAG: {dimension}")

    # blocked if any block_on_flags are triggered
    block_on_flags = output_card.block_on_flags or []
    blocked = any(
        f"FLAG: {flag}" in findings for flag in block_on_flags
    )

    return ExpertCardAuditResult(
        expert_name=output_card.expert_name,
        review_type=output_card.review_type,
        findings=findings,
        passed=not blocked,
        blocked=blocked,
        block_reason="Flagged dimensions" if blocked else None,
    )
