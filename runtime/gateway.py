"""Orchestrate resource discovery, customer resolution, and write safety."""

from __future__ import annotations

from .customer_resolver import CustomerResolver
from .live_adapter import (
    LarkCliCustomerBackend,
    LarkCliResourceProbe,
    LarkCliSchemaBackend,
    LiveCapabilityReporter,
    LiveWorkbenchConfig,
)
from .lark_cli import LarkCliClient
from .models import GatewayResult, WriteCandidate
from .resource_resolver import ResourceResolver
from .runtime_sources import RuntimeSourceLoader
from .schema_preflight import SchemaPreflightRunner
from .write_guard import WriteGuard


class FeishuWorkbenchGateway:
    def __init__(
        self,
        repo_root: str,
        customer_resolver: CustomerResolver,
        schema_preflight: SchemaPreflightRunner,
        write_guard: WriteGuard,
        resource_resolver: ResourceResolver | None = None,
        capability_reporter: LiveCapabilityReporter | None = None,
        live_config: LiveWorkbenchConfig | None = None,
    ) -> None:
        self.source_loader = RuntimeSourceLoader(repo_root)
        self.resource_resolver = resource_resolver or ResourceResolver()
        self.customer_resolver = customer_resolver
        self.schema_preflight = schema_preflight
        self.write_guard = write_guard
        self.capability_reporter = capability_reporter
        self.live_config = live_config

    @classmethod
    def for_live_lark_cli(cls, repo_root: str) -> "FeishuWorkbenchGateway":
        source_loader = RuntimeSourceLoader(repo_root)
        sources = source_loader.load()
        config = LiveWorkbenchConfig.from_sources(sources)
        client = LarkCliClient()
        probe = LarkCliResourceProbe(client, config)
        return cls(
            repo_root=repo_root,
            customer_resolver=CustomerResolver(LarkCliCustomerBackend(client, config)),
            schema_preflight=SchemaPreflightRunner(LarkCliSchemaBackend(client, config)),
            write_guard=WriteGuard(),
            resource_resolver=ResourceResolver(probe=probe),
            capability_reporter=LiveCapabilityReporter(client, config, probe),
            live_config=config,
        )

    def run(
        self,
        customer_query: str,
        write_candidates: list[WriteCandidate] | None = None,
        owner_required_objects: set[str] | None = None,
    ) -> GatewayResult:
        runtime_sources = self.source_loader.load()
        resource_resolution = self.resource_resolver.resolve(runtime_sources)
        capability_report = None
        if self.capability_reporter:
            capability_report = self.capability_reporter.build(runtime_sources)
        result = GatewayResult(
            resource_resolution=resource_resolution,
            capability_report=capability_report,
        )

        customer_resolution = self.customer_resolver.resolve(customer_query)
        result.customer_resolution = customer_resolution
        if customer_resolution.status != "resolved":
            return result

        write_candidates = write_candidates or []
        result.write_candidates = write_candidates
        owner_required_objects = owner_required_objects or set()

        for candidate in write_candidates:
            report = self.schema_preflight.run(candidate)
            result.preflight_reports.append(report)
            guard = self.write_guard.evaluate(
                candidate,
                report,
                owner_required=candidate.object_name in owner_required_objects,
            )
            result.guard_results.append(guard)

        return result
