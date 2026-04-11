"""Final safety checks before a write becomes write-ready."""

from __future__ import annotations

from .models import GuardResult, PreflightReport, WriteCandidate


class WriteGuard:
    def __init__(self, protected_fields: dict[str, set[str]] | None = None) -> None:
        self.protected_fields = protected_fields or {}

    def evaluate(
        self,
        candidate: WriteCandidate,
        preflight: PreflightReport,
        owner_required: bool = False,
    ) -> GuardResult:
        reasons: list[str] = []
        protected = self.protected_fields.get(candidate.object_name, set())

        if preflight.status == "blocked":
            reasons.extend(preflight.blocked_reasons)

        touched_protected = protected.intersection(candidate.payload.keys())
        if touched_protected:
            reasons.append(f"protected_fields:{','.join(sorted(touched_protected))}")

        if owner_required and not candidate.payload.get("owner"):
            reasons.append("owner_unresolved")

        return GuardResult(
            object_name=candidate.object_name,
            allowed=not reasons,
            reasons=reasons,
        )
