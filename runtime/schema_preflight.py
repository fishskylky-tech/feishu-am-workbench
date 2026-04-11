"""Live schema preflight runner over injected schema snapshots/adapters."""

from __future__ import annotations

from typing import Protocol

from .models import (
    FieldOptionResult,
    PreflightFieldResult,
    PreflightReport,
    WriteCandidate,
)


class SchemaBackend(Protocol):
    def get_table_schema(self, object_name: str) -> dict[str, dict[str, object]] | None:
        """Return mapping: field name -> metadata including type/options/aliases."""


class SchemaPreflightRunner:
    def __init__(self, backend: SchemaBackend) -> None:
        self.backend = backend

    def run(self, candidate: WriteCandidate) -> PreflightReport:
        schema = self.backend.get_table_schema(candidate.object_name)
        if not schema:
            return PreflightReport(
                object_name=candidate.object_name,
                status="blocked",
                blocked_reasons=["table_missing"],
            )

        results: list[PreflightFieldResult] = []
        for semantic_field in candidate.semantic_fields:
            payload = candidate.payload.get(semantic_field)
            result = self._resolve_field(schema, semantic_field, payload, candidate)
            results.append(result)

        status = "safe"
        blocked_reasons: list[str] = []
        if any(item.status == "blocked" for item in results):
            status = "blocked"
            blocked_reasons = list(
                dict.fromkeys(
                    item.blocked_reason or "blocked"
                    for item in results
                    if item.status == "blocked"
                )
            )
        elif any(item.status == "safe_with_drift" for item in results):
            status = "safe_with_drift"

        return PreflightReport(
            object_name=candidate.object_name,
            status=status,
            field_results=results,
            blocked_reasons=blocked_reasons,
        )

    def _resolve_field(
        self,
        schema: dict[str, dict[str, object]],
        semantic_field: str,
        payload: object,
        candidate: WriteCandidate | None = None,
    ) -> PreflightFieldResult:
        field_meta = schema.get(semantic_field)
        alias_fallbacks: list[str] = []
        drift_items: list[str] = []

        if not field_meta:
            for field_name, meta in schema.items():
                aliases = meta.get("aliases", [])
                if semantic_field in aliases:
                    field_meta = meta
                    alias_fallbacks.append(f"{semantic_field}->{field_name}")
                    drift_items.append("field_renamed_alias_resolved")
                    break

        if not field_meta:
            missing_reason = (
                "todo_custom_field_missing"
                if candidate and candidate.layer == "reminder"
                else "field_missing"
            )
            return PreflightFieldResult(
                semantic_field=semantic_field,
                resolved_field_id=None,
                resolved_field_name=None,
                resolved_field_type=None,
                status="blocked",
                drift_items=[missing_reason],
                blocked_reason=missing_reason,
                reason="Live schema does not contain the target field.",
            )

        field_name = str(field_meta.get("name", semantic_field))
        field_id = self._optional_str(field_meta.get("field_id"))
        field_type = str(field_meta.get("type", "unknown"))
        write_policy = self._optional_str(field_meta.get("write_policy"))
        allowed_live_types = [str(item) for item in field_meta.get("allowed_live_types", [])]
        option_result = None
        status = "safe_with_drift" if alias_fallbacks else "safe"

        if allowed_live_types and field_type not in allowed_live_types:
            return PreflightFieldResult(
                semantic_field=semantic_field,
                resolved_field_id=field_id,
                resolved_field_name=field_name,
                resolved_field_type=field_type,
                status="blocked",
                drift_items=drift_items + ["field_type_changed_blocked"],
                alias_fallbacks=alias_fallbacks,
                blocked_reason="field_type_changed_blocked",
                write_policy=write_policy,
                reason="Live field type is incompatible with the semantic slot.",
            )

        if write_policy in {"guarded_update", "read_only_for_match"} and payload is not None:
            return PreflightFieldResult(
                semantic_field=semantic_field,
                resolved_field_id=field_id,
                resolved_field_name=field_name,
                resolved_field_type=field_type,
                status="blocked",
                drift_items=drift_items + ["protected_field_policy_changed"],
                alias_fallbacks=alias_fallbacks,
                blocked_reason="protected_field_policy_changed",
                write_policy=write_policy,
                reason="Field is guarded and cannot be updated in this write path.",
            )

        if (
            candidate
            and candidate.layer == "reminder"
            and semantic_field == "owner"
            and self._is_missing_payload(payload)
        ):
            return PreflightFieldResult(
                semantic_field=semantic_field,
                resolved_field_id=field_id,
                resolved_field_name=field_name,
                resolved_field_type=field_type,
                status="blocked",
                drift_items=drift_items + ["owner_unresolved"],
                alias_fallbacks=alias_fallbacks,
                blocked_reason="owner_unresolved",
                write_policy=write_policy,
                reason="Todo owner is missing or unresolved.",
            )

        if candidate and candidate.layer == "reminder" and semantic_field == "owner":
            owner_reason = self._owner_invalid_reason(field_meta, payload)
            if owner_reason:
                return PreflightFieldResult(
                    semantic_field=semantic_field,
                    resolved_field_id=field_id,
                    resolved_field_name=field_name,
                    resolved_field_type=field_type,
                    status="blocked",
                    drift_items=drift_items + [owner_reason],
                    alias_fallbacks=alias_fallbacks,
                    blocked_reason=owner_reason,
                    write_policy=write_policy,
                    reason="Todo owner is not valid for the live tasklist members.",
                )

        if write_policy in {"required_create", "required_lookup"} and self._is_missing_payload(payload):
            return PreflightFieldResult(
                semantic_field=semantic_field,
                resolved_field_id=field_id,
                resolved_field_name=field_name,
                resolved_field_type=field_type,
                status="blocked",
                drift_items=drift_items + ["required_field_missing"],
                alias_fallbacks=alias_fallbacks,
                blocked_reason="required_field_missing",
                write_policy=write_policy,
                reason="Required payload is missing for this semantic slot.",
            )

        payload_reason = self._payload_incompatible_reason(field_type, payload)
        if payload_reason:
            return PreflightFieldResult(
                semantic_field=semantic_field,
                resolved_field_id=field_id,
                resolved_field_name=field_name,
                resolved_field_type=field_type,
                status="blocked",
                drift_items=drift_items + [payload_reason],
                alias_fallbacks=alias_fallbacks,
                blocked_reason=payload_reason,
                write_policy=write_policy,
                reason="Payload shape is incompatible with the live field type.",
            )

        if field_type in {"single_select", "multi_select"}:
            option_result = self._resolve_option(field_meta, payload)
            if option_result.resolved_option is None and payload is not None:
                return PreflightFieldResult(
                    semantic_field=semantic_field,
                    resolved_field_id=field_id,
                    resolved_field_name=field_name,
                    resolved_field_type=field_type,
                    status="blocked",
                    drift_items=drift_items + ["option_missing_blocked"],
                    alias_fallbacks=alias_fallbacks,
                    blocked_reason="option_missing_blocked",
                    option_result=option_result,
                    write_policy=write_policy,
                    reason="Candidate option does not exist in the live field options.",
                )
            if option_result.used_synonym:
                drift_items.append("option_synonym_resolved")
                status = "safe_with_drift"

        return PreflightFieldResult(
            semantic_field=semantic_field,
            resolved_field_id=field_id,
            resolved_field_name=field_name,
            resolved_field_type=field_type,
            status=status,
            drift_items=drift_items,
            alias_fallbacks=alias_fallbacks,
            option_result=option_result,
            write_policy=write_policy,
            reason=(
                "Alias fallback or option normalization was applied."
                if drift_items
                else "Resolved against live schema without drift."
            ),
        )

    def _resolve_option(
        self, field_meta: dict[str, object], payload: object
    ) -> FieldOptionResult:
        if payload is None:
            return FieldOptionResult(candidate_value=None)
        options = [str(item) for item in field_meta.get("options", [])]
        synonyms = field_meta.get("synonyms", {})
        candidate = str(payload)
        if candidate in options:
            return FieldOptionResult(candidate_value=candidate, resolved_option=candidate)
        mapped = synonyms.get(candidate)
        if mapped in options:
            return FieldOptionResult(
                candidate_value=candidate,
                resolved_option=str(mapped),
                used_synonym=True,
            )
        return FieldOptionResult(candidate_value=candidate)

    def _payload_incompatible_reason(
        self, field_type: str, payload: object
    ) -> str | None:
        if payload is None:
            return None
        if field_type in {"text", "url"}:
            return None if isinstance(payload, str) else "field_type_changed_blocked"
        if field_type == "datetime":
            return None if isinstance(payload, (str, int, float)) else "field_type_changed_blocked"
        if field_type == "number":
            return None if isinstance(payload, (int, float)) else "field_type_changed_blocked"
        if field_type == "single_select":
            return None if not isinstance(payload, (list, tuple, set, dict)) else "field_type_changed_blocked"
        if field_type == "multi_select":
            return None if isinstance(payload, (list, tuple, set)) else "field_type_changed_blocked"
        if field_type == "user":
            return None if isinstance(payload, (str, list, tuple, set, dict)) else "field_type_changed_blocked"
        return None

    def _optional_str(self, value: object) -> str | None:
        if value is None:
            return None
        return str(value)

    def _is_missing_payload(self, payload: object) -> bool:
        if payload is None:
            return True
        if isinstance(payload, str):
            return payload.strip() == ""
        if isinstance(payload, (list, tuple, set, dict)):
            return len(payload) == 0
        return False

    def _owner_invalid_reason(
        self, field_meta: dict[str, object], payload: object
    ) -> str | None:
        valid_member_ids = [str(item) for item in field_meta.get("valid_member_ids", [])]
        if not valid_member_ids:
            return "owner_unresolved"
        payload_ids = self._extract_member_ids(payload)
        if not payload_ids:
            return "owner_unresolved"
        return None if all(member_id in valid_member_ids for member_id in payload_ids) else "owner_unresolved"

    def _extract_member_ids(self, payload: object) -> list[str]:
        if isinstance(payload, str):
            value = payload.strip()
            return [value] if value else []
        if isinstance(payload, dict):
            member_id = payload.get("id")
            return [str(member_id)] if member_id else []
        if isinstance(payload, (list, tuple, set)):
            ids: list[str] = []
            for item in payload:
                ids.extend(self._extract_member_ids(item))
            return ids
        return []
