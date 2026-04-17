"""Shared data models for the local runtime layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


Status = Literal["resolved", "partial", "unresolved"]
ContextStatus = Literal["not-run", "completed", "partial", "context-limited"]
PreflightStatus = Literal["safe", "safe_with_drift", "blocked"]
CapabilityStatus = Literal["available", "degraded", "blocked"]
TableRole = Literal["snapshot", "detail", "dimension", "bridge"]
WriteOperation = Literal["create", "update"]
DedupeDecision = Literal["create_new", "update_existing", "create_subtask", "no_write"]
GuardStatus = Literal["allowed", "blocked"]
ExecutedOperation = Literal["create", "update", "blocked", "no_write"]
WriteCeiling = Literal["normal", "recommendation-only"]


@dataclass
class ResourceHint:
    key: str
    source_file: str
    value: str | None
    confirmed_live: bool = False


@dataclass
class RuntimeSources:
    base_token: ResourceHint | None = None
    customer_master_table_id: ResourceHint | None = None
    customer_archive_folder: ResourceHint | None = None
    meeting_notes_folder: ResourceHint | None = None
    todo_tasklist_guid: ResourceHint | None = None
    todo_customer_field_guid: ResourceHint | None = None
    todo_priority_field_guid: ResourceHint | None = None
    todo_priority_options: list[str] = field(default_factory=list)
    todo_priority_option_guids: dict[str, str] = field(default_factory=dict)
    source_files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TableProfile:
    table_name: str
    table_role: TableRole
    entity_key: str
    dedupe_key: list[str] = field(default_factory=list)
    default_read_slots: list[str] = field(default_factory=list)
    write_slots: list[str] = field(default_factory=list)
    protected_slots: list[str] = field(default_factory=list)
    strict_enum_slots: list[str] = field(default_factory=list)
    capability_required: bool = False


@dataclass
class ResourceResolution:
    status: Status
    hints_used: list[ResourceHint] = field(default_factory=list)
    missing_keys: list[str] = field(default_factory=list)
    unconfirmed_keys: list[str] = field(default_factory=list)


@dataclass
class ResourceProbeOutcome:
    key: str
    confirmed: bool
    status: CapabilityStatus
    reason: str | None = None
    hint: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomerMatch:
    customer_id: str
    short_name: str
    archive_link: str | None = None
    confidence: float = 1.0
    raw_record: dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomerResolution:
    status: Literal["resolved", "ambiguous", "missing"]
    candidates: list[CustomerMatch] = field(default_factory=list)
    query: str = ""


@dataclass
class ContextRecoveryResult:
    status: ContextStatus
    used_sources: list[str] = field(default_factory=list)
    fallback_reason: str | None = None
    key_context: list[str] = field(default_factory=list)
    missing_sources: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    write_ceiling: WriteCeiling = "normal"
    candidate_conflicts: list[str] = field(default_factory=list)
    evidence_container: EvidenceContainer | None = None

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


@dataclass
class WriteCandidate:
    object_name: str
    layer: Literal["snapshot", "detail", "archive", "reminder"]
    semantic_fields: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    operation: WriteOperation = "create"
    match_basis: dict[str, Any] = field(default_factory=dict)
    source_context: dict[str, Any] = field(default_factory=dict)
    target_object: str | None = None

    def routing_metadata(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "match_basis": dict(self.match_basis),
            "source_context": dict(self.source_context),
            "target_object": self.target_object,
        }


@dataclass
class FieldOptionResult:
    candidate_value: str | None
    resolved_option: str | None = None
    used_synonym: bool = False


@dataclass
class PreflightFieldResult:
    semantic_field: str
    resolved_field_id: str | None
    resolved_field_name: str | None
    resolved_field_type: str | None
    status: PreflightStatus
    drift_items: list[str] = field(default_factory=list)
    alias_fallbacks: list[str] = field(default_factory=list)
    blocked_reason: str | None = None
    option_result: FieldOptionResult | None = None
    write_policy: str | None = None
    reason: str | None = None


@dataclass
class PreflightReport:
    object_name: str
    status: PreflightStatus
    field_results: list[PreflightFieldResult] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)


@dataclass
class GuardResult:
    object_name: str
    allowed: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class WriteExecutionResult:
    target_object: str
    attempted: bool
    allowed: bool
    preflight_status: PreflightStatus | None = None
    guard_status: GuardStatus | None = None
    dedupe_decision: DedupeDecision = "create_new"
    executed_operation: ExecutedOperation = "no_write"
    remote_object_id: str | None = None
    remote_url: str | None = None
    remote_metadata: dict[str, Any] = field(default_factory=dict)
    blocked_reasons: list[str] = field(default_factory=list)
    drift_items: list[str] = field(default_factory=list)
    source_context: dict[str, Any] = field(default_factory=dict)
    preflight_report: PreflightReport | None = None
    guard_result: GuardResult | None = None
    request_payload: dict[str, Any] = field(default_factory=dict)

    def structured_result(self) -> dict[str, Any]:
        remote_metadata = dict(self.remote_metadata)
        if self.remote_object_id is not None:
            remote_metadata.setdefault("object_id", self.remote_object_id)
        if self.remote_url is not None:
            remote_metadata.setdefault("url", self.remote_url)
        return {
            "target_object": self.target_object,
            "attempted": self.attempted,
            "allowed": self.allowed,
            "preflight_status": self.preflight_status,
            "guard_status": self.guard_status,
            "dedupe_decision": self.dedupe_decision,
            "executed_operation": self.executed_operation,
            "blocked_reasons": list(self.blocked_reasons),
            "drift_items": list(self.drift_items),
            "source_context": dict(self.source_context),
            "remote_metadata": remote_metadata,
            "request_payload": dict(self.request_payload),
        }


@dataclass
class TodoWriteResult(WriteExecutionResult):
    @property
    def task_guid(self) -> str | None:
        return self.remote_object_id

    @property
    def task_url(self) -> str | None:
        return self.remote_url


@dataclass
class CapabilityCheck:
    name: str
    status: CapabilityStatus
    reasons: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilityReport:
    checks: list[CapabilityCheck] = field(default_factory=list)


@dataclass
class GatewayResult:
    resource_resolution: ResourceResolution
    capability_report: CapabilityReport | None = None
    customer_resolution: CustomerResolution | None = None
    write_candidates: list[WriteCandidate] = field(default_factory=list)
    preflight_reports: list[PreflightReport] = field(default_factory=list)
    guard_results: list[GuardResult] = field(default_factory=list)
    write_results: list[WriteExecutionResult] = field(default_factory=list)


# --- Expert Analysis Foundation (Phase 16) ---
# Re-exported from expert_analysis_helper for backward compatibility with code
# that imports EvidenceContainer et al. from runtime.models.

from .expert_analysis_helper import (
    CRITICAL_SOURCES,
    EvidenceAssemblyInput,
    EvidenceContainer,
    EvidenceQuality,
    EvidenceSource,
    EvidenceSourceName,
    WriteCeiling,
)

__all__ = [
    "CRITICAL_SOURCES",
    "EvidenceAssemblyInput",
    "EvidenceContainer",
    "EvidenceQuality",
    "EvidenceSource",
    "EvidenceSourceName",
    "WriteCeiling",
]
