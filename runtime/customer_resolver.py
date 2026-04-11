"""Resolve one customer from the current customer master source of truth."""

from __future__ import annotations

from typing import Protocol

from .models import CustomerMatch, CustomerResolution


class CustomerBackend(Protocol):
    def search_customer_master(self, query: str) -> list[dict[str, str]]:
        """Return candidate customer rows from customer master."""


class CustomerResolver:
    def __init__(self, backend: CustomerBackend) -> None:
        self.backend = backend

    def resolve(self, query: str) -> CustomerResolution:
        rows = self.backend.search_customer_master(query)
        if not rows:
            return CustomerResolution(status="missing", query=query)

        candidates = [self._row_to_match(row, query) for row in rows]
        exact = [c for c in candidates if c.short_name == query or c.customer_id == query]

        if len(exact) == 1:
            return CustomerResolution(status="resolved", candidates=exact, query=query)
        if len(candidates) == 1:
            return CustomerResolution(status="resolved", candidates=candidates, query=query)
        return CustomerResolution(status="ambiguous", candidates=candidates, query=query)

    def _row_to_match(self, row: dict[str, str], query: str) -> CustomerMatch:
        short_name = row.get("简称") or row.get("客户名称") or query
        customer_id = row.get("客户ID") or row.get("客户 ID") or ""
        archive_link = row.get("客户档案")
        confidence = 1.0 if short_name == query else 0.7
        return CustomerMatch(
            customer_id=customer_id,
            short_name=short_name,
            archive_link=archive_link,
            confidence=confidence,
            raw_record=dict(row),
        )
