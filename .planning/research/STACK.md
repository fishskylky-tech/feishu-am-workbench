# Research: Stack

## Recommendation

v1.1 should keep the current stack: Python runtime, lark-cli adapters, markdown-first skill docs, and unittest/eval assets. The milestone needs an executable scene runtime layer, not a new framework.

## Keep

- Python 3.10+ runtime as the deterministic execution surface
- lark-cli as the live Feishu adapter
- markdown-first skill and references as policy/routing context
- unittest plus existing eval assets for regression proof

## Do Not Add

- No plugin framework
- No workflow engine
- No web service or database layer
- No host-specific SDK abstractions in core runtime
- No generic scene DSL

## Integration Points

- Reuse runtime/gateway.py for resource resolution, customer resolution, preflight, and guard boundaries
- Reuse runtime/live_adapter.py for thin targeted reads
- Extend runtime/__main__.py as the operator surface for scene execution
- Reuse runtime/models.py contracts rather than inventing parallel result models

## Implementation Guidance

1. Keep the runtime thin and let scenes own business reasoning.
2. Add scene orchestration modules before adding any dependency.
3. Keep outputs host-agnostic so portability remains testable.
4. Treat cache or schema snapshots as hints, never as live truth.
5. Add contract tests whenever a scene gains a new executable surface.
