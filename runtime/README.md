# Runtime

This directory contains the local runtime layer for `feishu-am-workbench`.

Current goal:

- make the Feishu workbench gateway executable inside the skill repository
- keep the runtime local and personal-workflow oriented
- avoid premature multi-user configuration design

## Modules

- `models.py`
  - shared data models
- `runtime_sources.py`
  - load current runtime hints from repository files
  - includes parsing current live URLs from `references/live-resource-links.md`
- `resource_resolver.py`
  - resolve currently known resource hints
- `lark_cli.py`
  - wrapper around local `lark-cli` JSON commands
- `live_adapter.py`
  - thin live adapters and resource probes over `lark-cli`
  - no default business query strategy or scene-level context assembly
- `semantic_registry.py`
  - current semantic slot mapping for local live-schema resolution
- `customer_resolver.py`
  - resolve one customer from customer master via injected backend
- `schema_preflight.py`
  - run schema checks via injected backend
- `write_guard.py`
  - apply final write safety rules
- `gateway.py`
  - orchestrate the full Feishu workbench gateway
  - includes `FeishuWorkbenchGateway.for_live_lark_cli(repo_root)` as the standard live entrypoint
- `diagnostics.py`
  - builds and renders a local live capability diagnostic report

## Current boundary

The runtime now includes a first live adapter layer over local `lark-cli`.

That means:

- the gateway flow is now code, not only prose
- resource probing can distinguish `resolved` from `present-but-not-live-confirmed`
- task resources can already be confirmed live in the current environment
- drive/docs/base access still depends on local scopes and any available `FEISHU_AM_BASE_TOKEN`

This is still intentionally local and personal-workflow oriented.

## Live capability report

The live gateway now exposes a capability report before any business-stage interpretation:

- `base_access`
  - whether `FEISHU_AM_BASE_TOKEN` is present and readable
- `docs_access`
  - whether customer archive / meeting-note folders can be confirmed live
- `task_access`
  - whether the configured tasklist is reachable live

This keeps runtime failures explicit instead of surfacing later as ambiguous scene-level errors.

Current design rule:

- the runtime should expose only基础资源解析、客户解析和写前安全能力
- upper-layer scenes decide what to read and how to assemble it
- the default gateway should not assemble business context on behalf of scenes

## Diagnostic entrypoint

Run one command to inspect the current local environment:

```bash
python3 -m runtime /Users/liaoky/.codex/skills/feishu-am-workbench
```

Use JSON output when another tool or scene needs to consume the report:

```bash
python3 -m runtime /Users/liaoky/.codex/skills/feishu-am-workbench --json
```
